import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from string import Template
from pathlib import Path

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
    plt.savefig('plots/PI-vs-log(Re).png')
    plt.cla()
    plt.clf()

    plt.errorbar(re_vals, Pi_vals/np.max(abs(Pi_vals)), yerr=std_err_Pi, label = "$\pi$")
    plt.errorbar(re_vals, T_vals/np.max(abs(T_vals)), yerr=std_err_T, label = "T")
    plt.errorbar(re_vals, GE_vals/np.max(abs(GE_vals)), yerr=std_err_GE, label = "GE")
    plt.xlabel("$\log_{10}{Re}$")
    plt.legend()
    plt.grid()
    plt.title("Normalized $\pi$, $T$ and $GE$")
    plt.savefig('plots/ALL-vs-log(Re).png')
    plt.cla()
    plt.clf()

def read_data_from_file(path:Path):
    x_arr = []
    data_arr = []
    with open(path, "r") as file:
        for line in file:
            data = line.split()
            try:
                x_arr.append(float(data[0]))
                data_arr.append(np.array(data[1:], dtype=float))
            except:
                pass
    
    return x_arr, data_arr

def plot_residuals(re_list:list, path:Path, savename:str=None) -> None:
    row_number = int(np.ceil(len(re_list)/5))
    col_number = 5
    fig, ax = plt.subplots(row_number, col_number, figsize=(20, 35))
    fig.tight_layout(pad=3.0)

    for i, Re in enumerate(re_list):
        Ux_path = path.joinpath(f'OF_Model_{Re:0.4f}', 'logs', 'Ux_0')
        Uy_path = path.joinpath(f'OF_Model_{Re:0.4f}', 'logs', 'Uy_0')
        Uz_path = path.joinpath(f'OF_Model_{Re:0.4f}', 'logs', 'Uz_0')
        p_path  = path.joinpath(f'OF_Model_{Re:0.4f}', 'logs', 'p_0')

        iters, Ux_data = read_data_from_file(Ux_path)
        _    , Uy_data = read_data_from_file(Uy_path)
        _    , Uz_data = read_data_from_file(Uz_path)
        _    , p_data  = read_data_from_file(p_path)

        Ux = [u[0] for u in Ux_data]
        Uy = [u[0] for u in Uy_data]
        Uz = [u[0] for u in Uz_data]
        p  = [p[0] for p in p_data]

        ax[int(i/col_number), int(i%col_number)].plot(iters, Ux, label = "Ux_0")
        ax[int(i/col_number), int(i%col_number)].plot(iters, Uy, label = "Uy_0")
        ax[int(i/col_number), int(i%col_number)].plot(iters, Uz, label = "Uz_0")
        ax[int(i/col_number), int(i%col_number)].plot(iters, p, label = "p_0")
        ax[int(i/col_number), int(i%col_number)].set_title(
            f"Residuals\nRe={Re:0.4f}"
        )
        ax[int(i/col_number), int(i%col_number)].set_yscale('log')
        ax[int(i/col_number), int(i%col_number)].legend()

    if savename is not None:
        plt.savefig(f'{savename}.png')
    else:
        plt.show()




#/-----------------------------------------------------------------------------\
#                               OF UTILITIES 
#\-----------------------------------------------------------------------------|

