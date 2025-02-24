import pathlib
import pyvista as pv
import numpy as np
import pandas as pd


def read_vtk(
    path_to_vtk: pathlib.Path,
    interest_b_box: np.ndarray = None
) -> pd.DataFrame:
    """Reads VTK and parses it into a pandas Dataframe
    with velocity components, and cell sizes. The input
    VTK can be cut in norder to analyze only the volume
    of interest.

    Args:
        path_to_vtk (pathlib.Path): Path to VTK file.
        interest_b_box (np.ndarray): Bounding box of interest.
            (x_min, x_max, y_min, y_max, z_min, z_max)

    Returns:
        pd.DataFrame
    """
    raw_vtk = pv.read(path_to_vtk)
    vtk = raw_vtk.compute_cell_sizes()
    u_x = vtk['U'][:, 0]
    u_y = vtk['U'][:, 1]
    u_z = vtk['U'][:, 2]
    u_norm = np.sqrt(u_x**2 + u_y**2 + u_z**2)

    volumes = vtk['Volume']
    cell_ids = vtk['cellID']

    cells_points = {}
    vtk_cells = vtk.cells
    i = 0
    while len(cells_points) < len(u_x):
        no_of_points = vtk_cells[i]
        cells_points[len(cells_points)] = vtk_cells[i+1:i+no_of_points+1]
        i += no_of_points + 1

    x_pos = vtk.points[:, 0]
    y_pos = vtk.points[:, 1]
    z_pos = vtk.points[:, 2]

    cells_positions_x = np.array([
        np.mean(x_pos[points_list]) for k, points_list in cells_points.items()
    ])
    cells_positions_y = np.array([
        np.mean(y_pos[points_list]) for k, points_list in cells_points.items()
    ])
    cells_positions_z = np.array([
        np.mean(z_pos[points_list]) for k, points_list in cells_points.items()
    ])

    if interest_b_box is not None:
        x_mask = (cells_positions_x >= interest_b_box[0]) & (cells_positions_x <= interest_b_box[1])
        y_mask = (cells_positions_y >= interest_b_box[2]) & (cells_positions_y <= interest_b_box[3])
        z_mask = (cells_positions_z >= interest_b_box[4]) & (cells_positions_z <= interest_b_box[5])

        mask = x_mask & y_mask & z_mask

    else:
        mask = np.ones_like(u_x, dtype=bool)

    if 'rho' in vtk.array_names:
        mass_density = vtk['rho']
    else:
        mass_density = np.ones_like(u_x)

    df = pd.DataFrame(
        {
            'x': cells_positions_x[mask],
            'y': cells_positions_y[mask],
            'z': cells_positions_z[mask],
            'u_x': u_x[mask],
            'u_y': u_y[mask],
            'u_z': u_z[mask],
            'u_norm': u_norm[mask],
            'mass_density': mass_density[mask],
            'volume': volumes[mask],
        },
        index=cell_ids[mask]
    )

    return df


def read_vtm(
    path_to_vtm: pathlib.Path,
    interest_b_box: np.ndarray = None
) -> pd.DataFrame:
    """Reads VTM and parses it into a pandas Dataframe
    with velocity components, and cell sizes

    Args:
        path_to_vtk (pathlib.Path): Path to VTK file.

    Returns:
        pd.DataFrame
    """
    raw_vtm = pv.read(path_to_vtm)
    internal_mesh = raw_vtm['internal']
    vtk = internal_mesh.compute_cell_sizes()
    u_x = vtk['U'][:, 0]
    u_y = vtk['U'][:, 1]
    u_z = vtk['U'][:, 2]
    u_norm = np.sqrt(u_x**2 + u_y**2 + u_z**2)

    volumes = vtk['Volume']
    vtk['kin_e'] = volumes * u_norm**2 / 2
    print(np.sum(volumes * u_norm**2 / 2) / np.sum(volumes))
    vtk.save('test.vtk')
    if 'rho' in vtk.array_names:
        mass_density = vtk['rho']
    else:
        mass_density = np.ones_like(u_x)

    # Compute positions of cells centers
    cells_points = {}
    vtk_cells = vtk.cells
    i = 0
    while len(cells_points) < len(u_x):
        no_of_points = vtk_cells[i]
        cells_points[len(cells_points)] = vtk_cells[i+1:i+no_of_points+1]
        i += no_of_points + 1

    x_pos = vtk.points[:, 0]
    y_pos = vtk.points[:, 1]
    z_pos = vtk.points[:, 2]

    cells_positions_x = [
        np.mean(x_pos[points_list]) for k, points_list in cells_points.items()
    ]
    cells_positions_y = [
        np.mean(y_pos[points_list]) for k, points_list in cells_points.items()
    ]
    cells_positions_z = [
        np.mean(z_pos[points_list]) for k, points_list in cells_points.items()
    ]

    if interest_b_box is not None:
        x_mask = (cells_positions_x >= interest_b_box[0]) & (cells_positions_x <= interest_b_box[1])
        y_mask = (cells_positions_y >= interest_b_box[2]) & (cells_positions_y <= interest_b_box[3])
        z_mask = (cells_positions_z >= interest_b_box[4]) & (cells_positions_z <= interest_b_box[5])

        mask = x_mask & y_mask & z_mask

    else:
        mask = np.ones_like(u_x, dtype=bool)

    df = pd.DataFrame(
        {
            'x': cells_positions_x[mask],
            'y': cells_positions_y[mask],
            'z': cells_positions_z[mask],
            'u_x': u_x[mask],
            'u_y': u_y[mask],
            'u_z': u_z[mask],
            'u_norm': u_norm[mask],
            'mass_density': mass_density[mask],
            'volume': volumes[mask],
        },
        index=range(len(u_x[mask]))
    )

    return df
