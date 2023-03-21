import os
import utils
import argparse
import numpy as np
from postProcessing import IFMP_postProc
from pathlib import Path
from ifpm import IFPM

def get_args():
    parser = argparse.ArgumentParser(
                    prog = 'automaticIFPM',
                    description = 'This program automaticaly generates results for IFPM')
    parser.add_argument("Re_min", type=float, help='Minimal common (base 10) logarithm of Reynold number.') 
    parser.add_argument("Re_max", type=float, help='Maximal common (base 10) logarithm of Reynold number.')
    parser.add_argument("Re_num", type=int, help='Number of Reynold numbers between Re_min and Re_max to run simulation for.')            
    parser.add_argument("-gn","--geometry_number", type=int, help='Number of different geometry realisations to simulate', default=10)
    parser.add_argument("-x","--x_size", type=int, help='Size of the model in X-direction.', default=64)
    parser.add_argument("-y","--y_size", type=int, help='Size of the model in Y-direction.', default=64)
    parser.add_argument("-z","--z_size", type=int, help='Size of the model in Z-direction.', default=1)
    parser.add_argument("-on","--outname", type=str, help='Name of the output file with Re vs pi.', default='results')  
    parser.add_argument("-r","--reset", type=str, help='Wheater or not to delete the output file', default='false')      
    parser.add_argument("-marg","--margins", type=int, help='Size of the margin', default=4)
    parser.add_argument("-eps","--epsilon", type=float, help='Lattice porosity', default=0.9)
    parser.add_argument("-wd","--work_dir", type=str, help='Working directory', default='/home/damian/MGR/wd')
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
    
    # Change the dos endline convention to unix convention 
    for f in ['prep_model.sh', 'run_meshing.sh', 'run_meshing2D.sh', 'run_simpleFoam.sh']:
        os.system(f'dos2unix {f}')

    os.makedirs(wd, exist_ok=True)
    Re_arr = [10**Re for Re in np.linspace(Re_min, Re_max, Re_num)]

    for k in range(geometry_number):
        if reset:
            outFile = open(f"{args.outname}-{k}.dat", "w")
        else:
            outFile = open(f"{args.outname}-{k}.dat", "a")
        outFile.write("Re\tPI\tT\tEntropy\n")

        ifpm = IFPM(porosity=epsilon, size={'x': x, 'y': y, 'z': z}, margin= margin, working_dir=Path(wd))
        ifpm.prepare_model()
        ifpm.run_meshing()
        for Re, i in zip(Re_arr, range(Re_num)):
            print(f"\n[{k+1}/{geometry_number}]\n [{i+1}/{Re_num}] Current Re ~= {Re:0.4f}")

            ifpm.prepare_initial_conditions(Re)
            ifpm.run_single_simulation(Re)
            ifpm.save_as_VTK()

            ifpm_pp = IFMP_postProc(ifpm)
            outFile.write(f"{Re}\t{ifpm_pp.pi}\t{ifpm_pp.T}\t{ifpm_pp.entropy}\n")
            
    utils.make_plot(geometry_number)