################################################################################
#                                                                              #
#                            CREATE BLOCK MESH DICT                            #
#                                                                              #
################################################################################
def  createBlockMeshDict(filePath, size, margin):
    if size['z'] == 1:
        front_back_type = 'empty'
    else:
        front_back_type = 'wall'
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
   inlet.stl
    {
        type patch;
        faces
        (
            (0 3 7 4)
        );
    }
    outlet.stl
    {
        type patch;
        faces
        (
            (1 5 6 2)
        );
    }
    walls.stl
    {
        type wall;
        faces
        (
            (0 1 2 3)
            (4 5 6 7)
        );
    }
    frontAndBack.stl
    {
        type $fab_type;
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

// ************************************************************************* //
""")
        file.write(text.substitute(x = size['x']+2*margin, y = size['y'], z = size['z'], fab_type = front_back_type))

################################################################################
#                                                                              #
#                          CREATE SNAPPY HEX MESH DICT                         #
#                                                                              #
################################################################################
def createMeshDict(filePath):
 with open(filePath, "w") as file:
        text = """/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                |
| \\      /  F ield         | cfMesh: A library for mesh generation          |
|  \\    /   O peration     |                                                |
|   \\  /    A nd           | Author: Franjo Juretic                         |
|    \\/     M anipulation  | E-mail: franjo.juretic@c-fields.com            |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version   2.0;
    format    ascii;
    class     dictionary;
    location  "system";
    object    meshDict;
}

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

surfaceFile "constant/triSurface/col_model.fms";

/* minCellSize 0.2; */

maxCellSize 0.25;

/* boundaryCellSize 0.1; */

/* boundaryCellSizeRefinementThickness 1; */

localRefinement
{
    "grains.stl"
    {
        additionalRefinementLevel 2;
        refinementThickness 0.25;
    }
}


// ************************************************************************* //
"""
        file.write(text)
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
        name grains.stl;
    }
    inlet.stl
    {
        type triSurfaceMesh;
        name inlet.stl;
    }
    outlet.stl
    {
        type triSurfaceMesh;
        name outlet.stl;
    }
    wall_up.stl
    {
        type triSurfaceMesh;
        name wall_up.stl;
    }
    wall_down.stl
    {
        type triSurfaceMesh;
        name wall_down.stl;
    }
    wall_front.stl
    {
        type triSurfaceMesh;
        name wall_front.stl;
    }
    wall_back.stl
    {
        type triSurfaceMesh;
        name wall_back.stl;
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
        grains.stl{ level (2 2); }
        wall_front.stl{ level (2 2); }
        wall_back.stl{ level (2 2); }
        wall_down.stl{ level (2 2); }
        wall_up.stl{ level (2 2); }
        inlet.stl{ level (2 2); patchInfo { type patch; } }
        outlet.stl{ level (2 2); patchInfo { type patch; } }
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
def make_0_U(filePath, size, Re: float):
    if size['z'] == 1:
        front_back_type = 'empty'
    else:
        front_back_type = 'noSlip'
    velocity = Re*1e-6
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

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
    inlet.stl
    {
        type            groovyBC;
        value           uniform ($v 0 0);
        valueExpression "vector($v,0,0)";    
    }

    outlet.stl
    {
        type            zeroGradient;
    }

    walls.stl
    {
        type            noSlip;
    }

    wall_up.stl
    {
        type            noSlip;
    }

    wall_down.stl
    {
        type            noSlip;
    }

    wall_front.stl
    {
        type            $fab_type;
    }   

    wall_back.stl
    {
        type            $fab_type;
    }   

    grains.stl
    {
        type            noSlip;
    }
}
""")
        file.write(text.substitute(v = velocity, fab_type = front_back_type))

################################################################################
#                                                                              #
#                        INITIAL CONDITIONS FOR PRESSURE                       #
#                                                                              #
################################################################################
def make_0_p(filePath, size):
    if size['z'] == 1:
        front_back_type = 'empty'
    else:
        front_back_type = 'zeroGradient'

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

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    inlet.stl
    {
        type            zeroGradient;
    }

    outlet.stl
    {
        type            fixedValue;
        value uniform   0;
    }

    walls.stl
    {
        type            zeroGradient;
    }

    wall_up.stl
    {
        type            zeroGradient;
    }

    wall_down.stl
    {
        type            zeroGradient;
    }

    wall_front.stl
    {
        type            $fab_type;
    }

    wall_back.stl
    {
        type            $fab_type;
    }

    grains.stl
    {
        type            zeroGradient;
    }
}
    """)

        file.write(text.substitute(fab_type = front_back_type))
