import pathlib
import argparse
import logging

import fpm.utilities.utils as utils
from fpm.postprocessing import ExperimentPostProcessor


logger = logging.getLogger("fpm.postprocess")


def parse_cla():
    parser = argparse.ArgumentParser(
        description=(
            "Post-process an FPM experiment: aggregate the per-case flow "
            "metrics into CSVs and plot experiment-level figures. Reads the "
            "results tree produced by scripts/automatic_runner.py and can be "
            "run at any time, including while a run is still in progress."
        )
    )

    parser.add_argument(
        "-r",
        "--results-dir",
        dest="results_dir",
        required=True,
        help="Path to the experiment results directory to post-process.",
    )

    parser.add_argument(
        "--figures-dir",
        dest="figures_dir",
        default=None,
        help=(
            "Directory to write figures to. Defaults to "
            "<results-dir>/figures."
        ),
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Recompute every case's metrics from the VTK fields, ignoring any "
            "cached case_flow_params.csv files."
        ),
    )

    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Only write the metrics CSVs; skip plotting.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print debug info to console.",
    )

    return parser.parse_args()


def main():
    args = parse_cla()
    results_dir = pathlib.Path(args.results_dir)

    utils.setup_logging(
        verbose=args.verbose,
        log_file=results_dir / "postprocess.log",
    )

    logger.info("Post-processing experiment in %s", results_dir)

    experiment = ExperimentPostProcessor(results_dir, overwrite=args.overwrite)
    experiment.compute_metrics()

    csv_path = experiment.to_csv()
    logger.info("Experiment metrics written to %s", csv_path)

    if not args.no_plots:
        figures_dir = (
            pathlib.Path(args.figures_dir) if args.figures_dir else None
        )
        experiment.plot_results(figures_dir=figures_dir)


if __name__ == "__main__":
    main()
