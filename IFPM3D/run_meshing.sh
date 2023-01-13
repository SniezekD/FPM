#!/bin/bash

source /usr/lib/openfoam/openfoam2006/etc/bashrc

cd ../OF_Model 
echo "    Creating boundary mesh with blockMesh"
blockMesh &> blockMesh.log
echo "     Done"

echo "    Decomposing the mesh into 6 domains"
decomposePar -force &> decomposeParMesh.log
echo "     Done"

echo "    Creating the mesh with snappyHexMesh"
mpirun -np 6 snappyHexMesh -parallel -overwrite &> snappyHexMesh.log
echo "     Done"

echo "    Reconstructing the mesh into 1 domain"
reconstructParMesh -mergeTol 1e-06 -constant &> reconstructParMesh.log
echo "     Done"

echo "    Checking the mesh"
checkMesh &> checkMesh.log
echo "     Done"
