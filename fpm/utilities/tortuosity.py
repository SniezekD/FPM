import numpy as np
import pandas as pd


def compute_tortuosity(
    vtk_df: pd.DataFrame,
    streamwise_direction: str = 'x'
) -> float:
    """Computes the tortuosity for a given VTK file.
    Necessary columns in the VTK DataFrame are:
    - u_norm: Norm of the velocity vector.
    - u_{streamwise_direction}: Streamwise velocity component.
    - rho: Mass density.
    - volume: Volume of the cell

    Args:
        vtk_df (pd.DataFrame): DataFrame containing the VTK data.
        streamwise_direction (str, optional): Streamwise direction.
            Shoud be one of ['x', 'y','z'].  Defaults to 'x'.

    Returns:
        float: tortuosity.
    """
    u_norm = vtk_df['u_norm']
    u_streamwise = vtk_df[f'u_{streamwise_direction}']
    rho = vtk_df['rho']

    volumes = vtk_df['volume']

    total_momentum_arr = rho * volumes * u_norm
    streamwise_momentum_arr = rho * volumes * u_streamwise

    tortuosity = np.sum(total_momentum_arr) / np.sum(streamwise_momentum_arr)

    return tortuosity
