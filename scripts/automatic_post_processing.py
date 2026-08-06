import pathlib
import argparse
import tarfile
import logging

import pandas as pd
import numpy as np
from fpm.io.vtk_reader import read_vtk
from fpm.utilities.participation_number import compute_participation_number
from fpm.utilities.rho_minus import compute_rho_minus
from fpm.utilities.tortuosity import (
    compute_tortuosity,
    plot_tortuosity_on_polar_plot
)
from fpm.io.spec_reader import read_porous_medium_spec, read_openfoam_spec
from fpm.utilities.utils import calculate_inlet_flow_rate


logger = logging.getLogger(__name__)


def parse_cla():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i',
        '--input-archive',
        help='Path to the main archive for given geometry.',
        type=str,
        required=True
    )

    parser.add_argument(
        '-o',
        '--output-dir',
        help='Path to the output directory.',
        type=str,
        required=True
    )

    parser.add_argument(
        '-n',
        '--norm-const-type',
        help=('Type of normalization constant for'
              'participation number computation.'),
        type=str,
        default='n_cells'
    )

    parser.add_argument(
        '-s',
        '--streamwise-direction',
        help='Streamwise direction.',
        type=str,
        default='x'
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_cla()

    results_df = pd.DataFrame(
        columns=[
            'porosity',
            'inlet_flow_rate',
            'participation_number',
            'rho_minus',
            'tortuosity'
        ]
    )

    input_archive = pathlib.Path(args.input_archive)
    output_dir = pathlib.Path(args.output_dir)

    working_dir = output_dir / 'working_dir'
    working_dir.mkdir(parents=True, exist_ok=True)

    # Unpack the main archive
    with tarfile.open(input_archive, 'r') as tar:
        tar.extractall(working_dir)

    porous_medium_spec = read_porous_medium_spec(working_dir)
    logger.debug("Porous medium spec:\n %s", porous_medium_spec)

    # Unpack U archives
    u_archives = list(working_dir.glob('U_*.tar.gz'))
    for u_archive in u_archives:
        with tarfile.open(u_archive, 'r') as tar:
            tar.extractall(working_dir)

    u_dirs = [
        f for f in list(working_dir.glob('U_*')) if 'tar.gz' not in f.name
    ]

    for u_dir in u_dirs:
        vtk_paths = list(u_dir.glob('*.vtk'))
        logger.debug(f"\n\n{vtk_paths}")
        if len(vtk_paths) > 1:
            logger.warning(
                'More than one vtk file found in the directory. '
                'Choosing the first one %s.',
                {vtk_paths[0]}
            )
        elif len(vtk_paths) == 0:
            logger.warning("No vtk files found in the directory %s.", u_dir)
            continue

        vtk_path = vtk_paths[0]

        vtk_df = read_vtk(vtk_path)
        participation_number = compute_participation_number(
            vtk_df=vtk_df,
            norm_const_type=args.norm_const_type
        )
        rho_minus = compute_rho_minus(
            vtk_df=vtk_df,
            streamwise_axis=args.streamwise_direction
        )
        tortuosity = compute_tortuosity(
            vtk_df=vtk_df,
            streamwise_axis=args.streamwise_direction
        )

        plot_tortuosity_on_polar_plot(
            vtk_df=vtk_df,
            streamwise_direction_vector=np.array([1, 0, 0]),
            plot_save_path=u_dir / 'tortuosity_polar_plot{u_dir}.png',
        )

        of_spec = read_openfoam_spec(u_dir, 'OF_spec.csv')

        inlet_flow_rate = calculate_inlet_flow_rate(of_spec)

        results_df.loc[len(results_df)] = {
            'porosity': porous_medium_spec['porosity'].values[0],
            'inlet_flow_rate': inlet_flow_rate,
            'participation_number': participation_number,
            'rho_minus': rho_minus,
            'tortuosity': tortuosity
        }

    logger.debug("Results:\n %s", results_df)
    results_df.to_csv(output_dir / 'results.csv', index=False)
