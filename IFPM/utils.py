import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt
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

def standard_err(vector):
    return np.std(vector, ddof=1) / np.sqrt(np.size(vector))
 

def make_plot(number_of_geoms):
    re_vals = []
    Pi_vals = []
    GE_vals = []
    T_vals  = []
    for i in range(number_of_geoms):
        with open(f"results-{i}.dat") as file:
            tmp_Pi = []
            tmp_T  = []
            tmp_GE = []
            for line in file:
                try:
                    vals = line.split()
                  
                    if i == 0:
                        re_vals.append(float(vals[0]))

                    tmp_Pi.append(float(vals[1]))
                    tmp_GE.append(float(vals[3]))
                    tmp_T.append(float(vals[2]))
                except:
                    pass
            
            Pi_vals.append(tmp_Pi)
            GE_vals.append(tmp_GE)
            T_vals.append(tmp_T)

    re_vals = [np.log10(re) for re in re_vals]
    std_err_Pi = standard_err(Pi_vals)
    std_err_GE = standard_err(GE_vals)
    std_err_T  = standard_err(T_vals)

    Pi_vals = sum(np.array(Pi_vals))/number_of_geoms
    GE_vals = sum(np.array(GE_vals))/number_of_geoms
    T_vals  = sum(np.array(T_vals))/number_of_geoms

    plt.errorbar(re_vals, GE_vals, yerr=std_err_GE)
    plt.grid()
    plt.ylabel("Entropy")
    plt.xlabel("$\log_{10}{Re}$")
    plt.savefig('plots/GE-vs-log(Re).png')
    plt.cla()
    plt.clf()

    plt.errorbar(re_vals, T_vals, yerr=std_err_T)
    plt.grid()
    plt.ylabel("T")
    plt.xlabel("$\log_{10}{Re}$")
    plt.savefig('plots/T-vs-log(Re).png')
    plt.cla()
    plt.clf()

    plt.errorbar(re_vals, Pi_vals, yerr=std_err_Pi)
    plt.grid()
    plt.ylabel("$\pi$")
    plt.xlabel("$\log_{10}{Re}$")
    plt.ylim(0.35,0.55)
    plt.yticks(np.arange(0.35,0.56,0.05))
    plt.savefig('plots/PI-vs-log(Re).png')
    plt.cla()
    plt.clf()
    plt.errorbar(re_vals, Pi_vals/np.max(abs(Pi_vals)), yerr=std_err_Pi, label = "Pi")
    plt.errorbar(re_vals, T_vals/np.max(abs(T_vals)), yerr=std_err_T, label = "T")
    plt.errorbar(re_vals, -1*GE_vals/np.max(abs(GE_vals)), yerr=std_err_GE, label = "GE")
    plt.legend()
    plt.title("Normalized $\pi$, $T$ and $GE$")
    plt.savefig('plots/ALL-vs-log(Re).png')




#/-----------------------------------------------------------------------------\
#                               OF UTILITIES 
#\-----------------------------------------------------------------------------|

################################################################################
#                                                                              #
#                            CREATE BLOCK MESH DICT                            #
#                                                                              #
################################################################################
def  createBlockMeshDict(filePath, size, margin):
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
            (4 5 6 7)
        );
    }
    frontAndBack
    {
        type empty;
        faces
        (
            (0 1 5 4)
            (2 3 7 6)
        );
    }
);

mergePatchPairs
(
);

// ************************************************************************* //""")
        file.write(text.substitute(x = size['x']+2*margin, y = size['y'], z = size['z']))


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

    grains
    {
        type            noSlip;
    }

    """)
    # for grain in grains:
    #     file.write(f"grains_{grain}")
    #     file.write("""
    # {
    #     type            noSlip;
    # }
    # """)

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

    grains
    {
        type            zeroGradient;
    }

    """)
    # for grain in grains:
    #     file.write(f"grains_{grain}")
    #     file.write("""
    # {
    #     type            zeroGradient;
    # }
    # """)
    file.write("}")
    file.close()

