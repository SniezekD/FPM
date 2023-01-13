import os
import sys
import argparse
import subprocess
import numpy as np
import fRE
import preapareRandomCaseFrame3D as prcf
import prepareInitialConditions as pic

from calculatePi3D import get_Pi
from createBlockMeshDict import createBlockMeshDict
from createSnappyHexMeshDict import createSnappyHexMeshDict

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
                    prog = 'automaticIFPM3D',
                    description = 'This program automaticaly generates results for IFPM3D')
    parser.add_argument("Re_min",  type=float, help='Minimal common (base 10) logarithm of Reynold number.') 
    parser.add_argument("Re_max",  type=float, help='Maximal common (base 10) logarithm of Reynold number.')
    parser.add_argument("Re_num",  type=int, help='Number of Reynold numbers between Re_min and Re_max to run simulation for.')            
    parser.add_argument("-n","--name",    type=str,   help='Name of the model.', 
                                    default='model')
    parser.add_argument("-on","--outname", type=str,   help='Name of the output file with Re vs pi.', 
                                   default='results')  
    parser.add_argument("-r","--reset",   type=str,  help='Wheater or not to delete the output file', 
                                   default='false')      
    parser.add_argument("-nl","--n_lattice",       type=int,   help='Porosity lattice size in number of grains.', 
                                   default=64)           
    parser.add_argument("-ml","--m_lattice",       type=int,   help='How many grains length to add before and after porosity lattice?', 
                                   default=4)
    parser.add_argument("-eps","--epsilon",       type=float,   help='Lattice porosity', 
                                   default=0.9)
    return parser.parse_args()

args    = get_args()
n       = args.n_lattice
m       = args.m_lattice
Re_min  = args.Re_min
Re_max  = args.Re_max
Re_num  = args.Re_num
name    = args.name
reset   = str2bool(args.reset)
epsilon = args.epsilon

postProcessPath = "/home/damian/MGR/OF_Model/postProcessing/"
postProcessAvDat = "/0/surfaceFieldValue.dat"
outletPostProcessPath = postProcessPath + "OutletPAverage" + postProcessAvDat
inletPostProcessPath = postProcessPath + "InletPAverage" + postProcessAvDat
blockMeshdictPath = "/home/damian/MGR/OF_Model/system/blockMeshDict"
snappyHexMeshDictPath = "/home/damian/MGR/OF_Model/system/snappyHexMeshDict"

Nstart = 0 # number of different geometries to simulate
Nend = 10 # number of different geometries to simulate
for k in range(Nstart, Nend):
    Re_arr = [10**Re for Re in np.linspace(Re_min, Re_max, Re_num)]
    U_file_path = "/home/damian/MGR/OF_Model/500/U"

    if reset:
        outFile = open(f"{args.outname}-{k}.dat", "w")
    else:
        outFile = open(f"{args.outname}-{k}.dat", "a")

    outFile.write("Re\tPI\tf\tRe'\n")

    print("\n+----------------------------------+")
    print(f"\n[{k+1}/{Nend}] Creating the lattice")
    lattice, grains_names = prcf.create_lattice_stl(epsilon, save_name=name, n=n, m=m)
    run_cmd([r'./prep_model.sh'])

    createBlockMeshDict(blockMeshdictPath, n, m)
    createSnappyHexMeshDict(snappyHexMeshDictPath)
    
    run_cmd([r'./run_meshing.sh'])
    for Re, i in zip(Re_arr, range(Re_num)):
        u = Re*1e-6

        print(f"\n[{k+1}/{Nend}]\n [{i+1}/{Re_num}] Current Re ~= {Re:0.4f}")
        print("    Preparing the initial Condition")
        p_file = open('../OF_Model/0/p','w')
        U_file = open('../OF_Model/0/U','w')
        
        pic.make_0_U(grains_names, n, U_file, Re)
        pic.make_0_p(grains_names, n, p_file)
        print("     Done")

        run_cmd([r'./run_simpleFoam.sh', f'{Re:0.4f}'])
        
        print("    Calculating f and Re")
        dp     = fRE.readDPfromFile(inletPostProcessPath, outletPostProcessPath)
        f      = fRE.calcf(dp, u)
        RePrim = fRE.calcRePrim(u)

        print("    Calculating Participation number")
        pi = get_Pi(U_file_path)
        print("     Done")

        outFile.write(f"{Re}\t{pi}\t{f}\t{RePrim}\n")
        if k == 0:
            if f'../OF_{Re:0.4f}' not in os.listdir('../'):
                os.system(rf'mkdir ../OF_{Re:0.4f}')
            os.system(rf'cp -r ../OF_Model ../OF_{Re:0.4f}')

    outFile.close()
