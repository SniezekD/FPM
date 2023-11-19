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

# if (( $(echo "$Re > 0.01" |bc -l) )); then
#     echo "    Mapping fields from previous case pimpleFoam"
#     mapFields -case /home/user/sharedVol/OF_Model -consistent -sourceTime 0  &> mapFields.log
#     sed -i sed -i 's/endTime         50000;/endTime         25000;/' ../wd/OF_Model/system/controlDict
# fi

cd ../wd/OF_Model 
echo "    Decomposing"
decomposePar -force &> decomposePar.log
check_return_code $?

echo "    Running simpleFoam"
if [ ! -d simpleLogs ]; then
    mkdir simpleLogs
fi

mpirun -np 6 simpleFoam -parallel &> simpleLogs/simpleFoam${Re}.log

 
# echo "    Running pisoeFoam"
# if [ ! -d pisoleLogs ]; then
#     mkdir pisoLogs
# fi
# # mpirun -np 6 pisoFoam -parallel &> pisoLogs/pisoFoam${Re}.log

# echo "    Running pimpleFoam"
# if [ ! -d pimpleLogs ]; then
    # mkdir pimpleLogs
# fi
# mpirun -np 6 pimpleFoam -parallel &> pimpleLogs/pimpleFoam${Re}.log 


check_return_code $?

echo "    Reconstructing"
reconstructPar -latestTime &> reconstructPar.log
check_return_code $?

echo "    Converting foam to VTK"
foamToVTK -latestTime -ascii  &> foamToVTK.log
check_return_code $?

echo "    Removing all processors' directories"
rm -r processor*
check_return_code $?

# echo "    Saving the fields for next run."
# if (( $(echo "$Re > 0.01" |bc -l) )); then
#     echo "    Mapping fields from previous case pimpleFoam"
#     mapFields -case /home/user/sharedVol/OF_Model -consistent -sourceTime 0  &> mapFields.log
# else
#     cd /home/user/sharedVol/OF_Model
#     mapFields -case /home/user/MGR/wd/OF_Model -consistent -sourceTime 0
# fi

