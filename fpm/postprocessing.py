from __future__ import annotations

import pathlib
import tempfile
import tarfile
import logging
from typing import List, Tuple

import pandas as pd
import numpy as np

from fpm.io.vtk_reader import read_vtk
from fpm.utilities.participation_number import compute_participation_number
from fpm.utilities.rho_minus import compute_rho_minus
from fpm.utilities.tortuosity import (
    compute_tortuosity,
)
from fpm.utilities.utils import calculate_inlet_flow_rate

logger = logging.getLogger(__name__)

class ExperimentPostProcessor():
    def __init__(self, results_dir: pathlib.Path) -> None:
        self.results_df = pd.DataFrame(
            columns=[
                'geometry_id',
                'porosity',
                'inlet_flow_rate',
                'participation_number',
                'rho_minus',
                'tortuosity'
            ]
        )
        self.results_dir: pathlib.Path = results_dir
        self.geometry_post_procs: List[GeometryPostProcessor] = self.read_geometries()

    def read_geometries(self) -> List[GeometryPostProcessor]:
        """Read each geometry archive in the experiment"""
        pass

    def merge_results(self) -> None:
        """Merges results from each geometry into one dataframe."""
        pass

    def to_csv(self, save_path: pathlib.Path) -> None:
        """Saves results into a CSV in given path."""
        pass

    def plot_results(
        self,
        save_path: pathlib.Path | None = None,
        show: bool = False
    ):
        """Plots all the results and either shows them or saves to a file"""
        pass


class GeometryPostProcessor():
    def __init__(self, archive_path:pathlib.Path) -> None:
        self.results_df = pd.DataFrame(
            columns=[
                'porosity',
                'inlet_flow_rate',
                'participation_number',
                'rho_minus',
                'tortuosity'
            ]
        )
        self._archive_path: pathlib.Path = archive_path

        self._porous_medium_spec = self.read_spec_from_archive()
        self._porous_medium_b_box = self.read_prous_medium_b_box()


    def read_cases(self) -> List[CasePostProcessor]:
        """Find all cases inside the archive"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            with tarfile.open(self._archive_path, "r:gz") as tar:
                tar.extractall(tmp)
            
            case_archives = [f for f in tmp.glob("U_*.tar.gz")]

        return list(
            CasePostProcessor(f, interest_b_box=self._porous_medium_b_box)
                for f in case_archives
        )


class CasePostProcessor():
    def __init__(self, case_dir_path: pathlib.Path, interest_b_box=None):
        self._case_dir_path = case_dir_path
        self._pm_spec = pd.read_csv(
            self._case_dir_path.parent / "porous_medium_spec.csv"
        )
        self._interest_b_box = (
            self._get_pm_bbox() if interest_b_box is None else interest_b_box
        )
        self._of_spec = pd.read_csv(self._case_dir_path / "OF_spec.csv")
        self.streamwise = self._of_spec['streamwise_direction'].values[0]

        # Populated lazily on first access to `metrics` to avoid reading the
        # (potentially large) VTK field for every case at construction time.
        self._df: pd.DataFrame | None = None
        self._metrics: dict | None = None

    def _get_pm_bbox(self) -> tuple:
        return (
            self._pm_spec['x_min'].values[0],
            self._pm_spec['x_max'].values[0],
            self._pm_spec['y_min'].values[0],
            self._pm_spec['y_max'].values[0],
            self._pm_spec['z_min'].values[0],
            self._pm_spec['z_max'].values[0],
        )

    def read_case_fields(self) -> pd.DataFrame:
        """Extract the case's VTK field archive and read it into a DataFrame.

        The frame is cropped to the porous medium bounding box and cached on
        the instance so repeated metric computations reuse it.
        """
        fields_archive = list(self._case_dir_path.glob("fields_*.vtk.gz"))
        if len(fields_archive) == 0:
            raise FileNotFoundError(
                f"No fields archive found in case directory: {self._case_dir_path}"
            )
        if len(fields_archive) > 1:
            logger.warning("More than one fields archive detected."
                           " Using the first one: %s", fields_archive[0])
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            with tarfile.open(fields_archive[0], "r:gz") as tar:
                tar.extractall(tmp)
            fields = list(tmp.glob("fields_*.vtk"))
            self._df = read_vtk(fields[0], interest_b_box=self._interest_b_box)

        return self._df

    @property
    def metrics(self) -> dict:
        """Parameters of interest for this case, computed once and cached."""
        if self._metrics is None:
            if self._df is None:
                self.read_case_fields()
            self._metrics = {
                "porosity": self._pm_spec['porosity'].values[0],
                "tortuosity": compute_tortuosity(self._df, self.streamwise),
                "participation_number": compute_participation_number(self._df),
                "rho_minus": compute_rho_minus(self._df, self.streamwise),
                "inlet_flow_rate": calculate_inlet_flow_rate(self._of_spec),
                "streamwise_direction": self.streamwise,
            }
        return self._metrics
