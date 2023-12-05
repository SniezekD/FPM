#!/bin/bash

Re=$1
source /usr/lib/openfoam/openfoam2006/etc/bashrc

cd ../wd/OF_Model 

foamLog -quiet simpleLogs/simpleFoam${Re}.log 
# foamLog -quiet pisoLogs/pisoFoam${Re}.log 
