import sys
import subprocess
from string import Template

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise TypeError('Boolean value expected.')

def run_cmd(args: list, shell: bool = False) -> float:
    status = subprocess.run(args, shell)
    if status.returncode == 0:
        print("     Done")
    else:
        print(f"     Error! \n{args} ended with code {status.returncode}.")
        sys.exit(status)

def run_cmd2(arg: str, shell: bool = False) -> float:
    status = subprocess.run(arg, shell)
    if status.returncode == 0:
        print("     Done")
    else:
        print(f"     Error! \n{arg} ended with code {status.returncode}.")
        sys.exit(status)



#/-----------------------------------------------------------------------------\
#                               OF UTILITIES 
#\-----------------------------------------------------------------------------|

################################################################################
#                                                                              #
#                            CREATE BLOCK MESH DICT                            #
#                                                                              #
################################################################################
def  createBlockMeshDict(filePath, size):
    with open(filePath, "w") as file:
        text = Template("""/*--------------------------------*- C++ -*----------------------------------*\\
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
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
scale   1;

vertices
(
    (0  0  0)
    ($x 0  0)
    ($x $y 0)
    (0  $y 0)
    (0  0  $z)
    ($x 0  $z)
    ($x $y $z)
    (0  $y $z)
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ($x $y $z) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
   inlet
    {
        type patch;
        faces
        (
            (0 3 7 4)
        );
    }
    outlet
    {
        type patch;
        faces
        (
            (1 5 6 2)
        );
    }
    walls
    {
        type wall;
        faces
        (
            (0 1 2 3)
            (0 1 5 4)
            (2 3 7 6)
            (4 5 6 7)
        );
    }
);

mergePatchPairs
(
);

// ************************************************************************* //""")
        file.write(text.substitute(x = size['x'], y = size['y'], z = size['z']))


################################################################################
#                                                                              #
#                          CREATE SNAPPY HEX MESH DICT                         #
#                                                                              #
################################################################################
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
    wall_front.stl
    {
        type triSurfaceMesh;
        name wall_front;
    }
    wall_back.stl
    {
        type triSurfaceMesh;
        name wall_back;
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
        wall_front{ level (2 2); }
        wall_back{ level (2 2); }
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

################################################################################
#                                                                              #
#                        INITIAL CONDITIONS FOR VELOCITY                       #
#                                                                              #
################################################################################
def make_0_U(grains, file, Re: float):
    v = Re*1e-6
    # valExp = f"vector(pos().x/{n}*(pos().x/{n} - 1)*pos().y/{n}*(pos().y/{n} - 1),0,0)"
    valExp = f"vector({v},0,0)"
    file.write("""FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
    inlet
    {
        type            groovyBC;
        value           uniform (""")
    file.write(f"{v}")
    file.write(""" 0 0);
        valueExpression \" """)
    file.write(f"{valExp}\";")
    file.write(
    """}

    outlet
    {
        type            zeroGradient;
    }

    walls
    {
        type            noSlip;
    }

    wall_up
    {
        type            noSlip;
    }

    wall_down
    {
        type            noSlip;
    }

    wall_front
    {
        type            noSlip;
    }   

    wall_back
    {
        type            noSlip;
    }

    """)
    for grain in grains:
        file.write(f"grains_{grain}")
        file.write("""
    {
        type            noSlip;
    }
    """)

    file.write("}")
    file.close()

################################################################################
#                                                                              #
#                        INITIAL CONDITIONS FOR PRESSURE                       #
#                                                                              #
################################################################################
def make_0_p(grains, file):
    file.write("""FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    inlet
    {
        type            zeroGradient;
    }

    outlet
    {
        type            fixedValue;
        value uniform   0;
    }

    walls
    {
        type            zeroGradient;
    }

    wall_up
    {
        type            zeroGradient;
    }

    wall_down
    {
        type            zeroGradient;
    }

    wall_front
    {
        type            zeroGradient;
    }

    wall_back
    {
        type            zeroGradient;
    }

    """)
    for grain in grains:
        file.write(f"grains_{grain}")
        file.write("""
    {
        type            zeroGradient;
    }
    """)
    file.write("}")
    file.close()

