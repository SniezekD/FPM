import sys
import numpy as np


def ordered_PM_lattice(
        porosity: float,
        x_dim: int,
        y_dim: int,
        z_dim: int = 0,
        in_margin: int = 4,
        out_margin: int = 4
) -> np.ndarray:
    """ 
    This function produces a ordered porous medium lattice of given size.
    """

    lattice = np.zeros((x_dim, y_dim, z_dim))
    if z_dim == 0 or z_dim == 1:
        # A 2D case
        number_of_obstacles = x_dim * y_dim * (1 - porosity)
        number_of_x_rows = int(np.ceil(number_of_obstacles**(1/2)))
        number_of_y_rows = int(np.floor(number_of_obstacles**(1/2)))

        x_coords = np.linspace(0, x_dim-1, number_of_x_rows+2)[1:-1]
        y_coords = np.linspace(0, y_dim-1, number_of_y_rows+2)[1:-1]

        for x in x_coords:
            for y in y_coords:
                lattice[int(x),int(y)] = 1

    elif z_dim > 1:
        # A 3D case
        number_of_obstacles = x_dim * y_dim * z_dim (1 - porosity)
        number_of_x_rows = int(np.ceil(number_of_obstacles**(1/3)))
        number_of_y_rows = int(np.ceil(number_of_obstacles**(1/3)))
        number_of_z_rows = int(np.floor(number_of_obstacles**(1/3)))

        x_coords = np.linspace(0, x_dim-1, number_of_x_rows+2)[1:-1]
        y_coords = np.linspace(0, y_dim-1, number_of_y_rows+2)[1:-1]
        z_coords = np.linspace(0, z_dim-1, number_of_z_rows+2)[1:-1]

        for x in x_coords:
            for y in y_coords:
                for z in z_coords:
                    lattice[int(x),int(y),int(z)] = 1
    else:
        sys.exit("Illegal value of input")

    lattice  = np.insert(
            lattice, 
            0, 
            np.zeros((in_margin, y_dim, z_dim)),
            axis=0
        )
    lattice  = np.append(
            lattice,
            np.zeros((out_margin, y_dim, z_dim)),
            axis=0
        )
    lattice  = lattice.transpose()

    return lattice
