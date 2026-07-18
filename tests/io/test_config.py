import pathlib

import pytest

from fpm.io.config import CaseConfig, ConfigError
from fpm.io.config_reader import ConfigReader


def test_valid_config_parses(valid_config):
    cfg = CaseConfig.from_toml(valid_config)
    assert cfg.run.number_of_geometries == 2
    assert cfg.run.working_directory == pathlib.Path("./runs/test")
    assert cfg.run.results_directory == pathlib.Path("/results")
    assert cfg.run.porosities == (0.7, 0.6)
    assert cfg.run.velocities == (1e-9, 1e-6)

    assert cfg.parallelism.number_of_procs == 6
    assert cfg.parallelism.decompose_method == "scotch"

    assert cfg.control.end_time == 501
    assert cfg.control.time_step == 1
    assert cfg.control.write_interval == 50
    assert cfg.control.solver_name == "simpleFoam"

    assert cfg.medium.min_radius == 0.1
    assert cfg.medium.max_radius == 1.0
    assert cfg.medium.geometry_bounds_type == "non_periodic"

    assert cfg.medium.bounding_box.x_min == 0
    assert cfg.medium.bounding_box.x_max == 16
    assert cfg.medium.bounding_box.y_min == 0
    assert cfg.medium.bounding_box.y_max == 16
    assert cfg.medium.bounding_box.z_min == 0
    assert cfg.medium.bounding_box.z_max == 16

    assert cfg.fluid.fluid_kinematic_viscosity == 1e-6
    assert cfg.fluid.transport_model is None
    assert cfg.fluid.turbulence_model is None

    assert cfg.boundary.u["left_bc_type"] == "fixedValue"
    assert cfg.boundary.u["right_bc_type"] == "zeroGradient"
    assert cfg.boundary.u["up_bc_type"] == "noSlip"
    assert cfg.boundary.u["down_bc_type"] == "noSlip"
    assert cfg.boundary.u["front_bc_type"] == "noSlip"
    assert cfg.boundary.u["back_bc_type"] == "noSlip"
    assert cfg.boundary.u["obstacles_bc_type"] == "noSlip"

    assert cfg.boundary.p["left_bc_type"] == "zeroGradient"
    assert cfg.boundary.p["right_bc_type"] == "fixedValue"
    assert cfg.boundary.p["up_bc_type"] == "zeroGradient"
    assert cfg.boundary.p["down_bc_type"] == "zeroGradient"
    assert cfg.boundary.p["front_bc_type"] == "zeroGradient"
    assert cfg.boundary.p["back_bc_type"] == "zeroGradient"
    assert cfg.boundary.p["obstacles_bc_type"] == "zeroGradient"

    assert cfg.snappy.seed_location_in_mesh == (-0.5, 0.5, 0.5)
    assert cfg.snappy.max_local_cells == 2000000
    assert cfg.snappy.max_global_cells == 400000
    assert cfg.snappy.min_surface_refinement_lvl == 2
    assert cfg.snappy.max_surface_refinement_lvl == 3

    assert cfg.block_mesh.bounding_box.x_min == -20
    assert cfg.block_mesh.bounding_box.x_max == 46
    assert cfg.block_mesh.bounding_box.y_min == 0
    assert cfg.block_mesh.bounding_box.y_max == 16
    assert cfg.block_mesh.bounding_box.z_min == 0
    assert cfg.block_mesh.bounding_box.z_max == 16

    assert cfg.block_mesh.discretization.dx == 264
    assert cfg.block_mesh.discretization.dy == 64
    assert cfg.block_mesh.discretization.dz == 64

    assert cfg.block_mesh.boundary_types['obstacles'] == "wall"
    assert cfg.block_mesh.boundary_types['front'] == "wall"
    assert cfg.block_mesh.boundary_types['back'] == "wall"
    assert cfg.block_mesh.boundary_types['up'] == "wall"
    assert cfg.block_mesh.boundary_types['down'] == "wall"
    assert cfg.block_mesh.boundary_types['left'] == "patch"
    assert cfg.block_mesh.boundary_types['right'] == "patch"


@pytest.mark.parametrize(
    "find, replace, expected_message",
    [
        ("porosities = [0.7, 0.6]",     "porosities = [5.0]",          "open interval"),
        ('left_bc_type = "fixedValue"',
         'left_bc_type = "fixedvalue"',
         "unknown boundary type"),
        ("end_time = 501",              "",                            "wrong keys"),
        ("x_min = -20",                 "x_min = 999",                 "must be <"),
    ],
)
def test_bad_config_raises(tmp_path, valid_config, find, replace, expected_message):
    good_text = valid_config.read_text(encoding="utf-8")
    assert find in good_text
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text(good_text.replace(find, replace))
    with pytest.raises(ConfigError, match=expected_message):
        CaseConfig.from_toml(bad_config)


