import pandas as pd
import pytest

from fpm.media_models.swiss_cheese import SwissCheese

BOUNDS = {"x_min": 0, "x_max": 4, "y_min": 0, "y_max": 4, "z_min": 0, "z_max": 4}


def make_medium(**overrides):
    """Factory for a SwissCheese under test; override one field per test."""
    kwargs = dict(porosity=0.9, bounds=BOUNDS, min_radius=0.3,
                  max_radius=0.5, geometry_bounds_type="non_periodic")
    kwargs.update(overrides)
    return SwissCheese(**kwargs)


def test_rejects_invalid_geometry_bounds_type():
    with pytest.raises(ValueError):
        make_medium(geometry_bounds_type="banana")


def test_create_boundary_walls_returns_six_walls():
    walls = make_medium().create_boundary_walls()
    assert set(walls) == {
        "porous_medium_wall_up",
        "porous_medium_wall_down",
        "porous_medium_wall_right",
        "porous_medium_wall_left",
        "porous_medium_wall_front",
        "porous_medium_wall_back",
    }


def test_save_spec_writes_readable_csv(tmp_path):
    spec = tmp_path / "spec.csv"
    make_medium().save_spec_to_file(spec)
    assert spec.exists()
    df = pd.read_csv(spec)
    assert df["porosity"][0] == 0.9
    assert df["geometry_bounds_type"][0] == "non_periodic"


def test_save_stls_writes_wall_files(tmp_path):
    pm = make_medium()
    pm.walls = pm.create_boundary_walls()
    pm.save_stls(tmp_path)
    stl_files = sorted(p.name for p in tmp_path.glob("*.stl"))
    assert len(stl_files) == 6