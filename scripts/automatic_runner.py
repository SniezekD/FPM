import pathlib
import os
import tarfile
import argparse
import shutil
import itertools

import pandas as pd
import matplotlib.pyplot as plt

import fpm.utilities.utils as utils
from fpm.openfoam_case import OpenFoamCase
from fpm.media_models.swiss_cheese import SwissCheese
from fpm.io.config_reader import ConfigReader
from fpm.io.vtk_reader import read_vtk

from fpm.utilities.participation_number import compute_participation_number
from fpm.utilities.tortuosity import compute_tortuosity
from fpm.utilities.rho_minus import compute_rho_minus

import time


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

    return parser.parse_args()


def compute_case(
    foam_case: OpenFoamCase,
    velocity: float,
    working_dir: pathlib.Path,
    simple_foam_runner_path: pathlib.Path,
    prep_postproc_runner_path: pathlib.Path,
    interest_b_box: tuple,
) -> pd.DataFrame:
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

    utils.run_cmd(
        ["bash", f'{prep_postproc_runner_path}']
    )

    velocity_dir = working_dir / 'OF_case' / f"U_{velocity}"
    velocity_dir.mkdir(exist_ok=True, parents=True)

    utils.run_cmd(
        args=[
            'mv',
            working_dir / "OF_case" / latest_time,
            velocity_dir / latest_time
        ]
    )
    utils.run_cmd(
        args=[
            'mv',
            working_dir / "OF_case" / "simpleFoam.log",
            velocity_dir / 'simpleFoam.log'
        ]
    )
    utils.run_cmd(
        args=[
            'mv',
            working_dir / "OF_case" / f"VTK/OF_case_{latest_time}.vtk",
            f"{velocity_dir / f'OF_case_{latest_time}.vtk'}"
        ]
    )

    foam_case.save_spec_to_file(velocity_dir / 'OF_spec.csv')

    with tarfile.open(f"{velocity_dir}.tar.gz", "w:gz") as tar:
        tar.add(velocity_dir, arcname=f"{velocity_dir.name}")

    print(f"Latest Time: {latest_time}")
    vtk_df = read_vtk(
            f"{velocity_dir / f'OF_case_{latest_time}.vtk'}",
            interest_b_box=interest_b_box
        )

    return vtk_df


