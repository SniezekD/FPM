def make_0_U(grains, n, file, Re: float):
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

    cover_up
    {
        type            noSlip;
    }   

    cover_down
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

def make_0_p(grains, n, file):
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

    cover_up
    {
        type            zeroGradient;
    }

    cover_down
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
