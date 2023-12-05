import os
import pathlib
import argparse
import numpy as np
import shutil

from ifpm import utils
from ifpm.postProcessing import IFPM_postProc
from pathlib import Path
from ifpm.ifpm import IFPM, FractalIFPM


def get_args():
    parser = argparse.ArgumentParser(
        prog='automaticIFPM',
        description='This program automaticaly generates results for IFPM'
    )
    parser.add_argument(
        "Re_min",
        type=float,
        help='Minimal common (base 10) logarithm of Reynold number.'
    )
    parser.add_argument(
        "Re_max",
        type=float,
        help='Maximal common (base 10) logarithm of Reynold number.'
    )
    parser.add_argument(
        "Re_num",
        type=int,
        help='Number of Reynold numbers between Re_min and Re_max \
              to run a simulation for.'
    )
    parser.add_argument(
        "-gn",
        "--geometry_number",
        type=int,
        default=10,
        help='Number of different geometry realisations to simulate'
    )
    parser.add_argument(
        "-x",
        "--x_size",
        type=int,
        default=64,
        help='Size of the model in X-direction.'
    )
    parser.add_argument(
        "-y",
        "--y_size",
        type=int,
        default=64,
        help='Size of the model in Y-direction.'
    )
    parser.add_argument(
        "-z",
        "--z_size",
        type=int,
        default=1,
        help='Size of the model in Z-direction.'
    )
    parser.add_argument(
        "-on",
        "--outname",
        type=str,
        default='results',
        help='Name of the output file with Re vs pi.'
    )
    parser.add_argument(
        "-r",
        "--reset",
        action='store_true',
        help='Whether or not to delete the output file'
    )
    parser.add_argument(
        "-imarg",
        "--inlet_margin",
        type=int,
        default=4,
        help='Size of the inlet margin'
    )
    parser.add_argument(
        "-omarg",
        "--outlet_margin",
        type=int,
        default=4,
        help='Size of the outlet margin'
    )
    parser.add_argument(
        "-eps",
        "--epsilon",
        type=float,
        default=0.9,
        help='Lattice porosity'
    )
    parser.add_argument(
        "-wd",
        "--work_dir",
        type=str,
        default='/home/user/MGR/wd',
        help='Working directory'
    )
    parser.add_argument(
        '-procs',
        '--number-of-processors',
        help=("On how many processors parallelised OpenFOAM related parts "
              "should run"),
        required=False,
        default=6
    )
    parser.add_argument(
        "-s",
        "--save",
        action='store_true',
        help=('Save openFOAM directory for each Re for the first '
              'geometry realisation?')
    )
    parser.add_argument(
        "-rr",
        "--rounding_radius",
        type=float,
        default=1.0,
        help=("Rounding radius used to round the vertices of the cubes. "
              "It should be defined as the fraction of the cube's edge length. "
              "If defined as more than sqrt(3)/2 ~= 0.866 there will be "
              "sharp cubes, if defined as less than or equal to 0.5 there "
              "will be spheres.")
    )
    parser.add_argument(
        "-sso",
        "--save_separate_obstacles",
        action='store_true',
        help=("If present, separate obstacles' stls will be saved "
              "instead of one collective one.")
    )
    parser.add_argument(
        "-fractal",
        "--fractal_lvl",
        type=int,
        default=0,
        help=("If set to integer greater than 0 the geometry will be "
              "Sierpinski carpet (2D) of Manger Sponge (3D) "
              "- depends on the size of the system.")
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    x = args.x_size
    y = args.y_size
    z = args.z_size

    in_margin = args.inlet_margin
    out_margin = args.outlet_margin

    Re_min = args.Re_min
    Re_max = args.Re_max
    Re_num = args.Re_num

    geometry_number = args.geometry_number
    reset = args.reset
    save = args.save
    s_s_o = args.save_separate_obstacles

    epsilon = args.epsilon
    wd = args.work_dir
    r_radius = args.rounding_radius
    fractal_lvl = args.fractal_lvl

    # Change the dos endline convention to unix convention.
    for f in ['prep_model.sh', 'run_meshing.sh',
              'run_meshing2D.sh', 'run_simpleFoam.sh']:
        os.system(f'dos2unix {f}')

    os.makedirs(wd, exist_ok=True)
    Re_arr = [10**Re for Re in np.linspace(Re_min, Re_max, Re_num)]

    for k in range(geometry_number):
        if reset:
            outFile = open(f"{args.outname}-{k}.dat", "w")
        else:
            outFile = open(f"{args.outname}-{k}.dat", "a")

        outFile.write("Re\tPI\tT\tAvg_Delta_P\tAVG_uX\tAVG_uMag\tFriction\tRe'"
                      "\tVortex_mean_kinetic_energy"
                      "\tVortex_mean_kinetic_energy_normalized"
                      "\tPI_numerator\tPI_denominator\n")

        if fractal_lvl > 0:
            ifpm = FractalIFPM(
                fractal_level=fractal_lvl,
                size={'x': x, 'y': y, 'z': z},
                in_margin=in_margin,
                out_margin=out_margin,
                working_dir=Path(wd),
                proc_num=args.number_of_processors,
                s_o=s_s_o
            )
        else:
            ifpm = IFPM(
                porosity=epsilon,
                size={'x': x, 'y': y, 'z': z},
                in_margin=in_margin,
                out_margin=out_margin,
                working_dir=Path(wd),
                r_r=r_radius,
                proc_num=args.number_of_processors,
                s_o=s_s_o
                )

        ifpm.prepare_model()
        ifpm.run_meshing()

        for Re, i in zip(Re_arr, range(Re_num)):
            print(
                f"\n[{k+1}/{geometry_number}]\n",
                f"[{i+1}/{Re_num}] Current Re ~= {Re:0.4f}"
                )

            ifpm.prepare_initial_conditions(Re)
            ifpm.run_single_simulation(Re)
            ifpm.prep_convergence(Re)

            # vtk_path = ifpm.wd.joinpath('OF_Model', 'VTK', 'OF_Model_50000.vtm') # pimple
            vtk_path = ifpm.wd.joinpath('OF_Model', 'VTK', 'OF_Model_500.vtm') # simple
            # vtk_path = ifpm.wd.joinpath('OF_Model', 'VTK', 'OF_Model_350.vtm') # piso
            ifpm_pp = IFPM_postProc(
                vtk_path,
                ifpm.in_margin,
                ifpm.out_margin,
                ifpm.size
            )
            vortex_ke = ifpm_pp.calculate_avg_kinetic_energy_in_vortices()
            vortex_ke_norm = ifpm_pp.calculate_avg_kinetic_energy_in_vortices(
                normalize=True
            )
            pi_numerator = ifpm_pp.uMag_sum
            pi_denominator = ifpm_pp.uX_sum

            outFile.write(
                (f"{Re}\t{ifpm_pp.pi}\t{ifpm_pp.T}\t{ifpm_pp.delta_p}"
                 f"\t{ifpm_pp.uX_avg}\t{ifpm_pp.uMag_avg}"
                 f"\t{ifpm_pp.friction_factor}\t{ifpm_pp.re_Dash}"
                 f"\t{vortex_ke}\t{vortex_ke_norm}"
                 f"\t{pi_numerator}\t{pi_denominator}\n")
            )

            if save and k == 0:
                sharedvol_path = pathlib.Path('/home/user/sharedVol')
                if ifpm.size['z'] == 1:
                    save_path = sharedvol_path.joinpath(
                        f'OF_2D_Model_save/OF_Model_{Re:0.4f}'
                    )
                else:
                    save_path = sharedvol_path.joinpath(
                        f'OF_3D_Model_save/OF_Model_{Re:0.4f}'
                    )
                of_path = Path(wd)
                of_path = of_path.joinpath('OF_Model')
                os.makedirs(save_path, exist_ok=True)
                shutil.copytree(src=of_path, dst=save_path, dirs_exist_ok=True)
