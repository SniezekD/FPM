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
echo "    Running simpleFoam"
simpleFoam &> simpleFoam${Re}.log
check_return_code $?
