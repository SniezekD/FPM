#!/bin/bash
rm -r ../wd/OF_Model/constant/triSurface/*
rm -r ../wd/OF_Model/0/*

mkdir -p ../wd/OF_Model/constant/triSurface/grains
mv grain_* ../wd/OF_Model/constant/triSurface/grains
mv grains.stl ../wd/OF_Model/constant/triSurface
mv *.stl ../wd/OF_Model/constant/triSurface

touch ../wd/OF_Model/0/p
touch ../wd/OF_Model/0/U
