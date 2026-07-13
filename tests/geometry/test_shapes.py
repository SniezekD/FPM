import numpy as np
import pytest

import fpm.geometry.shapes as shapes


def test_sphere_properties():
    s = shapes.Sphere(position=[1, 2, 3], radius=0.5)
    assert s.type == "sphere"
    assert s.radius == 0.5
    assert list(s.position) == [1, 2, 3]


def test_sphere_mesh_volume_matches_analytic():
    s = shapes.Sphere(position=[0, 0, 0], radius=2.0)
    analytic = (4 / 3) * np.pi * 2.0 ** 3
    assert s.to_stl().volume == pytest.approx(analytic, rel=0.02)


def test_plane_properties_and_area():
    p = shapes.Plane(position=[0, 0, 0], size=[3, 0, 4])
    assert p.type == "plane"
    assert list(p.size) == [3, 0, 4]
    assert p.area == pytest.approx(12.0)   # width 3 * height 4