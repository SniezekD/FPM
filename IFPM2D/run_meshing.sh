#!/bin/bash

#convert stl to fms:
source /usr/lib/openfoam/openfoam2006/etc/bashrc
echo "    Converting stl to fms"
surfaceFeatureEdges ../OF_Model/constant/triSurface/col_model.stl ../OF_Model/constant/triSurface/col_model.fms &> convertToFMS.log
echo "     Done"
echo "    Defining boundaty types in fms"
sed -i s/empty/wall/g ../OF_Model/constant/triSurface/col_model.fms
sed -i '/.*inlet.stl.*/c\inlet.stl patch' ../OF_Model/constant/triSurface/col_model.fms
sed -i '/.*outlet.stl.*/c\outlet.stl patch' ../OF_Model/constant/triSurface/col_model.fms
echo "     Done"

cd ../OF_Model 
echo "    Creating the mesh with cfMesh"
cartesian2DMesh &> cartesian2DMesh.log