import pytest

from fpm.io.config_reader import ConfigReader
from fpm.openfoam_case import OpenFoamCase


@pytest.fixture
def foam_case(valid_config, tmp_path):
    kwargs = ConfigReader(valid_config).unpack_foam_case_config()
    kwargs["working_direcory"] = tmp_path
    return OpenFoamCase(**kwargs)


@pytest.mark.parametrize("subdir, filename", [
        ("0", "U"),
        ("0", "p"),
        ("system", "blockMeshDict"),
        ("system", "snappyHexMeshDict"),
        ("system", "meshQualityDict"),
        ("system", "controlDict"),
        ("system", "fvSchemes"),
        ("system", "fvSolution"),
        ("system", "decomposeParDict"),
        ("constant", "turbulenceProperties"),
        ("constant", "transportProperties"),
    ]
)
def test_create_of_dir_writes_case_files(foam_case, tmp_path, subdir, filename):
    foam_case.create_of_dir()
    of = tmp_path / "OF_case"
    assert (of / subdir / filename).exists()


def test_velocity_is_rendered(foam_case, tmp_path):
    foam_case.create_of_dir()
    u = (tmp_path / "OF_case" / "0" / "U").read_text()
    assert ("""wall_left
    {
        type            fixedValue;
        value   uniform (0 0 0);
    }

    wall_right
    {
        type            zeroGradient;
        None   None;
    }

    wall_up
    {
        type            noSlip;
        None   None;
    }

    wall_down
    {
        type            noSlip;
        None   None;
    }

    wall_front
    {
        type            noSlip;
        None   None;
    }

    wall_back
    {
        type            noSlip;
        None   None;
    }

    obstacles
    {
        type            noSlip;
        None   None;
    }""") in u


def test_pressure_is_rendered(foam_case, tmp_path):
    foam_case.create_of_dir()
    p = (tmp_path / "OF_case" / "0" / "p").read_text()
    assert ("""wall_left
    {
        type            zeroGradient;
        None   None;
    }

    wall_right
    {
        type            fixedValue;
        value   uniform 0;
    }

    wall_up
    {
        type            zeroGradient;
        None   None;
    }

    wall_down
    {
        type            zeroGradient;
        None   None;
    }

    wall_front
    {
        type            zeroGradient;
        None   None;
    }

    wall_back
    {
        type            zeroGradient;
        None   None;
    }

    obstacles
    {
        type            zeroGradient;
        None   None;
    }""") in p


def test_change_velocity_rewrites_u_file(foam_case, tmp_path):
    foam_case.create_of_dir()
    new_u = foam_case.u_boundary_types
    new_u["left_field_value"] = "uniform (0.5 0 0)"
    foam_case.change_velocity_boundary_types(new_u)
    u = (tmp_path / "OF_case" / "0" / "U").read_text()
    assert "uniform (0.5 0 0)" in u


def test_streamwise_axis_is_determined(foam_case):
    assert foam_case.streamwise_axis == "x"


def test_calculate_inlet_area(foam_case):
    assert foam_case.inlet_area == 16 * 16
