import pathlib
import tarfile
import argparse
import shutil
import itertools
import logging
import time

import pandas as pd

import fpm.utilities.utils as utils
from fpm.openfoam_case import OpenFoamCase
from fpm.media_models.swiss_cheese import SwissCheese
from fpm.io.config_reader import ConfigReader


logger = logging.getLogger("fpm.runner")


def parse_cla():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-cfg",
        "--config-path",
        dest="config_path",
        required=True,
        help=("Path to config.toml path that defines necessary parameters. "
              "See ./examples/experiment_config.toml for reference.")
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print debug info to console."
    )

    return parser.parse_args()


def compute_case(
    foam_case: OpenFoamCase,
    velocity: float,
    working_dir: pathlib.Path,
    simple_foam_runner_path: pathlib.Path,
    prep_postproc_runner_path: pathlib.Path,
    dest_dir: pathlib.Path
) -> dict:
    previous_u_boundary_types = foam_case.u_boundary_types
    new_u_boundary_types = previous_u_boundary_types
    new_u_boundary_types['left_field_value'] = f'uniform ({velocity} 0 0)'
    foam_case.change_velocity_boundary_types(new_u_boundary_types)

    utils.run_cmd(
        ["bash", simple_foam_runner_path]
    )

    latest_time = utils.run_cmd(
        args=["foamListTimes", "-latestTime", "-case", f"{working_dir / 'OF_case'}"]
    )

    logger.info("simpleFoam finished, latest time=%s", latest_time)

    utils.run_cmd(
        ["bash", f'{prep_postproc_runner_path}']
    )

    dest_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(dest_dir / f"fields_{latest_time}.vtk.gz", "w:gz") as tar:
        tar.add(
            working_dir / "OF_case" / f"VTK/OF_case_{latest_time}.vtk",
            arcname=f"fields_{latest_time}.vtk"
        )

    with tarfile.open(dest_dir / "simpleFoam.log.gz", "w:gz") as tar:
        tar.add(
            working_dir / "OF_case" / "simpleFoam.log",
            arcname="simpleFoam.log"
        )

    foam_case.save_spec_to_file(dest_dir / 'OF_spec.csv')

    manifest_data_dict = {
        "latest_time": latest_time,
        "vtk_file": dest_dir / f"fields_{latest_time}.vtk.gz",
        "absolute_path": dest_dir
    }

    return manifest_data_dict


def prepare_runner_files(work_dir: pathlib.Path, n_proc: int):
    simple_foam_runner_path = utils.create_runner_file(
        runner_name='run_simpleFoam.sh',
        runner_path=work_dir / 'OF_case',
        template_name="run_simpleFoam_template.jinja",
        templates_dir_path=pathlib.Path("fpm/templates/runners/"),
        var_dict={
            'number_of_procs': str(n_proc),
            'working_directory': f"{work_dir / 'OF_case'}"
        }
    )

    prep_postproc_runner_path = utils.create_runner_file(
        runner_name='run_prep_for_postproc.sh',
        runner_path=work_dir / 'OF_case',
        template_name="run_prep_for_postproc_template.jinja",
        templates_dir_path=pathlib.Path("fpm/templates/runners/"),
        var_dict={
            'number_of_procs': str(n_proc),
            'working_directory': f"{work_dir / 'OF_case'}"
        }
    )

    mesher_file_path = utils.create_runner_file(
        runner_name='run_meshing.sh',
        runner_path=work_dir / 'OF_case',
        template_name="run_meshing_template.jinja",
        templates_dir_path=pathlib.Path("fpm/templates/runners/"),
        var_dict={
            'number_of_procs': str(n_proc),
            'working_directory': f"{work_dir / 'OF_case'}"
        }
    )

    return {
        "simple_foam_runner_path": simple_foam_runner_path,
        "prep_postproc_runner_path": prep_postproc_runner_path,
        "mesher_file_path": mesher_file_path
    }


