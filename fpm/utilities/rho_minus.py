import numpy as np
import pandas as pd


def compute_rho_minus(
    vtk_df: pd.DataFrame,
    streamwise_direction: str = 'x'
) -> float:
    """Computes the rho_minus for a given VTK file.
    Necessary columns in the VTK DataFrame are:
    - u_{streamwise_direction}: Streamwise velocity component.
    - volume: Volume of the cell

    rho_minus is defined as the ratio of the volume of the
    cells with negative streamwise velocity to the total
    volume of the domain.

    Args:
        vtk_df (pd.DataFrame): DataFrame containing the VTK data.
        streamwise_direction (str, optional): Streamwise direction.
            Shoud be one of ['x', 'y','z'].  Defaults to 'x'.

    Returns:
        float: rho_minus.
    """
    u_streamwise = vtk_df[f'u_{streamwise_direction}']
    negative_vel_mask = u_streamwise < 0
    volumes = vtk_df['volume']

    rho_minus = np.sum(volumes[negative_vel_mask]) / np.sum(volumes)

    return rho_minus
