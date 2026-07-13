import numpy as np
import pytest

import fpm.geometry.shapes as shapes
from fpm.media_models.swiss_cheese import SwissCheese

from fpm.utilities.calculate_porosity import (
    calculate_porosity,
    map_coordinate_to_index,
    map_index_to_coordinate,
    map_index_difference_to_distance,
)


def test_coordinate_to_index_known_value():
    discretization = (10, 10, 10)
    bounds = {
        "x_min": 0,
        "x_max": 10,
        "y_min": 0,
        "y_max": 10,
        "z_min": 0,
        "z_max": 10
    }   # cell size = 1
    assert map_coordinate_to_index(3.5, 7.2, 0.0, discretization, bounds) == (3, 7, 0)


def test_index_zero_maps_to_box_origin():
    discretization = (66, 16, 16)
    bounds = {
        "x_min": -20,
        "x_max": 46,
        "y_min": 0,
        "y_max": 10,
        "z_min": 0,
        "z_max": 10
    }
    # index (0,0,0) is the box's lower corner -> the box minimum, i.e. x_min = -20
    assert map_index_to_coordinate(0, 0, 0, discretization, bounds) == (-20, 0, 0)


@pytest.mark.parametrize("bounds", [
    # zero origin
    {"x_min": 0, "x_max": 10, "y_min": 0, "y_max": 10, "z_min": 0, "z_max": 10},
    # nonzero origin
    {"x_min": -20, "x_max": 46, "y_min": 0, "y_max": 16, "z_min": 0, "z_max": 16},
])
def test_index_coordinate_roundtrip(bounds):
    discretization = (
        int(bounds["x_max"] - bounds["x_min"]),
        int(bounds["y_max"] - bounds["y_min"]),
        int(bounds["z_max"] - bounds["z_min"]),
    )
    x, y, z = map_index_to_coordinate(5, 3, 3, discretization, bounds)
    assert map_coordinate_to_index(x, y, z, discretization, bounds) == (5, 3, 3)


def test_index_difference_to_distance_known_value():
    discretization = (10, 10, 10)
    bounds = {
        "x_min": 0,
        "x_max": 10,
        "y_min": 0,
        "y_max": 10,
        "z_min": 0,
        "z_max": 10
    }   # cell size = 1
    assert map_index_difference_to_distance(3, 4, 0, discretization, bounds) == 5.0


UNIT_BOX = {"x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1, "z_min": 0, "z_max": 1}


def unit_medium():
    return SwissCheese(porosity=0.9, bounds=UNIT_BOX, min_radius=0.1,
                       max_radius=0.1, geometry_bounds_type="non_periodic")


def test_porosity_of_empty_medium_is_one():
    pm = unit_medium()  # constructor leaves obstacles = None
    porosity, _ = calculate_porosity(pm)
    assert porosity == 1.0


@pytest.mark.parametrize("radius", [
    0.01,
    0.1,
    0.2,
    0.35,
    0.5,
])
def test_porosity_of_single_sphere_matches_analytic(radius):
    pm = unit_medium()
    sphere = shapes.Sphere(position=[0.5, 0.5, 0.5], radius=radius)
    expected = 1 - (4 / 3) * np.pi * radius ** 3       # void fraction in a unit box
    porosity, _ = calculate_porosity(
        pm,
        obstacles=[sphere],
        discretization=(200, 200, 200)
    )
    assert porosity == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("discretization, accuracy", [
   ((10, 10, 10), 0.200),
   ((40, 40, 40), 0.050),
   ((80, 80, 80), 0.025),
   ((100, 100, 100), 0.0200),
   ((150, 150, 150), 0.0150),
   ((200, 200, 200), 0.01),
   ((400, 400, 400), 0.005),
])
def test_finer_discretization_increases_accuracy(discretization, accuracy):
    pm = unit_medium()
    radius = 0.5
    sphere = shapes.Sphere(position=[0.5, 0.5, 0.5], radius=radius)
    expected = 1 - (4 / 3) * np.pi * radius ** 3       # void fraction in a unit box
    porosity, _ = calculate_porosity(
        pm,
        obstacles=[sphere],
        discretization=discretization
    )
    assert porosity == pytest.approx(expected, abs=accuracy)