def main():
    args = parse_cla()
    start_time = time.time()
    config_path = pathlib.Path(args.config_path)
    config = ConfigReader(config_path)

    work_dir = config.case_cfg.run.working_directory
    work_dir.mkdir(parents=True, exist_ok=True)
    results_dir = config.case_cfg.run.results_directory
    cases_dir = results_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    utils.setup_logging(
        verbose=args.verbose,
        log_file=results_dir / "experiment.log"
    )

    porosity_list = config.case_cfg.run.porosities
    velocity_list = config.case_cfg.run.velocities
    geometries_per_porosity = config.case_cfg.run.number_of_geometries

    logger.info("Correctly read experiment config from %s", config_path)

    manifest_rows = []

    shutil.copy(config_path, results_dir / "experiment_config.toml")

    total_cases_processed = 0
    cases_in_experiment = (len(porosity_list)
                           * len(velocity_list)
                           * geometries_per_porosity)

    for geom_num, (porosity_i, porosity) in itertools.product(
        range(geometries_per_porosity),
        enumerate(porosity_list)
    ):
        foam_case = OpenFoamCase.from_config(config_path=config_path)

        foam_case.create_of_dir()

        foam_case.save_walls_stls(work_dir / 'OF_case' / 'constant' / 'triSurface')

        logger.info("Generating geometry %d with porosity %0.2f", geom_num, porosity)
        porous_medium = SwissCheese(
            porosity=porosity,
            bounds=config.case_cfg.medium.bounding_box.as_dict(),
            min_radius=config.case_cfg.medium.min_radius,
            max_radius=config.case_cfg.medium.max_radius,
            geometry_bounds_type=config.case_cfg.medium.geometry_bounds_type
        )
        porous_medium.walls = porous_medium.create_boundary_walls()
        porous_medium.obstacles = porous_medium.create_obstacles()
        porous_medium.save_stls(
            savepath=work_dir / 'OF_case' / 'constant' / 'triSurface'
        )
        logger.info("Preparing runner files for OpenFOAM...")
        runner_files = prepare_runner_files(
            work_dir=work_dir,
            n_proc=config.case_cfg.parallelism.number_of_procs
        )
        simple_foam_runner_path = runner_files["simple_foam_runner_path"]
        prep_postproc_runner_path = runner_files["prep_postproc_runner_path"]
        mesher_file_path = runner_files["mesher_file_path"]

        logger.info("Meshing the geometry...")
        utils.run_cmd(
            ["bash", f"{mesher_file_path}"]
        )
        logger.info("Meshing completed.")
        end_time = time.time()

        logger.debug("Meshing Elapsed time: %.2f seconds", end_time - start_time)

        porosity_dir = cases_dir / f"porosity_{porosity:0.5f}"
        geom_dir = porosity_dir / f"geometry_{geom_num:03}"
        geom_dir.mkdir(parents=True, exist_ok=True)

        porous_medium.save_spec_to_file(geom_dir / 'porous_medium_spec.csv')
        trisurface_dir = work_dir / 'OF_case' / 'constant' / 'triSurface'
        with tarfile.open(geom_dir / "geometry.tar.gz", "w:gz") as tar:
            for file in trisurface_dir.glob("*.stl"):
                tar.add(file, arcname=file.name)

        new_start_time = time.time()

        for velocity_i, velocity in enumerate(velocity_list):
            velocity_dir = geom_dir / f"velocity_{velocity:0.5e}"
            logger.info(
                "   Now processing for\n     Porosity: %0.5f [%d / %d]"
                "     Velocity: %0.5e [%d / %d]     Geometry: [%d / %d]"
                "     Total progress: %0.2f %%\n",
                porosity,
                porosity_i + 1,
                len(porosity_list),
                velocity,
                velocity_i + 1,
                len(velocity_list),
                geom_num + 1,
                geometries_per_porosity,
                100 * total_cases_processed / cases_in_experiment
            )

            case_manifest_info = compute_case(
                foam_case=foam_case,
                velocity=velocity,
                working_dir=work_dir,
                simple_foam_runner_path=simple_foam_runner_path,
                prep_postproc_runner_path=prep_postproc_runner_path,
                dest_dir=velocity_dir
            )
            logger.debug(
                "Computed one case in %0.2f seconds.",
                time.time() - new_start_time
            )
            new_start_time = time.time()

            total_cases_processed += 1

            manifest_rows.append({
                "case_id": len(manifest_rows),
                "aimed_porosity": porosity,
                "geom_num": geom_num,
                "inlet_velocity": velocity,
                "inlet_flow_rate": velocity * foam_case.inlet_area,
                "rel_path": case_manifest_info["absolute_path"].relative_to(
                    results_dir
                ),
                "latest_time": case_manifest_info["latest_time"],
                "vtk_archive": case_manifest_info["vtk_file"].relative_to(results_dir)
            })

        logger.info("Case's saved to %s", geom_dir)

        shutil.rmtree(work_dir / 'OF_case')

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_csv(results_dir / "manifest.csv", index=False)
    logger.info("Manifest CSV saved to %s", results_dir / "manifest.csv")

    logger.info(
        "Experiment finished. Post-process the results with "
        "`python scripts/postprocess.py --results-dir %s`.",
        results_dir,
    )


if __name__ == "__main__":
    main()
