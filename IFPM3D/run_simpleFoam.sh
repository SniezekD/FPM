#!/bin/bash

check_return_code () {
if [ $1 -eq 0 ]; then
    echo "     Done in $2"
else
    echo "     Error with code $1, exiting."
    exit 1
fi
}

Re=$1

source /usr/lib/openfoam/openfoam2006/etc/bashrc

cd ../OF_Model 
echo "    Decomposing"
starta=$SECONDS
decomposePar -force &> decomposePar.log
check_return_code $? $SECONDS - $starta

echo "    Running simpleFoam"
startb=$SECONDS
mpirun -np 6 simpleFoam -parallel &> logs/simpleFoam${Re}.log
check_return_code $? $SECONDS - $startb

echo "    Reconstructing"
startc=$SECONDS
reconstructPar &> reconstructPar.log
check_return_code $?  $SECONDS - $startc
