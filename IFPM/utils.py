import os
import sys
import subprocess
from pathlib import Path
from string import Template
import numpy as np
import matplotlib.pyplot as plt


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise TypeError('Boolean value expected.')


def run_cmd(args: list, shell: bool = False):
    status = subprocess.run(args, shell)
    if status.returncode == 0:
        print("     Done")
    else:
        print(f"     Error! \n{args} ended with code {status.returncode}.")
        sys.exit(status)


def run_cmd2(arg: str, shell: bool = False):
    status = subprocess.run(arg, shell)
    if status.returncode == 0:
        print("     Done")
    else:
        print(f"     Error! \n{arg} ended with code {status.returncode}.")
        sys.exit(status)


def standard_err(array):
    std_err_vec = []
    arr = np.array(array)
    for j in range(arr.shape[1]):
        vector = [arr[i, j] for i in range(arr.shape[0])]

        std_err_vec.append(np.std(vector, ddof=1) / np.sqrt(np.size(vector)))

    return std_err_vec


def make_plot(number_of_geoms):
    re_vals = []
    pi_vals = []
    DP_vals = []
    t_vals = []
    f_vals = []
    rep_vals = []
    uX_vals = []
    uMag_vals = []
    for i in range(number_of_geoms):
        with open(f"results-{i}.dat") as file:
            tmp_Pi = []
            tmp_T = []
            tmp_DP = []
            tmp_F = []
            tmp_rep = []
            tmp_uX_vals = []
            tmp_uMag_vals = []

            for line in file:
                try:
                    vals = line.split()

                    if i == 0:
                        re_vals.append(float(vals[0]))

                    tmp_Pi.append(float(vals[1]))
                    tmp_T.append(float(vals[2]))
                    tmp_DP.append(float(vals[3]))
                    tmp_F.append(float(vals[6]))
                    tmp_rep.append(float(vals[7]))
                    tmp_uX_vals.append(float(vals[4]))
                    tmp_uMag_vals.append(float(vals[5]))
                except ValueError:
                    pass

            pi_vals.append(tmp_Pi)
            DP_vals.append(tmp_DP)
            t_vals.append(tmp_T)
            f_vals.append(tmp_F)
            rep_vals.append(tmp_rep)
            uX_vals.append(tmp_uX_vals)
            uMag_vals.append(tmp_uMag_vals)

    re_vals = [np.log10(re) for re in re_vals]
    std_err_Pi = standard_err(pi_vals)
    std_err_DP = standard_err(DP_vals)
    std_err_T = standard_err(t_vals)
    std_err_F = standard_err(f_vals)
    std_err_rep = standard_err(rep_vals)
    std_err_uX = standard_err(uX_vals)
    std_err_uMag = standard_err(uMag_vals)

    pi_vals = sum(np.array(pi_vals)) / number_of_geoms
    DP_vals = sum(np.array(DP_vals)) / number_of_geoms
    t_vals = sum(np.array(t_vals)) / number_of_geoms
    f_vals = sum(np.array(f_vals)) / number_of_geoms
    rep_vals = sum(np.array(rep_vals)) / number_of_geoms
    uX_vals = sum(np.array(uX_vals)) / number_of_geoms
    uMag_vals = sum(np.array(uMag_vals)) / number_of_geoms

    outfile = open("AvgResults.dat", "w")
    outfile.write(("log_10(Re)\tpi\tstd_pi\tT\tstd_T\tDP\tstd_DP\tFriciton\t"
                   "std_Friction\tre'\tstd_re'\tU_x_std_Ux\tU_mag\tstd_uMag\n"))
    for re, Pi, std_Pi, DP, std_DP, T, std_T, F, std_F, rep, std_rep, \
        u_x, std_ux, u_mag, std_umag in zip(
            re_vals,
            pi_vals,
            std_err_Pi,
            t_vals,
            std_err_T,
            DP_vals,
            std_err_DP,
            f_vals,
            std_err_F,
            rep_vals,
            std_err_rep,
            uX_vals,
            std_err_uX,
            uMag_vals,
            std_err_uMag
            ):
        outfile.write((f"{re}\t{Pi}\t{std_Pi}\t{DP}\t{std_DP}\t{T}"
                       f"\t{std_T}\t{F}\t{std_F}\t{rep}\t{std_rep}"
                       f"\t{u_x}\t{std_ux}\t{u_mag}\t{std_umag}\n"))

    outfile.close()


def read_data_from_file(path: Path):
    x_arr = []
    data_arr = []
    with open(path, "r") as file:
        for line in file:
            data = line.split()
            try:
                x_arr.append(float(data[0]))
                data_arr.append(np.array(data[1:], dtype=float))
            except ValueError:
                pass

    return x_arr, data_arr

