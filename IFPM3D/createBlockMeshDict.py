from string import Template

def  createBlockMeshDict(filePath, nl:int, ml:int):
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
    (0 0 0)
    ($nlml 0 0)
    ($nlml $nl 0)
    (0 $nl 0)
    (0 0 $nl)
    ($nlml 0 $nl)
    ($nlml $nl $nl)
    (0 $nl $nl)
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ($nlml $nl $nl) simpleGrading (1 1 1)
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
        file.write(text.substitute(nl=nl, nlml=nl+2*ml))

