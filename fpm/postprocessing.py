from __future__ import annotations

import re
import pathlib
import tempfile
import tarfile
import logging
from typing import List

import pandas as pd
import matplotlib.pyplot as plt

from fpm.io.vtk_reader import read_vtk
from fpm.utilities.participation_number import compute_participation_number
from fpm.utilities.rho_minus import compute_rho_minus
from fpm.utilities.tortuosity import (
    compute_tortuosity,
)
from fpm.utilities.utils import calculate_inlet_flow_rate

logger = logging.getLogger(__name__)


class ExperimentPostProcessor():
    """Aggregates and plots the metrics of a whole experiment.

    An experiment's results directory holds several geometry directories (see
    :class:`GeometryPostProcessor`), grouped by porosity. This class discovers
    every geometry, computes its cases' metrics in a cascade, merges them into a
    single DataFrame and produces experiment-level figures.
    """

    #: Metrics plotted against inlet flow rate, mapped to their axis labels.
    _METRIC_LABELS = {
        "participation_number": "Participation Number",
        "tortuosity": "Tortuosity",
        "rho_minus": r"$\rho^-$",
    }
    _FLOW_RATE_LABEL = r"Inlet Flow Rate [m$^3$/s]"

    def __init__(self, results_dir: pathlib.Path) -> None:
        self.results_dir: pathlib.Path = results_dir
        self.geometry_post_procs: List[GeometryPostProcessor] = (
            self.read_geometries()
        )
        self.results_df: pd.DataFrame | None = None

    def read_geometries(self) -> List[GeometryPostProcessor]:
        """Discover every geometry directory under the results directory.

        A geometry directory is identified by the presence of a
        ``porous_medium_spec.csv`` file, which keeps discovery independent of the
        ``cases/porosity_*/geometry_*`` layout.
        """
        geometry_dirs = sorted({
            spec.parent
            for spec in self.results_dir.rglob("porous_medium_spec.csv")
        })
        if not geometry_dirs:
            logger.warning(
                "No geometries found under %s", self.results_dir
            )
        return [GeometryPostProcessor(d) for d in geometry_dirs]

    def compute_metrics(self) -> pd.DataFrame:
        """Compute metrics for every case in every geometry, in a cascade.

        Each :class:`GeometryPostProcessor` computes its own cases' metrics; the
        per-geometry frames are then concatenated into a single experiment-level
        DataFrame stored on :attr:`results_df` and returned.
        """
        frames = [
            geom.compute_metrics() for geom in self.geometry_post_procs
        ]
        self.results_df = (
            pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        )
        return self.results_df

    def _ensure_metrics(self) -> None:
        """Compute metrics if they have not been computed yet."""
        if self.results_df is None:
            logger.warning(
                "Metrics have not been computed yet; computing them now, "
                "this might take a while."
            )
            self.compute_metrics()

    def to_csv(self, save_path: pathlib.Path | None = None) -> pathlib.Path:
        """Save the merged experiment metrics to a CSV file.

        Defaults to ``experiment_flow_params.csv`` in the results directory.
        Metrics are computed on demand if needed. Returns the written path.
        """
        self._ensure_metrics()
        if save_path is None:
            save_path = self.results_dir / "experiment_flow_params.csv"
        self.results_df.to_csv(save_path, index=False)
        logger.debug("Saved experiment flow params to %s", save_path)
        return save_path

    def plot_results(
        self,
        figures_dir: pathlib.Path | None = None,
        show: bool = False,
    ) -> pathlib.Path | None:
        """Plot experiment-level figures for every metric.

        For each metric three kinds of figure are produced: one averaging over
        the geometries of every porosity in a single plot (with standard-
        deviation error bars), one such averaged plot per porosity on its own,
        and one showing each geometry separately per porosity. Figures are saved
        under ``results_dir/figures`` (overridable via ``figures_dir``). Returns
        the figures directory, or ``None`` if there is nothing to plot.
        """
        self._ensure_metrics()
        if self.results_df.empty:
            logger.warning("No results to plot.")
            return None

        if figures_dir is None:
            figures_dir = self.results_dir / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        for metric, ylabel in self._METRIC_LABELS.items():
            self._plot_averaged_by_porosity(metric, ylabel, figures_dir, show)
            self._plot_averaged_per_porosity(metric, ylabel, figures_dir, show)
            self._plot_geometries_by_porosity(metric, ylabel, figures_dir, show)

        logger.info("Saved experiment figures to %s", figures_dir)
        return figures_dir

    @staticmethod
    def _averaged(sub: pd.DataFrame, metric: str) -> pd.DataFrame:
        """Mean and std of ``metric`` over geometries at each inlet flow rate."""
        return (
            sub.groupby("inlet_flow_rate")[metric]
            .agg(["mean", "std"])
            .reset_index()
            .sort_values("inlet_flow_rate")
        )

    def _draw_averaged_curve(self, ax, grouped: pd.DataFrame, color, label) -> None:
        """Draw one averaged curve: eye-guide line plus markers with std bars."""
        # Thin translucent line: an eye-guide only, not a fit.
        ax.plot(
            grouped["inlet_flow_rate"], grouped["mean"],
            linestyle="-", linewidth=0.8, alpha=0.5, color=color,
        )
        ax.errorbar(
            grouped["inlet_flow_rate"], grouped["mean"],
            yerr=grouped["std"].fillna(0.0),
            fmt="o", markersize=4, capsize=3, color=color, label=label,
        )

    def _finalize_axes(self, ax, ylabel: str, title: str) -> None:
        """Apply the shared axis labels, title, dashed grid and legend."""
        ax.set_xlabel(self._FLOW_RATE_LABEL)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(linestyle="--", color="gray")
        ax.legend()

    def _plot_averaged_by_porosity(
        self,
        metric: str,
        ylabel: str,
        figures_dir: pathlib.Path,
        show: bool,
    ) -> None:
        """One figure: metric vs inlet flow rate, averaged over geometries.

        Each porosity is a single curve of the mean over all geometries, with
        vertical error bars representing the standard deviation.
        """
        cmap = plt.get_cmap("tab10")
        fig, ax = plt.subplots()
        for i, porosity in enumerate(sorted(self.results_df["porosity"].unique())):
            sub = self.results_df[self.results_df["porosity"] == porosity]
            n_geometries = sub["geometry_id"].nunique()
            self._draw_averaged_curve(
                ax, self._averaged(sub, metric),
                color=cmap(i % cmap.N),
                label=f"porosity = {porosity:g} (N = {n_geometries})",
            )
        self._finalize_axes(ax, ylabel, f"{ylabel} averaged over geometries")
        fig.tight_layout()
        fig.savefig(figures_dir / f"{metric}_avg_by_porosity.png")
        if show:
            plt.show()
        plt.close(fig)

    def _plot_averaged_per_porosity(
        self,
        metric: str,
        ylabel: str,
        figures_dir: pathlib.Path,
        show: bool,
    ) -> None:
        """One figure per porosity: metric vs inlet flow rate, averaged.

        Same averaged-over-geometries curve as :meth:`_plot_averaged_by_porosity`
        but with each porosity saved to its own file.
        """
        cmap = plt.get_cmap("tab10")
        for i, porosity in enumerate(sorted(self.results_df["porosity"].unique())):
            sub = self.results_df[self.results_df["porosity"] == porosity]
            n_geometries = sub["geometry_id"].nunique()
            fig, ax = plt.subplots()
            self._draw_averaged_curve(
                ax, self._averaged(sub, metric),
                color=cmap(i % cmap.N), label=f"porosity = {porosity:g}",
            )
            self._finalize_axes(
                ax, ylabel,
                f"{ylabel} averaged over {n_geometries} geometries "
                f"(porosity = {porosity:g})",
            )
            fig.tight_layout()
            fig.savefig(figures_dir / f"{metric}_avg_porosity_{porosity:.5f}.png")
            if show:
                plt.show()
            plt.close(fig)

    def _plot_geometries_by_porosity(
        self,
        metric: str,
        ylabel: str,
        figures_dir: pathlib.Path,
        show: bool,
    ) -> None:
        """One figure per porosity: metric vs inlet flow rate per geometry.

        Within a porosity, each geometry is drawn separately in its own color.
        """
        cmap = plt.get_cmap("tab10")
        for porosity in sorted(self.results_df["porosity"].unique()):
            sub = self.results_df[self.results_df["porosity"] == porosity]
            fig, ax = plt.subplots()
            for i, geom_id in enumerate(sorted(sub["geometry_id"].unique())):
                geom_df = (
                    sub[sub["geometry_id"] == geom_id]
                    .sort_values("inlet_flow_rate")
                )
                color = cmap(i % cmap.N)
                # Thin translucent line: an eye-guide only, not a fit.
                ax.plot(
                    geom_df["inlet_flow_rate"], geom_df[metric],
                    linestyle="-", linewidth=0.8, alpha=0.5, color=color,
                )
                ax.plot(
                    geom_df["inlet_flow_rate"], geom_df[metric],
                    linestyle="none", marker="o", markersize=4, color=color,
                    label=f"geometry {geom_id}",
                )
            self._finalize_axes(
                ax, ylabel, f"{ylabel} per geometry (porosity = {porosity:g})"
            )
            fig.tight_layout()
            fig.savefig(
                figures_dir / f"{metric}_porosity_{porosity:.5f}_by_geometry.png"
            )
            if show:
                plt.show()
            plt.close(fig)


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
