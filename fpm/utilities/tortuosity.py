import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_tortuosity(
    vtk_df: pd.DataFrame,
    streamwise_axis: str | None = 'x'
) -> float:
    """Computes the tortuosity for a given VTK file.
    Necessary columns in the VTK DataFrame are:
    - u_norm: Norm of the velocity vector.
    - u_{streamwise_direction}: Streamwise velocity component.
    - mass_density: Mass density.
    - volume: Volume of the cell

    Args:
        vtk_df (pd.DataFrame): DataFrame containing the VTK data.
        streamwise_direction (str, optional): Streamwise direction.
            Should be one of ['x', 'y','z'].  Defaults to 'x'.

    Returns:
        float: tortuosity.
    """
    if streamwise_axis is None:
        raise ValueError("streamwise_direction must be one of ['x', 'y', 'z'], "
                         f"not {streamwise_axis}")
    u_norm = vtk_df['u_norm']
    u_streamwise = vtk_df[f'u_{streamwise_axis}']
    mass_density = vtk_df['mass_density']

    volumes = vtk_df['volume']

    total_momentum_arr = mass_density * volumes * u_norm
    streamwise_momentum_arr = mass_density * volumes * u_streamwise

    tortuosity = np.sum(total_momentum_arr) / np.sum(streamwise_momentum_arr)

    return tortuosity


def plot_tortuosity_on_polar_plot(
        vtk_df: pd.DataFrame,
        streamwise_direction_vector: np.ndarray,
        plot_save_path: str = None,
        angle_accuracy: float = 0.001,
):
    mass_density = vtk_df['mass_density']
    volumes = vtk_df['volume']
    masses = mass_density * volumes
    u_norm = vtk_df['u_norm']
    momentum = masses * u_norm
    momentum_direction = np.arccos(
        np.dot(streamwise_direction_vector, vtk_df[['u_x', 'u_y', 'u_z']].T)
        / (np.linalg.norm(streamwise_direction_vector) * u_norm)
    )
    angle_bin_edges = np.arange(0, 2 * np.pi, angle_accuracy)
    angle_bin_middle = (angle_bin_edges[:-1] + angle_bin_edges[1:]) / 2
    angle_momentum = [
        np.sum(
            momentum[
                (momentum_direction >= bin_start)
                & (momentum_direction < bin_end)
            ]
        )
        for bin_start, bin_end in zip(
            angle_bin_edges[: -1],
            angle_bin_edges[1:]
        )
    ]
    angle_momentum = np.array(angle_momentum)

    # Create a polar plot
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.scatter(angle_bin_middle, angle_momentum, c='r', s=1)
    ax.set_title('Tortuosity on Polar Plot')
    ax.set_xlabel('Angle (radians)')
    ax.set_ylabel('Momentum')
    # Save the plot
    if plot_save_path is None:
        fig.savefig(plot_save_path)
    # Close the plot
    plt.close(fig)
