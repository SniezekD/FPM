def make_0_U(grains, file):
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
    inlet.stl
    {
        type            fixedValue;
        value uniform (1 0 0);
    }

    outlet.stl
    {
        type            zeroGradient;
    }

    wall_up.stl
    {
        type            noSlip;
    }

    wall_down.stl
    {
        type            noSlip;
    }

    cover_up.stl
    {
        type            empty;
    }   

    cover_down.stl
    {
        type            empty;
    }

    """)
    for grain in grains:
        file.write(f"{grain}")
        file.write("""
    {
        type            noSlip;
    }
    """)

    file.write("}")

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
    inlet.stl
    {
        type            fixedValue;
        value uniform   0;
    }

    outlet.stl
    {
        type            fixedValue;
        value uniform   0;
    }

    wall_up.stl
    {
        type            zeroGradient;
    }

    wall_down.stl
    {
        type            zeroGradient;
    }

    cover_up.stl
    {
        type            empty;
    }   

    cover_down.stl
    {
        type            empty;
    }

    """)
    for grain in grains:
        file.write(f"{grain}")
        file.write("""
    {
        type            zeroGradient;
    }
    """)
    file.write("}")
