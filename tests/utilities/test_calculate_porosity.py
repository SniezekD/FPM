import pytest

from fpm.utilities.calculate_porosity import (
    map_coordinate_to_index,
    map_index_to_coordinate,
    map_index_difference_to_distance,
)


def test_coordinate_to_index_known_value():
    discretization, bounds = (10, 10, 10), (0, 10, 0, 10, 0, 10)   # cell size = 1
    assert map_coordinate_to_index(3.5, 7.2, 0.0, discretization, bounds) == (3, 7, 0)


def test_index_zero_maps_to_box_origin():
    discretization, bounds = (66, 16, 16), (-20, 46, 0, 16, 0, 16)
    # index (0,0,0) is the box's lower corner -> the box minimum, i.e. x_min = -20
    assert map_index_to_coordinate(0, 0, 0, discretization, bounds) == (-20, 0, 0)


@pytest.mark.parametrize("bounds", [
    # (0, 10, 0, 10, 0, 10),        # zero origin
    (-20, 46, 0, 16, 0, 16),      # nonzero origin
])
def test_index_coordinate_roundtrip(bounds):
    discretization = (int(bounds[1] - bounds[0]), int(bounds[3] - bounds[2]), int(bounds[5] - bounds[4]))
    x, y, z = map_index_to_coordinate(5, 3, 3, discretization, bounds)
    assert x == -15
    assert y == 3
    assert z == 3
    assert map_coordinate_to_index(x, y, z, discretization, bounds) == (5, 3, 3)


def test_index_difference_to_distance_known_value():
    discretization, bounds = (10, 10, 10), (0, 10, 0, 10, 0, 10)   # cell size = 1
    assert map_index_difference_to_distance(3, 4, 0, discretization, bounds) == 5.0