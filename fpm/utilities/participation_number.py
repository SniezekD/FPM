import pandas as pd
import numpy as np


def compute_participation_number(
    vtk_df: pd.DataFrame,
) -> float:
    """Computes the participation number for a given VTK file.
        Necessary columns in the VTK DataFrame are:
        - u_norm: Norm of the velocity vector.
        - mass_density: Mass density.
        - volume: Volume of the cell

        see https://arxiv.org/abs/2504.11287 for details

    Args:
        vtk_df (pd.DataFrame): DataFrame containing the VTK data.
    Returns:
        float: Participation number.
    """
    u_norm = vtk_df['u_norm']
    mass_density = vtk_df['mass_density']
    volumes = vtk_df['volume']
    total_volume = np.sum(volumes)

    e_kin_arr = 0.5 * mass_density * volumes * u_norm**2
    e_kin_tot = np.sum(e_kin_arr)
    q_arr = e_kin_arr / e_kin_tot

    q_squared = q_arr**2
    participation_number = 1 / (total_volume * np.sum(q_squared * volumes))

    return participation_number
