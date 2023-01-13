#!/bin/bash

rm -r ../OF_Model/constant/triSurface/*
rm -r ../OF_Model/0/*
mkdir ../OF_Model/constant/triSurface/grains
mv grains.stl ../OF_Model/constant/triSurface
mv grain* ../OF_Model/constant/triSurface/grains
mv *.stl ../OF_Model/constant/triSurface

touch ../OF_Model/0/p
touch ../OF_Model/0/U
