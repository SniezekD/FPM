import sys
import pathlib
import subprocess
import numpy as np
import jinja2


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
    print(f"... created {file_path}")

    run_cmd(
        ["chmod", "u+x", f"{file_path}"]
    )

    return file_path