def test_unpack_maps_scalar_fields(valid_config):
    kwargs = ConfigReader(valid_config).unpack_foam_case_config()
    assert kwargs["working_directory"] == pathlib.Path("./runs/test")
    assert kwargs["end_time"] == 501
    assert kwargs["time_step"] == 1
    assert kwargs["solver_name"] == "simpleFoam"
    assert kwargs["write_interval"] == 50
    assert kwargs["number_of_procs"] == 6
    assert kwargs["max_local_cells"] == 2000000
    assert kwargs["max_global_cells"] == 400000
    assert kwargs["min_surface_refinement_lvl"] == 2
    assert kwargs["max_surface_refinement_lvl"] == 3
    assert kwargs["seed_location_in_mesh"] == (-0.5, 0.5, 0.5)
    assert kwargs["fluid_kinematic_viscosity"] == 1e-6
    assert kwargs["blockmesh_boundary_types"] == {
        "obstacles": "wall",
        "front": "wall",
        "back": "wall",
        "up": "wall",
        "down": "wall",
        "left": "patch",
        "right": "patch",
    }
    assert kwargs["u_boundary_types"] == {
        "left_bc_type": "fixedValue",
        "left_field_type": "value",
        "left_field_value": "uniform (0 0 0)",
        "right_bc_type": "zeroGradient",
        "right_field_type": None,
        "right_field_value": None,
        "up_bc_type": "noSlip",
        "up_field_type": None,
        "up_field_value": None,
        "down_bc_type": "noSlip",
        "down_field_type": None,
        "down_field_value": None,
        "front_bc_type": "noSlip",
        "front_field_type": None,
        "front_field_value": None,
        "back_bc_type": "noSlip",
        "back_field_type": None,
        "back_field_value": None,
        "obstacles_bc_type": "noSlip",
        "obstacles_field_type": None,
        "obstacles_field_value": None,
    }
    assert kwargs["p_boundary_types"] == {
        "left_bc_type": "zeroGradient",
        "left_field_type": None,
        "left_field_value": None,
        "right_bc_type": "fixedValue",
        "right_field_type": "value",
        "right_field_value": "uniform 0",
        "up_bc_type": "zeroGradient",
        "up_field_type": None,
        "up_field_value": None,
        "down_bc_type": "zeroGradient",
        "down_field_type": None,
        "down_field_value": None,
        "front_bc_type": "zeroGradient",
        "front_field_type": None,
        "front_field_value": None,
        "back_bc_type": "zeroGradient",
        "back_field_type": None,
        "back_field_value": None,
        "obstacles_bc_type": "zeroGradient",
        "obstacles_field_type": None,
        "obstacles_field_value": None,
    }
    assert kwargs["bounding_box_coords"] == {
        "x_min": -20,
        "x_max": 46,
        "y_min": 0,
        "y_max": 16,
        "z_min": 0,
        "z_max": 16,
    }
    assert kwargs["bounding_box_discretization"] == {
        "dx": 264,
        "dy": 64,
        "dz": 64
    }
    assert kwargs["turbulence_model"] is None
    assert kwargs["decompose_method"] == "scotch"
    assert kwargs["transport_model"] is None


def test_velocity_inlet_is_expanded(valid_config):
    u = ConfigReader(valid_config).unpack_foam_case_config()["u_boundary_types"]
    assert u["left_bc_type"] == "fixedValue"
    assert u["left_field_type"] == "value"
    assert u["left_field_value"] == "uniform (0 0 0)"


def test_velocity_wall_has_no_field_type_and_value(valid_config):
    u = ConfigReader(valid_config).unpack_foam_case_config()["u_boundary_types"]
    assert u["up_bc_type"] == "noSlip"
    assert u["up_field_type"] is None
    assert u["up_field_value"] is None


def test_pressure_outlet_is_expanded(valid_config):
    p = ConfigReader(valid_config).unpack_foam_case_config()["p_boundary_types"]
    assert p["right_bc_type"] == "fixedValue"
    assert p["right_field_type"] == "value"
    assert p["right_field_value"] == "uniform 0"


def test_pressure_wall_has_no_field_type_and_value(valid_config):
    p = ConfigReader(valid_config).unpack_foam_case_config()["p_boundary_types"]
    assert p["up_bc_type"] == "zeroGradient"
    assert p["up_field_type"] is None
    assert p["up_field_value"] is None


@pytest.mark.parametrize(
    "field, face, bc_type, field_type, field_value",
    [
        ("u_boundary_types", "left",  "fixedValue",   "value", "uniform (0 0 0)"),
        ("u_boundary_types", "right", "zeroGradient", None,    None),
        ("u_boundary_types", "up",    "noSlip",       None,    None),
        ("u_boundary_types", "down",    "noSlip",       None,    None),
        ("u_boundary_types", "front",    "noSlip",       None,    None),
        ("u_boundary_types", "back",    "noSlip",       None,    None),
        ("u_boundary_types", "obstacles",  "noSlip", None,    None),

        ("p_boundary_types", "left",  "zeroGradient", None,    None),
        ("p_boundary_types", "right", "fixedValue",   "value", "uniform 0"),
        ("p_boundary_types", "up",  "zeroGradient", None,    None),
        ("p_boundary_types", "down",  "zeroGradient", None,    None),
        ("p_boundary_types", "front",  "zeroGradient", None,    None),
        ("p_boundary_types", "back",  "zeroGradient", None,    None),
        ("p_boundary_types", "obstacles",  "zeroGradient", None,    None),
    ],
)
def test_boundary_expansion(
    valid_config,
    field,
    face,
    bc_type,
    field_type,
    field_value
):
    d = ConfigReader(valid_config).unpack_foam_case_config()[field]
    assert d[f"{face}_bc_type"] == bc_type
    assert d[f"{face}_field_type"] == field_type
    assert d[f"{face}_field_value"] == field_value