def plot_residuals(collective_path: Path, savename: str = None) -> None:
    plt.rcParams.update({'font.size': 22})
    of_dirs = os.listdir(collective_path)
    of_dirs = [ofdir for ofdir in of_dirs if "OF_Model" in ofdir]
    of_dirs = sorted(of_dirs, key=lambda x: float(x.split('_')[-1]))
    number_of_plots = len(of_dirs)
    if number_of_plots % 4 != 0:
        col_number = 2
        row_number = int(np.ceil(number_of_plots/col_number))
        figsize = (col_number*10, row_number*5)
    else:
        col_number = 4
        row_number = int(np.ceil(number_of_plots/col_number))
        figsize = (col_number*5, row_number*5)
    fig, ax = plt.subplots(
        row_number,
        col_number,
        figsize=figsize,
    )
    fig.tight_layout(pad=3.0)
    labels = ["U${_x}$", "U${_y}$", "U${_z}$", "p"]

    # fig.tight_layout(pad=2.0,h_pad=4.0)
    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]

    for i, ofdir in enumerate(of_dirs):
        Ux_path = collective_path.joinpath(ofdir, 'logs', 'Ux_0')
        Uy_path = collective_path.joinpath(ofdir, 'logs', 'Uy_0')
        if "Uz_0" in os.listdir(collective_path.joinpath(ofdir, 'logs')):
            Uz_path = collective_path.joinpath(ofdir, 'logs', 'Uz_0')
        else:
            Uz_path = None
        p_path = collective_path.joinpath(ofdir, 'logs', 'p_0')
        Re = float(ofdir.split('_')[-1])
        print(Ux_path)
        iters, Ux_data = read_data_from_file(Ux_path)
        _, Uy_data = read_data_from_file(Uy_path)
        if Uz_path is not None:
            _, Uz_data = read_data_from_file(Uz_path)
        _, p_data = read_data_from_file(p_path)

        Ux = [u[0] for u in Ux_data]
        Uy = [u[0] for u in Uy_data]
        if Uz_path is not None:
            Uz = [u[0] for u in Uz_data]
        p = [p[0] for p in p_data]

        ax[int(i / col_number), int(i % col_number)].plot(
            iters,
            Ux,
            label="U${_x}$",
            color="red",
            linewidth=4.0
        )
        ax[int(i / col_number), int(i % col_number)].plot(
            iters,
            Uy,
            label="U${_y}$",
            color="blue",
            linewidth=4.0
        )
        if Uz_path is not None:
            ax[int(i / col_number), int(i % col_number)].plot(
                iters,
                Uz,
                color="green",
                label="U${_z}$",
                linewidth=4.0
            )
        ax[int(i / col_number), int(i % col_number)].plot(
            iters,
            p,
            label="p",
            color="gray",
            linewidth=4.0
        )
        ax[int(i / col_number), int(i % col_number)].set_title(
            f"Re={Re:0.4f}"
        )
        ax[int(i / col_number), int(i % col_number)].set_yscale('log')

        tmp_ax = ax[int(i / col_number), int(i % col_number)]
        handles, labels = tmp_ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.015),
        ncols=4,
        columnspacing=5.0,
        labelspacing=5.0,
        fontsize=32,
        fancybox=True,
        frameon=True
    )
    if savename is not None:
        plt.savefig(f'{savename}.png',bbox_inches='tight')
    else:
        plt.show()


# /-------------------------------------------------------------------\
#                                OF UTILITIES
# \-------------------------------------------------------------------/

#######################################################################
#                                                                     #
#                            CREATE BLOCK MESH DICT                   #
#                                                                     #
#######################################################################
def  createBlockMeshDict(filePath, size, in_margin, out_margin):
    if size['z'] == 1:
        front_back_type = 'empty'
    else:
        front_back_type = 'wall'
    with open(filePath, "w") as file:
        text = Template(
"""
/*--------------------------------*- C++ -*----------------------------------*\\
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
    hex (0 1 2 3 4 5 6 7) ($xd $yd $zd) simpleGrading (1 1 1)
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
        file.write(
            text.substitute(
                x=size['x'] + in_margin + out_margin,
                y=size['y'],
                z=size['z'],
                xd=2 * (size['x'] + in_margin + out_margin),
                yd=2 * size['y'],
                zd=2 * size['z'],
                fab_type=front_back_type
            )
        )


########################################################################
#                                                                      #
#                          CREATE SNAPPY HEX MESH DICT                 #
#                                                                      #
########################################################################
def createMeshDict(filePath):
    with open(filePath, "w") as file:
        text = \
"""
/*--------------------------------*- C++ -*----------------------------------*\\
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

minCellSize 0.25;

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


########################################################################
#                                                                      #
#                      CREATE SNAPPY HEX MESH DICT                     #
#                                                                      #
########################################################################
def createSnappyHexMeshDict(filePath):
    with open(filePath, "w") as file:
        text = \
"""
/*--------------------------------*- C++ -*----------------------------------*\\
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


// ************************************************************************* //
"""
        file.write(text)


########################################################################
#                                                                      #
#                    INITIAL CONDITIONS FOR VELOCITY                   #
#                                                                      #
########################################################################
def make_0_U(filePath, size, Re: float):
    if size['z'] == 1:
        front_back_type = 'empty'
    else:
        front_back_type = 'noSlip'
    velocity = Re*1e-6
    with open(filePath, "w") as file:
        text = Template(
"""
/*--------------------------------*- C++ -*----------------------------------*\\
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
    class       volVectorField;
    object      U;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0 0 0);

boundaryField
{
    inlet.stl
    {
        type            fixedValue;
        value uniform   ($v 0 0);
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
        file.write(
            text.substitute(
                v=velocity,
                fab_type=front_back_type
            )
        )


########################################################################
#                                                                      #
#                    INITIAL CONDITIONS FOR PRESSURE                   #
#                                                                      #
########################################################################
def make_0_p(filePath, size):
    if size['z'] == 1:
        front_back_type = 'empty'
    else:
        front_back_type = 'zeroGradient'

    with open(filePath, "w") as file:
        text = Template(
"""
/*--------------------------------*- C++ -*----------------------------------*\\
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
    class       volScalarField;
    object      p;
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

        file.write(text.substitute(fab_type=front_back_type))
