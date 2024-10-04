import numpy as np
import pyvista as pv
from fpm.media_models.porous_medium import porousMedium


def map_distance_to_index_difference(
    dx: float,
    dy: float,
    dz: float,
    discretization: tuple,
    bounds: tuple
):
    """Maps cartesian distance to diference in indices of discretized matrix
    representing the porous medium.

    Args:
        x (float): x Cartesian distance
        y (float): y Cartesian distance
        z (float): z Cartesian distance
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (tuple): bounding box of the porous medium in the following
            format: (x_min, x_max, y_min, y_max, z_min, z_max)

    Returns:
        tuple: number of indexes in each direction of discretized porous medium
    """
    d_x = (bounds[1] - bounds[0]) / discretization[0]
    d_y = (bounds[3] - bounds[2]) / discretization[1]
    d_z = (bounds[5] - bounds[4]) / discretization[2]

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
    bounds: tuple
) -> float:
    """Maps cartesian distance to diference in indices of discretized matrix
    representing the porous medium.

    Args:
        d_i (int): index difference in 0th axis
        d_j (int): index difference in 1st axis
        d_k (int): index difference in 2nd axis
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (tuple): bounding box of the porous medium in the following
            format: (x_min, x_max, y_min, y_max, z_min, z_max)

    Returns:
        float: Cartesian distance
    """
    d_x = (bounds[1] - bounds[0]) / discretization[0]
    d_y = (bounds[3] - bounds[2]) / discretization[1]
    d_z = (bounds[5] - bounds[4]) / discretization[2]

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
    bounds: tuple
):
    """Maps cartesian coordinates to indices of discretized matrix
    representing the porous medium.

    Args:
        x (float): x Cartesian coordinate
        y (float): y Cartesian coordinate
        z (float): z Cartesian coordinate
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (tuple): bounding box of the porous medium in the following
            format: (x_min, x_max, y_min, y_max, z_min, z_max)

    Returns:
        tuple: indexes in discretized porous medium
    """
    d_x = (bounds[1] - bounds[0]) / discretization[0]
    d_y = (bounds[3] - bounds[2]) / discretization[1]
    d_z = (bounds[5] - bounds[4]) / discretization[2]

    index_x = np.floor((x - bounds[0]) / d_x)
    index_y = np.floor((y - bounds[2]) / d_y)
    index_z = np.floor((z - bounds[4]) / d_z)

    return index_x, index_y, index_z


def map_index_to_coordinate(
    i: int,
    j: int,
    k: int,
    discretization: tuple,
    bounds: tuple
):
    """Maps indices of discretized matrix
    representing the porous medium to cartesian coordinates.

    Args:
        i (int): index in 0th axis
        j (int): index in 1st axis
        k (int): index in 2nd axis
        discretization (tuple): Tuple containing discretization parameters for
        x, y and z coordinates.
        bounds (tuple): bounding box of the porous medium in the following
            format: (x_min, x_max, y_min, y_max, z_min, z_max)

    Returns:
        tuple: Cartesian coordinates in (x, y, z) format.
    """
    d_x = (bounds[1] - bounds[0]) / discretization[0]
    d_y = (bounds[3] - bounds[2]) / discretization[1]
    d_z = (bounds[5] - bounds[4]) / discretization[2]

    x = i * d_x
    y = j * d_y
    z = k * d_z

    return x, y, z


def calculate_porosity(
    porous_medium: porousMedium,
    obstacles: list = None,
    discretization: tuple = (100, 100, 100),
    saved_state: np.ndarray = None
) -> float:
    """Calculate porosity of given porpus medium.
    The larger the discretization, the better the precision

    Args:
        porous_medium (porousMedium): Porous medium
        discretization (int, optional): Defines porous media
            discretization. If given porous medium has size AxBxC, then the
            size of single discretization voxel will be
            A/discretization[0] x B/discretization[1] x C/discretization[2]
            Defaults to (100, 100, 100).

    Returns:
        float: Porosity of the porous medium
    """

    if obstacles is None:
        obstacles_list = porous_medium.obstacles
    else:
        obstacles_list = obstacles
    if porous_medium.bounds is None:
        print("Trying to calculate porosity, but"
              "bounds are not defined. Exiting!")
        exit(1)

    if obstacles_list is None:
        print("There are no obstacles")
        return 1.0


    # discretized porous medium
    if saved_state is None:
        discretized_pm = np.ones(
            (discretization[0], discretization[1], discretization[2])
        )
    else:
        discretized_pm = saved_state

    nx = np.linspace(
        porous_medium.bounds[0],
        porous_medium.bounds[1],
        discretization[0]
    )
    ny = np.linspace(
        porous_medium.bounds[2],
        porous_medium.bounds[3],
        discretization[1]
    )
    nz = np.linspace(
        porous_medium.bounds[4],
        porous_medium.bounds[5],
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

        elif obstacle.type in ["Cube", "RoundedCube", "Cylinder"] :
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
            print(f"Obstacles of type {obstacle.type} are not "
                  "implemented here yet.")
            exit(1)

    bulk_volume = discretization[0] * discretization[1] * discretization[2]
    porosity = np.sum(discretized_pm) / bulk_volume

    return porosity, discretized_pm
