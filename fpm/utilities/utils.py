import sys
import subprocess
import numpy as np


def run_cmd(args: list, shell: bool = True):
    status = subprocess.run(args, shell)
    if status.returncode == 0:
        print("     Done")
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
