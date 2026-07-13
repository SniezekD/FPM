import pathlib

import pytest

from fpm.io.config import CaseConfig, ConfigError


def test_valid_config_parses(valid_config):
    cfg = CaseConfig.from_toml(valid_config)
    assert cfg.run.number_of_geometries == 2
    assert cfg.run.working_directory == pathlib.Path("./runs/test")
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
        ('left_bc_type = "fixedValue"', 'left_bc_type = "fixedvalue"', "unknown boundary type"),
        ("end_time = 501",              "",                            "wrong keys"),
        ("x_min = -20",                 "x_min = 999",                 "must be <"),
    ],
)
def test_bad_config_raises(tmp_path, valid_config, find, replace, expected_message):
    good_text = valid_config.read_text()
    assert find in good_text
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text(good_text.replace(find, replace))
    with pytest.raises(ConfigError, match=expected_message):
        CaseConfig.from_toml(bad_config)