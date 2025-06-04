import pandas as pd
import numpy as np


def compute_participation_number(
    vtk_df: pd.DataFrame,
    norm_const_type: str = 'n_cells'
) -> float:
    """Computes the participation number for a given VTK file.
        Necessary columns in the VTK DataFrame are:
        - u_norm: Norm of the velocity vector.
        - rho: Mass density.
        - volume: Volume of the cell

    Args:
        vtk_df (pd.DataFrame): DataFrame containing the VTK data.
        norm_const_type (str, optional): Type of normalization constant.
            Should be one of ['n_cells', 'volume']. Defaults to 'n_cells'.
    Returns:
        float: Participation number.
    """
    if norm_const_type == 'n_cells':
        norm_const = len(vtk_df)
    elif norm_const_type == 'volume':
        norm_const = np.sum(vtk_df['volume'])**2 / np.sum(vtk_df['volume']**2)

    u_norm = vtk_df['u_norm']
    rho = vtk_df['mass_density']

    volumes = vtk_df['volume']

    e_kin_arr = 0.5 * rho * volumes * u_norm**2
    e_kin_tot = np.sum(e_kin_arr)
    q_arr = e_kin_arr / e_kin_tot

    q_squared = q_arr**2
    participation_number = 1 / (norm_const * np.sum(q_squared))

    return participation_number
