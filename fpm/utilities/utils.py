import sys
import pathlib
import subprocess

import numpy as np
import jinja2
import pandas as pd


def run_cmd(args: list, shell: bool = True):
    status = subprocess.run(
        args,
        shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
    if status.returncode == 0:
        print("     Done")
        return status.stdout.strip()
    else:
        print(f"     Error! \n{args} ended with code {status.returncode}.")
        sys.exit(status)


def standard_err(array):
    std_err_vec = []
    arr = np.array(array)
    for j in range(arr.shape[1]):
        vector = [arr[i, j] for i in range(arr.shape[0])]

        std_err_vec.append(np.std(vector, ddof=1) / np.sqrt(np.size(vector)))

    return std_err_vec


def create_runner_file(
    runner_name: str,
    runner_path: pathlib.Path,
    templates_dir_path: pathlib.Path,
    template_name: str,
    var_dict: dict
):
    jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir_path)
    )

    template = jinja_env.get_template(template_name)
    content = template.render(var_dict)

    file_path = runner_path / runner_name
    file_path.parent.mkdir(exist_ok=True, parents=True)

    with open(file_path, mode="w", encoding="utf-8") as file:
        file.write(content)
    print(f"  ... created {file_path}")

    run_cmd(
        ["chmod", "u+x", f"{file_path}"]
    )

    return file_path


def calculate_inlet_flow_rate(of_spec: pd.DataFrame) -> float:
    """Calculates the inlet flowrate from the OpenFOAM spec file

    Args:
        of_spec (pd.DateFrame): OpenFOAM spec file.

    Returns:
        float: Inlet flowrate [m^3 / s].
    """

    inlet_area = of_spec['inlet_area'].values[0]
    inlet_wall = of_spec['inlet_wall'].values[0]

    if inlet_wall in ['left', 'right']:
        streamline_velocity_id = 0
    elif inlet_wall in ['up', 'down']:
        streamline_velocity_id = 1
    elif inlet_wall in ['front', 'back']:
        streamline_velocity_id = 2

    inlet_velocity_str = of_spec['inlet_u_value'].values[0]
    start_idx = inlet_velocity_str.index('(') + 1
    end_idx = inlet_velocity_str.index(')')
    inlet_velocity = float(
        inlet_velocity_str[start_idx:end_idx].split()[streamline_velocity_id]
    )
    return inlet_velocity * inlet_area
