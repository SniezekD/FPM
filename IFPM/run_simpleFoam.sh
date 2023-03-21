#!/bin/bash

check_return_code () {
if [ $1 -eq 0 ]; then
    echo "     Done"
else
    echo "     Error with code $1, exiting."
    exit 1
fi
}

Re=$1
source /usr/lib/openfoam/openfoam2006/etc/bashrc

cd ../wd/OF_Model 
echo "    Decomposing"
# decomposePar -force -fields -zeroTime &> decomposePar.log
# check_return_code $?

echo "    Running simpleFoam"
if [ ! -d simpleLogs ]; then
    mkdir simpleLogs
fi
# mpirun -np 6 simpleFoam -parallel &> logs/simpleFoam${Re}.log
simpleFoam &> simpleLogs/simpleFoam${Re}.log
# check_return_code $?
echo "    Reconstructing"
# reconstructPar &> reconstructPar.log
# check_return_code $?

echo "    Converting foam to VTK"
foamToVTK -latestTime -ascii  &> foamToVTK.log
check_return_code $?

echo "    Removing all processors' directories"
if [  -d  processor* ]; then
    rm -r processor*
fi
check_return_code $?
