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

cd ../OF_Model 
echo "    Decomposing"
decomposePar -force &> decomposePar.log
check_return_code $?

echo "    Running simpleFoam"
mpirun -np 6 simpleFoam -parallel &> logs/simpleFoam${Re}.log
check_return_code $?

echo "    Reconstructing"
reconstructPar &> reconstructPar.log
check_return_code $?
