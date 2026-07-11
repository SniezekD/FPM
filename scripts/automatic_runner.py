import pathlib
import os
import tarfile
import argparse

import fpm.utilities.utils as utils
from fpm.openfoam_case import OpenFoamCase
from fpm.media_models.swiss_cheese import SwissCheese

import time

#TODO: introduce logger


def parse_cla():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-wd",
        "--working-direcotry",
        dest="working_directory",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--porosities",
        help="Values of porosities for which simulations should be run.",
        required=True,
        type=list,
        nargs='+',
    )

    parser.add_argument(
        "--velocities",
        help=("Velocity values to run simulations for. For each geometry there will be "
              "as many simulations as there are velocities."),
        required=True,
        type=list,
        nargs='+',
    )

    return parser.parse_args()


def compute_case(
    foam_case: OpenFoamCase,
    velocity: float,
    working_dir: pathlib.Path,
    simple_foam_runner_path: pathlib.Path,
    prep_postproc_runner_path: pathlib.Path,
):
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
            f"/home/user/tests/OF_case/{latest_time}",
            velocity_dir / latest_time
        ]
    )
    utils.run_cmd(
        args=[
            'mv',
            "/home/user/tests/OF_case/foamRun.log",
            velocity_dir / 'foamRun.log'
        ]
    )
    utils.run_cmd(
        args=[
            'mv',
            f"/home/user/tests/OF_case/VTK/OF_case_{latest_time}.vtk",
            f"{velocity_dir / f'OF_case_{latest_time}.vtk'}"
        ]
    )

    foam_case.save_spec_to_file(velocity_dir / 'OF_spec.csv')

    with tarfile.open(f"{velocity_dir}.tar.gz", "w:gz") as tar:
        tar.add(velocity_dir, arcname=f"{velocity_dir.name}")

    print(f"Latest Time: {latest_time}")
    


def main():
    args = parse_cla()
    start_time = time.time()
    work_dir = pathlib.Path(args.working_directory)

    for porosity in args.porosities:

        foam_case = OpenFoamCase(
            working_direcory=work_dir,
            end_time=501,
            time_step=1,
            solver_name='simpleFoam',
            write_interval=50,
            number_of_procs=6,
            max_local_cells=2000000,
            max_global_cells=400000,
            min_surface_refinement_lvl=2,
            max_surface_refinement_lvl=3,
            seed_location_in_mesh=(-0.5, 0.5, 0.5),
            fluid_kinematic_viscosity=1e-6,
            blockmesh_boundary_types={
                'obstacles': 'wall',
                'front': 'wall',
                'back': 'wall',
                'up': 'wall',
                'down': 'wall',
                'left': 'patch',
                'right': 'patch'
            },
            u_boundary_types={
                'left_bc_type': 'fixedValue',
                'left_field_type': 'value',
                'left_field_value': 'uniform (1e-6 0 0)',
                'right_bc_type': 'zeroGradient',
                'right_field_type': None,
                'right_field_value': None,
                'up_bc_type': 'noSlip',
                'up_field_type': None,
                'up_field_value': None,
                'down_bc_type': 'noSlip',
                'down_field_type': None,
                'down_field_value': None,
                'front_bc_type': 'noSlip',
                'front_field_type': None,
                'front_field_value': None,
                'back_bc_type': 'noSlip',
                'back_field_type': None,
                'back_field_value': None,
                'obstacles_bc_type': 'noSlip',
                'obstacles_field_type': None,
                'obstacles_field_value': None
            },
            p_boundary_types={
                'left_bc_type': 'zeroGradient',
                'left_field_type': None,
                'left_field_value': None,
                'right_bc_type': 'fixedValue',
                'right_field_type': 'value',
                'right_field_value': 'uniform 0',
                'up_bc_type': 'zeroGradient',
                'up_field_type': None,
                'up_field_value': None,
                'down_bc_type': 'zeroGradient',
                'down_field_type': None,
                'down_field_value': None,
                'front_bc_type': 'zeroGradient',
                'front_field_type': None,
                'front_field_value': None,
                'back_bc_type': 'zeroGradient',
                'back_field_type': None,
                'back_field_value': None,
                'obstacles_bc_type': 'zeroGradient',
                'obstacles_field_type': None,
                'obstacles_field_value': None
            },
            bounding_box_coords={
                'x_min': -20,
                'x_max': 16+30,
                'y_min': 0,
                'y_max': 16,
                'z_min': 0,
                'z_max': 16,
            },
            bounding_box_discretization={
                'dx': 66 * 4,
                'dy': 64,
                'dz': 64,
            },
            turbulence_model=None,
            decompose_method=None,
            transport_model=None
        )

        foam_case.create_of_dir()

        foam_case.save_walls_stls(work_dir / 'OF_case' / 'constant' / 'triSurface')

        pm = SwissCheese(
            porosity=porosity,
            bounds=[0, 16, 0, 16, 0, 16],
            min_radius=0.1,
            max_radius=1,
            geometry_bounds_type='non_periodic'
        )
        pm.walls = pm.create_boundary_walls()
        pm.obstacles = pm.create_obstacles()
        pm.save_stls(savepath=work_dir / 'OF_case' / 'constant' / 'triSurface')

        mesher_file_path = utils.create_runner_file(
            runner_name='run_meshing.sh',
            runner_path=work_dir / 'OF_case',
            template_name="run_meshing_template.jinja",
            templates_dir_path="fpm/templates/runners/",
            var_dict={
                'number_of_procs': '6',
                'working_directory': f"{work_dir / 'OF_case'}"
            }
        )
        utils.run_cmd(
            ["bash", f"{mesher_file_path}"]
        )
        end_time = time.time()

        print(f"Meshing Elapsed time: {end_time - start_time:0.2f} seconds")

        new_start_time = time.time()

        simple_foam_runner_path = utils.create_runner_file(
            runner_name='run_foamRun.sh',
            runner_path=work_dir / 'OF_case',
            template_name="run_foamRun_template.jinja",
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

        velocities = args.velocities

        for i, velocity in enumerate(velocities):
            print(f"   Now processing for velocity: {velocity}")
            compute_case(
                foam_case=foam_case,
                velocity=velocity,
                working_dir=work_dir,
                simple_foam_runner_path=simple_foam_runner_path,
                prep_postproc_runner_path=prep_postproc_runner_path,
            )
            print(time.time() - new_start_time)
            new_start_time = time.time()

        constant_dir = work_dir / 'OF_case' / 'constant'
        pm.save_spec_to_file(constant_dir / 'porous_medium_spec.csv')

        with tarfile.open(f"{constant_dir}.tar.gz", "w:gz") as tar:
            tar.add(constant_dir, arcname=constant_dir.name)

        with tarfile.open(f"OF_case_porosity{porosity}.tar.gz", "w:gz") as tar:
            files_to_tar = [
                file for file in os.listdir(work_dir / 'OF_case') if '.tar.gz' in file
                ]
            for file in files_to_tar:
                tar.add(work_dir / 'OF_case' / file, arcname=file)


if __name__ == "__main__":
    main()