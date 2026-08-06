from typing import Tuple
import logging

import numpy as np
import pyvista as pv

from fpm.media_models.porous_medium import PorousMedium


logger = logging.getLogger(__name__)


def map_distance_to_index_difference(
    dx: float,
    dy: float,
    dz: float,
    discretization: tuple,
    bounds: dict
):
    """Maps cartesian distance to difference in indices of discretized matrix
    representing the porous medium.

    Args:
        x (float): x Cartesian distance
        y (float): y Cartesian distance
        z (float): z Cartesian distance
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (dict): bounding box of the porous medium in the following
            format: {x_min, x_max, y_min, y_max, z_min, z_max}

    Returns:
        tuple: number of indexes in each direction of discretized porous medium
    """
    d_x = (bounds["x_max"] - bounds["x_min"]) / discretization[0]
    d_y = (bounds["y_max"] - bounds["y_min"]) / discretization[1]
    d_z = (bounds["z_max"] - bounds["z_min"]) / discretization[2]

    index_diff_x = np.floor(dx / d_x)
    index_diff_y = np.floor(dy / d_y)
    index_diff_z = np.floor(dz / d_z)

    index_dist = np.floor(
        np.sqrt(
            index_diff_x**2 + index_diff_y**2 + index_diff_z**2
        )
    )

    return index_dist


def map_index_difference_to_distance(
    d_i: int,
    d_j: int,
    d_k: int,
    discretization: tuple,
    bounds: dict
) -> float:
    """Maps cartesian distance to difference in indices of discretized matrix
    representing the porous medium.

    Args:
        d_i (int): index difference in 0th axis
        d_j (int): index difference in 1st axis
        d_k (int): index difference in 2nd axis
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (dict): bounding box of the porous medium in the following
            format: {x_min, x_max, y_min, y_max, z_min, z_max}

    Returns:
        float: Cartesian distance
    """
    d_x = (bounds["x_max"] - bounds["x_min"]) / discretization[0]
    d_y = (bounds["y_max"] - bounds["y_min"]) / discretization[1]
    d_z = (bounds["z_max"] - bounds["z_min"]) / discretization[2]

    dx = d_i * d_x
    dy = d_j * d_y
    dz = d_k * d_z

    cartesian_dist = np.sqrt(dx**2 + dy**2 + dz**2)

    return cartesian_dist


def map_coordinate_to_index(
    x: float,
    y: float,
    z: float,
    discretization: tuple,
    bounds: dict
):
    """Maps cartesian coordinates to indices of discretized matrix
    representing the porous medium.

    Args:
        x (float): x Cartesian coordinate
        y (float): y Cartesian coordinate
        z (float): z Cartesian coordinate
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (dict): bounding box of the porous medium in the following
            format: {x_min, x_max, y_min, y_max, z_min, z_max}

    Returns:
        tuple: indexes in discretized porous medium
    """
    d_x = (bounds["x_max"] - bounds["x_min"]) / discretization[0]
    d_y = (bounds["y_max"] - bounds["y_min"]) / discretization[1]
    d_z = (bounds["z_max"] - bounds["z_min"]) / discretization[2]

    index_x = np.floor((x - bounds["x_min"]) / d_x)
    index_y = np.floor((y - bounds["y_min"]) / d_y)
    index_z = np.floor((z - bounds["z_min"]) / d_z)

    return index_x, index_y, index_z


def map_index_to_coordinate(
    i: int,
    j: int,
    k: int,
    discretization: tuple,
    bounds: dict
):
    """Maps indices of discretized matrix
    representing the porous medium to cartesian coordinates.

    Args:
        i (int): index in 0th axis
        j (int): index in 1st axis
        k (int): index in 2nd axis
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (dict): bounding box of the porous medium in the following
            format: {x_min, x_max, y_min, y_max, z_min, z_max}

    Returns:
        tuple: Cartesian coordinates in (x, y, z) format.
    """
    d_x = (bounds["x_max"] - bounds["x_min"]) / discretization[0]
    d_y = (bounds["y_max"] - bounds["y_min"]) / discretization[1]
    d_z = (bounds["z_max"] - bounds["z_min"]) / discretization[2]

    x = bounds["x_min"] + i * d_x
    y = bounds["y_min"] + j * d_y
    z = bounds["z_min"] + k * d_z

    return x, y, z


