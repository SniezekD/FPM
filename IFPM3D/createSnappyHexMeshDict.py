def  createSnappyHexMeshDict(filePath):
    with open(filePath, "w") as file:
        text = """/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2006                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

castellatedMesh true;
snap            true;
addLayers       false;

geometry
{
    grains.stl
    {
        type triSurfaceMesh;
        name grains;
    }
    inlet.stl
    {
        type triSurfaceMesh;
        name inlet;
    }
    outlet.stl
    {
        type triSurfaceMesh;
        name outlet;
    }
    wall_up.stl
    {
        type triSurfaceMesh;
        name wall_up;
    }
    wall_down.stl
    {
        type triSurfaceMesh;
        name wall_down;
    }
    cover_up.stl
    {
        type triSurfaceMesh;
        name cover_up;
    }
    cover_down.stl
    {
        type triSurfaceMesh;
        name cover_down;
    }
}

castellatedMeshControls
{
    maxLocalCells 100000;
    maxGlobalCells 2000000;
    minRefinementCells 1;
    nCellsBetweenLevels 1;

    features
    (
    );

    refinementSurfaces
    {
        grains{ level (2 2); }
        cover_down{ level (2 2); }
        cover_up{ level (2 2); }
        wall_down{ level (2 2); }
        wall_up{ level (2 2); }
        inlet{ level (2 2); patchInfo { type patch; } }
        outlet{ level (2 2); patchInfo { type patch; } }
    }

    resolveFeatureAngle 30;
    refinementRegions { }
    locationInMesh (0.5 0.5 0.5); 
    allowFreeStandingZoneFaces true;
}

snapControls
{
    nSmoothPatch 3;
    tolerance 1.0;
    nSolveIter 300;
    nRelaxIter 5;
    nFeatureSnapIter 10;
    implicitFeatureSnap false;
    explicitFeatureSnap true;
    multiRegionFeatureSnap true;
}

addLayersControls
{
    relativeSizes true;
    layers
    {
    }
    expansionRatio 1.0;
    finalLayerThickness 0.3;
    minThickness 0.25;
    nGrow 0;
    featureAngle 30;
    nRelaxIter 5;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
    nRelaxedIter 20;
}

meshQualityControls
{
    #include "meshQualityDict"

    relaxed
    {
        maxNonOrtho 75;
    }
    nSmoothScale 4;
    errorReduction 0.75;
}


writeFlags
(
    scalarLevels    // write volScalarField with cellLevel for postprocessing
    layerSets       // write cellSets, faceSets of faces in layer
    layerFields     // write volScalarField for layer coverage
);

mergeTolerance 1E-6;


// ************************************************************************* //"""
        file.write(text)
