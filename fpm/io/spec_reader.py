import pathlib
import tarfile
import shutil

import pandas as pd


def read_porous_medium_spec(
        working_dir: pathlib.Path,
        spec_name: str = 'porous_medium_spec.csv'
) -> pd.DataFrame:
    """Reads the porous medium specification file.

    Args:
        working_dir (pathlib.Path): Path to the working directory.
        spec_name (str, optional): Name of CSV file with the spec.
            Defaults to 'porous_medium_spec.csv'.

    Raises:
        FileNotFoundError: Fires if no constant directory is found.

    Returns:
        pd.DataFrame: pandas.DataFrame with the porous medium spec.
    """
    constant_archive = list(working_dir.glob('constant.tar.gz'))
    if len(constant_archive) > 1:
        print(
            Warning('More than one constant archive found. '
                    f'Choosing the first one {constant_archive[0]}.')
        )
    elif len(constant_archive) == 0:
        print(f"No constant archive found in the directory {working_dir}.")
    else:
        with tarfile.open(constant_archive[0], 'r') as tar:
            tar.extractall(working_dir)

    constant_dirs = [
        f for f in list(working_dir.glob('constant')) if 'tar.gz' not in f.name
    ]

    if len(constant_dirs) > 1:
        print(
            Warning('More than one constant directory found. '
                    f'Choosing the first one {constant_dirs[0]}.')
        )
        constant_dir = constant_dirs[0]
    elif len(constant_dirs) == 0:
        raise FileNotFoundError("No constant directory found in "
                                f"the directory {working_dir}.")
    else:
        constant_dir = constant_dirs[0]

    porous_medium_spec = pd.read_csv(constant_dir / spec_name)

    # Remove the constant directory
    for f in constant_dirs:
        shutil.rmtree(f)

    return porous_medium_spec


def read_openfoam_spec(
        search_dir: pathlib.Path,
        spec_name: str = 'OF_spec.csv'
) -> pd.DataFrame:
    """Reads the OpenFOAM specification file

    Args:
        search_dir (pathlib.Path): Path to the directory with the CSV
            spec file.
        spec_name (str, optional): Name of CSV file with openfoam spec.
            Defaults to 'OF_spec.csv'.

    Raises:
        FileNotFoundError: Fires if no spec file is found in the directory.

    Returns:
        pd.DataFrame: pandas.DataFrame with the OpenFOAM spec.
    """
    of_spec_paths = list(search_dir.glob(spec_name))
    if len(of_spec_paths) > 1:
        print(
            Warning('More than one OF_spec.csv file found in the '
                    'directory. Choosing the first one '
                    f'{of_spec_paths[0]}.')
        )

        of_spec_path = of_spec_paths[0]

    elif len(of_spec_paths) == 1:
        of_spec_path = of_spec_paths[0]

    elif len(of_spec_paths) == 0:
        raise FileNotFoundError(
            f"No {spec_name} files found in the directory {search_dir}."
        )

    of_spec = pd.read_csv(of_spec_path)

    return of_spec
