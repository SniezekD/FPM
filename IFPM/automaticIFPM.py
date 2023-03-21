import os
import utils
import argparse
import numpy as np
import shutil
from postProcessing import IFMP_postProc
from pathlib import Path
from ifpm import IFPM

def get_args():
    parser = argparse.ArgumentParser(
                    prog = 'automaticIFPM',
                    description = 'This program automaticaly \
                                   generates results for IFPM'
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
        type=str,
        default='false',
        help='Wheater or not to delete the output file'
        )      
    parser.add_argument(
        "-marg",
        "--margins",
        type=int,
        default=4,
        help='Size of the margin'
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
        default='/home/damian/MGR/wd',
        help='Working directory'
        )
    parser.add_argument(
        "-s",
        "--save",
        type=str,
        default='false',
        help='Save openFOAM directory for each Re?'
        )
    return parser.parse_args()


if __name__ == '__main__':
    args            = get_args()
    x               = args.x_size
    y               = args.y_size
    z               = args.z_size
    margin          = args.margins
    Re_min          = args.Re_min
    Re_max          = args.Re_max
    Re_num          = args.Re_num
    geometry_number = args.geometry_number
    reset           = utils.str2bool(args.reset)
    epsilon         = args.epsilon
    wd              = args.work_dir
    save            = utils.str2bool(args.save)
    
    # Change the dos endline convention to unix convention 
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
        outFile.write("Re\tPI\tT\tEntropy\n")

        ifpm = IFPM(
            porosity=epsilon,
            size={'x': x, 'y': y, 'z': z},
            margin= margin,
            working_dir=Path(wd)
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
            ifpm.save_as_VTK()

            ifpm_pp = IFMP_postProc(ifpm)
            outFile.write(
                    f"{Re}\t{ifpm_pp.pi}\t{ifpm_pp.T}\t{ifpm_pp.entropy}\n"
                    )
            if save and k==0:
                if ifpm.size['z'] == 1:
                    save_path = Path(
                        f'/home/damian/sharedVol/OF_2D_Model_save/OF_Model_{Re:0.4f}'
                        )
                else:
                    save_path = Path(
                        f'/home/damian/sharedVol/OF_3D_Model_save/OF_Model_{Re:0.4f}'
                        )
                of_path = Path(wd)
                of_path = of_path.joinpath('OF_Model')
                os.makedirs(save_path, exist_ok=True)
                shutil.copytree(src=of_path, dst=save_path, dirs_exist_ok=True)
            
    utils.make_plot(geometry_number)
