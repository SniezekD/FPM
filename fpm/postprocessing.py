from __future__ import annotations

import re
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
    """Aggregates case metrics for a single geometry directory.

    A geometry directory (``geometry_<NNN>``) produced by the runner holds a
    ``porous_medium_spec.csv`` describing the medium and one sub-directory per
    simulated case (one per inlet velocity). This class discovers those cases,
    runs a :class:`CasePostProcessor` for each of them and gathers their metrics
    into a single DataFrame tagged with the geometry's id, which is parsed from
    the directory name.
    """

    def __init__(self, geometry_dir: pathlib.Path) -> None:
        self._geometry_dir = geometry_dir
        self.geometry_id = self._parse_geometry_id(geometry_dir)
        self.case_post_procs: List[CasePostProcessor] = self._discover_cases()
        self.results_df: pd.DataFrame | None = None

    @staticmethod
    def _parse_geometry_id(geometry_dir: pathlib.Path) -> int:
        """Extract the geometry number from a ``geometry_<NNN>`` directory name."""
        match = re.search(r"(\d+)$", geometry_dir.name)
        if match is None:
            raise ValueError(
                "Cannot parse geometry id from directory name "
                f"'{geometry_dir.name}'; expected a trailing integer."
            )
        return int(match.group(1))

    def _discover_cases(self) -> List[CasePostProcessor]:
        """Find every case sub-directory in the geometry directory.

        A case is any sub-directory that contains an ``OF_spec.csv`` file, which
        keeps discovery independent of the runner's ``velocity_*`` naming.
        """
        case_dirs = sorted(
            d for d in self._geometry_dir.iterdir()
            if d.is_dir() and (d / "OF_spec.csv").exists()
        )
        if not case_dirs:
            logger.warning(
                "No cases found in geometry directory %s", self._geometry_dir
            )
        return [CasePostProcessor(case_dir) for case_dir in case_dirs]

    def compute_metrics(self) -> pd.DataFrame:
        """Compute the metrics of every case and gather them in one DataFrame.

        The resulting frame has one row per case, one column per key in
        :attr:`CasePostProcessor.metrics`, plus a ``geometry_id`` column. It is
        also stored on :attr:`results_df`.
        """
        rows = [
            {"geometry_id": self.geometry_id, **case.metrics}
            for case in self.case_post_procs
        ]
        self.results_df = pd.DataFrame(rows)
        return self.results_df

    def to_csv(self) -> pathlib.Path:
        """Save the aggregated metrics to a CSV inside the geometry directory.

        The file is named ``geom_<NNN>_flow_params.csv``, where ``<NNN>`` is the
        zero-padded geometry id. Metrics are computed on demand if they have not
        been already. Returns the path of the written file.
        """
        if self.results_df is None:
            logger.warning(
                "Metrics have not been computed yet; computing them now, "
                "this might take a while."
            )
            self.compute_metrics()

        save_path = self._geometry_dir / f"geom_{self.geometry_id:03d}_flow_params.csv"
        self.results_df.to_csv(save_path, index=False)
        logger.debug("Saved geometry flow params to %s", save_path)
        return save_path


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
        self.streamwise = self._of_spec['streamwise_axis'].values[0]

        # Populated lazily on first access to `metrics` to avoid reading the
        # (potentially large) VTK field for every case at construction time.
        self._df: pd.DataFrame | None = None
        self._metrics: dict | None = None

    def _get_pm_bbox(self) -> tuple:
        """Read bounding box coordinates from porous medium spec CSV file
           and return them as a tuple.
        """
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
                "streamwise_axis": self.streamwise,
            }
        return self._metrics

    def to_csv(self) -> pathlib.Path:
        """Save this case's metrics to ``case_flow_params.csv`` in the case dir.

        Metrics are computed on demand if they have not been already. Returns
        the path of the written file.
        """
        save_path = self._case_dir_path / "case_flow_params.csv"
        pd.DataFrame([self.metrics]).to_csv(save_path, index=False)
        logger.debug("Saved case flow params to %s", save_path)
        return save_path
