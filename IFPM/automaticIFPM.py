import os
import sys
import argparse
import subprocess
import numpy as np
import preapareRandomCaseFrame as prcf
import prepareInitialConditions as pic

from calculatePi import get_Pi

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def run_cmd(args: list) -> float:
    status = subprocess.run(args)
    if status.returncode == 0:
        print("     Done")
    else:
        print(f"     Error! \n{args} ended with code {status.returncode}.")
        sys.exit(status)

def get_args():
    parser = argparse.ArgumentParser(
                    prog = 'automaticIFPM',
                    description = 'This program automaticaly generates results for IFPM')
    parser.add_argument("Re_min",  type=float, help='Minimal Reynold number.') 
    parser.add_argument("Re_max",  type=float, help='Maximal Reynold number.')
    parser.add_argument("Re_num",  type=int, help='Number of Reynold numbers between Re_min and Re_max to run simulation for.')            
    parser.add_argument("-n","--name",    type=str,   help='Name of the model.', 
                                    default='model')
    parser.add_argument("-on","--outname", type=str,   help='Name of the output file with Re vs pi.', 
                                   default='REvsPI.dat')  
    parser.add_argument("-r","--reset",   type=str,  help='Wheater or not to delete the output file', 
                                   default='false')      
    parser.add_argument("-nl","--n_lattice",       type=int,   help='Porosity lattice size in number of grains.', 
                                   default=64)           
    parser.add_argument("-ml","--m_lattice",       type=int,   help='How many grains length to add before and after porosity lattice?', 
                                   default=4)
    return parser.parse_args()

args   = get_args()
n      = args.n_lattice
m      = args.m_lattice
Re_min = args.Re_min
Re_max = args.Re_max
Re_num = args.Re_num
name   = args.name
reset  = str2bool(args.reset)

U_file_path = "/home/damian/MGR/OF_Model/500/U"

if reset:
    outFile = open(args.outname, "w")
else:
    outFile = open(args.outname, "a")

print("Creating the lattice")
lattice, grains_names = prcf.create_lattice_stl(prcf.create_random_lattice(0.9,n), save_name=name, n=n, m = m)
run_cmd([r'./prep_model.sh'])


run_cmd([r'./run_meshing.sh'])
for Re, i in zip(np.linspace(Re_min, Re_max, Re_num), range(Re_num)):
    print(f"\nCurret Re ~= {Re:0.4f} [{i}/{Re_num}]")
    print("    Preparing the initial Condition")
    p_file = open('../OF_Model/0/p','w')
    U_file = open('../OF_Model/0/U','w')
    pic.make_0_U(grains_names, U_file, Re)
    pic.make_0_p(grains_names, p_file)
    print("     Done")

    run_cmd([r'./run_simpleFoam.sh', f'{Re:0.4f}'])


    print("    Calculating Participation number")
    pi = get_Pi(U_file_path)
    print("     Done")

    outFile.write(f"{Re}\t{pi}\n")

outFile.close()