def calculate_porosity(
    porous_medium: PorousMedium,
    obstacles: list = None,
    discretization: tuple = (100, 100, 100),
    saved_state: np.ndarray = None
) -> Tuple[float, np.ndarray]:
    """Calculate porosity of given porous medium.
    The larger the discretization, the better the precision.

    Discretized porous medium is a np.ndarray with shape = discretization.
    There are two possible states: 1 and 0.
    1 -> free space
    0 -> space occupied by an obstacle

    Args:
        porous_medium (porousMedium): Porous medium
        discretization (int, optional): Defines porous media
            discretization. If given porous medium has size AxBxC, then the
            size of single discretization voxel will be
            A/discretization[0] x B/discretization[1] x C/discretization[2]
            Defaults to (100, 100, 100).

    Returns:
        Tuple[float, np.ndarray]: (
            Porosity of the porous medium,
            discretized porous medium
        )
    """

    if obstacles is None:
        obstacles_list = porous_medium.obstacles
    else:
        obstacles_list = obstacles
    if porous_medium.bounds is None:
        logger.error(
            "Trying to calculate porosity, but bounds are not defined. Exiting!"
        )
        exit(1)

    if obstacles_list is None:
        logger.warning("There are no obstacles!")
        return 1.0, np.ones((discretization[0], discretization[1], discretization[2]))

    # discretized porous medium
    if saved_state is None:
        discretized_pm = np.ones(
            (discretization[0], discretization[1], discretization[2])
        )
    else:
        discretized_pm = saved_state

    nx = np.linspace(
        porous_medium.bounds["x_min"],
        porous_medium.bounds["x_max"],
        discretization[0]
    )
    ny = np.linspace(
        porous_medium.bounds["y_min"],
        porous_medium.bounds["y_max"],
        discretization[1]
    )
    nz = np.linspace(
        porous_medium.bounds["z_min"],
        porous_medium.bounds["z_max"],
        discretization[2]
    )

    pm_x, pm_y, pm_z = np.meshgrid(nx, ny, nz)

    if saved_state is not None:
        obstacles_list = [obstacles_list[-1]]

    for obstacle in obstacles_list:
        if obstacle.type == 'sphere':
            dist_arr = np.sqrt(
                (pm_x - obstacle.position[0])**2 +
                (pm_y - obstacle.position[2])**2 +
                (pm_z - obstacle.position[1])**2
            )

            mask = dist_arr <= obstacle.radius
            discretized_pm[mask] = 0

        elif obstacle.type in ["Cube", "RoundedCube", "Cylinder"]:
            mesh_model = obstacle.to_stl()
            points = np.array([nx.flatten(), ny.flatten(), nz.flatten()]).T
            points_poly = pv.PolyData(points)
            points_inside = points_poly.select_enclosed_points(mesh_model)

            idxs_of_pts_inside = np.where(points_inside['SelectedPoints'])[0]

            points_inside_coords = [
                points_inside.GetPoint(x) for x in idxs_of_pts_inside
            ]

            discretized_pm_idxs = [
                map_coordinate_to_index(
                    x=p[0],
                    y=p[1],
                    z=p[2],
                    discretization=discretization,
                    bounds=porous_medium.bounds
                ) for p in points_inside_coords
            ]

            discretized_pm[discretized_pm_idxs] = 0

        else:
            logger.error(
                "Obstacles of type %s are not implemented here yet.",
                obstacle.type
            )
            exit(1)

    bulk_volume = discretization[0] * discretization[1] * discretization[2]
    porosity = np.sum(discretized_pm) / bulk_volume

    return porosity, discretized_pm