def prepare_runner_files(work_dir: pathlib.Path, n_proc: int):
    simple_foam_runner_path = utils.create_runner_file(
        runner_name='run_simpleFoam.sh',
        runner_path=work_dir / 'OF_case',
        template_name="run_simpleFoam_template.jinja",
        templates_dir_path="fpm/templates/runners/",
        var_dict={
            'number_of_procs': '6',
            'working_directory': f"{work_dir / 'OF_case'}"
        }
    )

    prep_postproc_runner_path = utils.create_runner_file(
        runner_name='run_prep_for_postproc.sh',
        runner_path=work_dir / 'OF_case',
        template_name="run_prep_for_postproc_template.jinja",
        templates_dir_path="fpm/templates/runners/",
        var_dict={
            'number_of_procs': '6',
            'working_directory': f"{work_dir / 'OF_case'}"
        }
    )

    mesher_file_path = utils.create_runner_file(
        runner_name='run_meshing.sh',
        runner_path=work_dir / 'OF_case',
        template_name="run_meshing_template.jinja",
        templates_dir_path="fpm/templates/runners/",
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


def plot_results(results_df: pd.DataFrame, results_dir: pathlib.Path):
    for porosity in results_df['porosity'].unique():
        plot_df = results_df.loc[results_df["porosity"] == porosity]

        plot_df.plot(
            x='inlet_flow_rate',
            y='tortuosity',
            kind='scatter',
            title=f'All geometries with porosity {porosity}'
        )
        plt.xlabel(r"Inlet Flow Rate [m$^3$/s]")
        plt.ylabel("Tortuosity")
        plt.grid(linestyle="--", color="gray")
        plt.savefig(results_dir / f"tortuosity_all_porosity_{porosity}.png")
        plt.close()

        plot_df.plot(
            x='inlet_flow_rate',
            y='participation_number',
            kind='scatter',
            title=f'All geometries with porosity {porosity}'
        )
        plt.xlabel(r"Inlet Flow Rate [m$^3$/s]")
        plt.ylabel("Participation Number")
        plt.grid(linestyle="--", color="gray")
        plt.savefig(results_dir / f"participation_number_all_porosity_{porosity}.png")
        plt.close()

        plot_df.plot(
            x='inlet_flow_rate',
            y='rho_minus',
            kind='scatter',
            title=f'All geometries with porosity {porosity}'
        )
        plt.xlabel(r"Inlet Flow Rate [m$^3$/s]")
        plt.ylabel(r"\rho^-")
        plt.grid(linestyle="--", color="gray")
        plt.savefig(results_dir / f"rho_minus_all_porosity_{porosity}.png")
        plt.close()

        for geom_no in plot_df["geometry_number"].unique():
            geom_plot_df = plot_df.loc[plot_df["geometry_number"] == geom_no]
            geom_plot_df.plot(
                x='inlet_flow_rate',
                y='tortuosity',
                kind='scatter',
                title=f'Geometry {geom_no} with porosity {porosity}'
            )
            plt.xlabel(r"Inlet Flow Rate [m$^3$/s]")
            plt.ylabel("Tortuosity")
            plt.grid(linestyle="--", color="gray")
            plt.savefig(
                results_dir / f"tortuosity_porosity_{porosity}_geom_{geom_no}.png"
            )
            plt.close()

            geom_plot_df.plot(
                x='inlet_flow_rate',
                y='participation_number',
                kind='scatter',
                title=f'Geometry {geom_no} with porosity {porosity}'
            )
            plt.xlabel(r"Inlet Flow Rate [m$^3$/s]")
            plt.ylabel("Participation Number")
            plt.grid(linestyle="--", color="gray")
            plt.savefig(
                results_dir / 
                f"participation_number_porosity_{porosity}_geom_{geom_no}.png"
            )
            plt.close()

            geom_plot_df.plot(
                x='inlet_flow_rate',
                y='rho_minus',
                kind='scatter',
                title=f'Geometry {geom_no} with porosity {porosity}'
            )
            plt.xlabel(r"Inlet Flow Rate [m$^3$/s]")
            plt.ylabel(r"\rho^-")
            plt.grid(linestyle="--", color="gray")
            plt.savefig(
                results_dir / f"rho_minus_porosity_{porosity}_geom_{geom_no}.png"
            )
            plt.close()


def main():
    args = parse_cla()
    start_time = time.time()
    config_path = pathlib.Path(args.config_path)
    config = ConfigReader(config_path)

    work_dir = config.case_cfg.run.working_directory
    work_dir.mkdir(parents=True, exist_ok=True)
    results_dir = config.case_cfg.run.results_directory
    porosity_list = config.case_cfg.run.porosities
    velocity_list = config.case_cfg.run.velocities
    geometries_per_porosity = config.case_cfg.run.number_of_geometries

    results_rows = []

    shutil.copy(config_path, work_dir / "experiment_config.toml")

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

        runner_files = prepare_runner_files(
            work_dir=work_dir,
            n_proc=config.case_cfg.parallelism.number_of_procs
        )
        simple_foam_runner_path = runner_files["simple_foam_runner_path"]
        prep_postproc_runner_path = runner_files["prep_postproc_runner_path"]
        mesher_file_path = runner_files["mesher_file_path"]

        utils.run_cmd(
            ["bash", f"{mesher_file_path}"]
        )
        end_time = time.time()

        print(f"Meshing Elapsed time: {end_time - start_time:0.2f} seconds")

        new_start_time = time.time()

        for velocity_i, velocity in enumerate(velocity_list):
            print(f"   Now processing for\n"
                  f"     Porosity: {porosity} [{porosity_i + 1} / {len(porosity_list)}]"
                  f"     Velocity: {velocity} [{velocity_i + 1} / {len(velocity_list)}]"
                  f"     Geometry: [{geom_num + 1} / {geometries_per_porosity}]"
                  f"     Total progress: "
                  f"{100 * total_cases_processed / cases_in_experiment:0.2f}%\n")

            vtk_df = compute_case(
                foam_case=foam_case,
                velocity=velocity,
                working_dir=work_dir,
                simple_foam_runner_path=simple_foam_runner_path,
                prep_postproc_runner_path=prep_postproc_runner_path,
                interest_b_box=tuple(
                    config.case_cfg.medium.bounding_box.as_dict().values()
                )
            )
            print(time.time() - new_start_time)
            new_start_time = time.time()

            total_cases_processed += 1

            results_rows.append({
                "porosity": porosity,
                "velocity": velocity,
                "tortuosity": compute_tortuosity(
                    vtk_df,
                    streamwise_axis=foam_case.streamwise_axis
                ),
                "participation_number": compute_participation_number(vtk_df),
                "rho_minus": compute_rho_minus(
                    vtk_df,
                    streamwise_axis=foam_case.streamwise_axis
                ),
                "inlet_flow_rate": velocity * foam_case.inlet_area,
                "geometry_number": geom_num,
            })

        constant_dir = work_dir / 'OF_case' / 'constant'
        porous_medium.save_spec_to_file(constant_dir / 'porous_medium_spec.csv')

        with tarfile.open(f"{constant_dir}.tar.gz", "w:gz") as tar:
            tar.add(constant_dir, arcname=constant_dir.name)

        tar_name = f"FOAM_case_geom_no_{geom_num}_porosity{porosity}.tar.gz"
        tar_path = results_dir / tar_name
        print(f"Saving the tarball to {tar_path}")
        with tarfile.open(tar_path, "w:gz") as tar:
            files_to_tar = [
                file
                for file in os.listdir(work_dir / 'OF_case')
                if '.tar.gz' in file
                ]
            for file in files_to_tar:
                tar.add(work_dir / 'OF_case' / file, arcname=file)

        shutil.rmtree(work_dir / 'OF_case')

    results_df = pd.DataFrame(results_rows)

    results_df.to_csv(results_dir / "resutls.csv", index=False)

    plot_results(results_df, results_dir)


if __name__ == "__main__":
    main()
