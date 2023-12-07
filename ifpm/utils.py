import os
import sys
import subprocess
import pathlib
from typing import List
from pathlib import Path
from string import Template
import numpy as np
import matplotlib.pyplot as plt
import jinja2


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


def make_plot(number_of_geoms):
    re_vals = []
    pi_vals = []
    DP_vals = []
    t_vals = []
    f_vals = []
    rep_vals = []
    uX_vals = []
    uMag_vals = []
    for i in range(number_of_geoms):
        with open(f"results-{i}.dat") as file:
            tmp_Pi = []
            tmp_T = []
            tmp_DP = []
            tmp_F = []
            tmp_rep = []
            tmp_uX_vals = []
            tmp_uMag_vals = []

            for line in file:
                try:
                    vals = line.split()

                    if i == 0:
                        re_vals.append(float(vals[0]))

                    tmp_Pi.append(float(vals[1]))
                    tmp_T.append(float(vals[2]))
                    tmp_DP.append(float(vals[3]))
                    tmp_F.append(float(vals[6]))
                    tmp_rep.append(float(vals[7]))
                    tmp_uX_vals.append(float(vals[4]))
                    tmp_uMag_vals.append(float(vals[5]))
                except ValueError:
                    pass

            pi_vals.append(tmp_Pi)
            DP_vals.append(tmp_DP)
            t_vals.append(tmp_T)
            f_vals.append(tmp_F)
            rep_vals.append(tmp_rep)
            uX_vals.append(tmp_uX_vals)
            uMag_vals.append(tmp_uMag_vals)

    re_vals = [np.log10(re) for re in re_vals]
    std_err_Pi = standard_err(pi_vals)
    std_err_DP = standard_err(DP_vals)
    std_err_T = standard_err(t_vals)
    std_err_F = standard_err(f_vals)
    std_err_rep = standard_err(rep_vals)
    std_err_uX = standard_err(uX_vals)
    std_err_uMag = standard_err(uMag_vals)

    pi_vals = sum(np.array(pi_vals)) / number_of_geoms
    DP_vals = sum(np.array(DP_vals)) / number_of_geoms
    t_vals = sum(np.array(t_vals)) / number_of_geoms
    f_vals = sum(np.array(f_vals)) / number_of_geoms
    rep_vals = sum(np.array(rep_vals)) / number_of_geoms
    uX_vals = sum(np.array(uX_vals)) / number_of_geoms
    uMag_vals = sum(np.array(uMag_vals)) / number_of_geoms

    outfile = open("AvgResults.dat", "w")
    outfile.write(("log_10(Re)\tpi\tstd_pi\tT\tstd_T\tDP\tstd_DP\tFriciton\t"
                   "std_Friction\tre'\tstd_re'\tU_x_std_Ux\tU_mag\tstd_uMag\n"))
    for re, Pi, std_Pi, DP, std_DP, T, std_T, F, std_F, rep, std_rep, \
        u_x, std_ux, u_mag, std_umag in zip(
            re_vals,
            pi_vals,
            std_err_Pi,
            t_vals,
            std_err_T,
            DP_vals,
            std_err_DP,
            f_vals,
            std_err_F,
            rep_vals,
            std_err_rep,
            uX_vals,
            std_err_uX,
            uMag_vals,
            std_err_uMag
            ):
        outfile.write((f"{re}\t{Pi}\t{std_Pi}\t{DP}\t{std_DP}\t{T}"
                       f"\t{std_T}\t{F}\t{std_F}\t{rep}\t{std_rep}"
                       f"\t{u_x}\t{std_ux}\t{u_mag}\t{std_umag}\n"))

    outfile.close()


def read_data_from_file(path: Path):
    x_arr = []
    data_arr = []
    with open(path, "r") as file:
        for line in file:
            data = line.split()
            try:
                x_arr.append(float(data[0]))
                data_arr.append(np.array(data[1:], dtype=float))
            except ValueError:
                pass

    return x_arr, data_arr


def plot_residuals(collective_path: Path, savename: str = None) -> None:
    plt.rcParams.update({'font.size': 22})
    of_dirs = os.listdir(collective_path)
    of_dirs = [ofdir for ofdir in of_dirs if "OF_Model" in ofdir]
    of_dirs = sorted(of_dirs, key=lambda x: float(x.split('_')[-1]))
    number_of_plots = len(of_dirs)
    if number_of_plots % 4 != 0:
        col_number = 2
        row_number = int(np.ceil(number_of_plots/col_number))
        figsize = (col_number*10, row_number*5)
    else:
        col_number = 4
        row_number = int(np.ceil(number_of_plots/col_number))
        figsize = (col_number*5, row_number*5)
    fig, ax = plt.subplots(
        row_number,
        col_number,
        figsize=figsize,
    )
    fig.tight_layout(pad=3.0)
    labels = ["U${_x}$", "U${_y}$", "U${_z}$", "p"]

    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    _, labels = [sum(lol, []) for lol in zip(*lines_labels)]

    for i, ofdir in enumerate(of_dirs):
        Ux_path = collective_path.joinpath(ofdir, 'logs', 'Ux_0')
        Uy_path = collective_path.joinpath(ofdir, 'logs', 'Uy_0')
        if "Uz_0" in os.listdir(collective_path.joinpath(ofdir, 'logs')):
            Uz_path = collective_path.joinpath(ofdir, 'logs', 'Uz_0')
        else:
            Uz_path = None
        p_path = collective_path.joinpath(ofdir, 'logs', 'p_0')
        Re = float(ofdir.split('_')[-1])
        print(Ux_path)
        iters, Ux_data = read_data_from_file(Ux_path)
        _, Uy_data = read_data_from_file(Uy_path)
        if Uz_path is not None:
            _, Uz_data = read_data_from_file(Uz_path)
        _, p_data = read_data_from_file(p_path)

        Ux = [u[0] for u in Ux_data]
        Uy = [u[0] for u in Uy_data]
        if Uz_path is not None:
            Uz = [u[0] for u in Uz_data]
        p = [p[0] for p in p_data]

        ax[int(i / col_number), int(i % col_number)].plot(
            iters,
            Ux,
            label="U${_x}$",
            color="red",
            linewidth=4.0
        )
        ax[int(i / col_number), int(i % col_number)].plot(
            iters,
            Uy,
            label="U${_y}$",
            color="blue",
            linewidth=4.0
        )
        if Uz_path is not None:
            ax[int(i / col_number), int(i % col_number)].plot(
                iters,
                Uz,
                color="green",
                label="U${_z}$",
                linewidth=4.0
            )
        ax[int(i / col_number), int(i % col_number)].plot(
            iters,
            p,
            label="p",
            color="gray",
            linewidth=4.0
        )
        ax[int(i / col_number), int(i % col_number)].set_title(
            f"Re={Re:0.4f}"
        )
        ax[int(i / col_number), int(i % col_number)].set_yscale('log')

        tmp_ax = ax[int(i / col_number), int(i % col_number)]
        handles, labels = tmp_ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.015),
        ncols=4,
        columnspacing=5.0,
        labelspacing=5.0,
        fontsize=32,
        fancybox=True,
        frameon=True
    )
    if savename is not None:
        plt.savefig(f'{savename}.png',bbox_inches='tight')
    else:
        plt.show()


# /-------------------------------------------------------------------\
#                       OpenFOAM UTILITIES
# \-------------------------------------------------------------------/

def createBlockMeshDict(filePath, size, in_margin, out_margin):
    if size['z'] == 1:
        front_type = 'empty'
        back_type = 'empty'
    else:
        front_type = 'wall'
        back_type = 'wall'

    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates/OF_files/')
    )

    template = jinja2_env.get_template('blockMesh_template.txt')
    content = template.render(
        x=size['x'] + in_margin + out_margin,
        y=size['y'],
        z=size['z'],
        dx=2 * (size['x'] + in_margin + out_margin),
        dy=2 * size['y'],
        dz=2 * size['z'],
        front_bc_type=front_type,
        back_bc_type=back_type
    )
    with open(filePath, "w") as file:
        file.write(content)


def createMeshDict(
        file_path: pathlib.Path,
        surface_file_path: str = 'constant/triSurface/col_model.fms',
        min_cell_size: float = 0.25,
        max_cell_size: float = 0.25,
        additional_refinement_level: int = 2,
        refinement_thickness: float = 0.25
):
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates/OF_files/')
    )

    template = jinja2_env.get_template('cfmesh_template.txt')
    content = template.render(
        surface_file=surface_file_path,
        min_cell_size=min_cell_size,
        max_cell_size=max_cell_size,
        additional_refinement_level=additional_refinement_level,
        refinement_thickness=refinement_thickness
    )
    with open(file_path, "w") as file:
        file.write(content)


def createSnappyHexMeshDict(
        file_path: pathlib.Path,
        min_surface_refinement_lvl: int = 2,
        max_surface_refinement_lvl: int = 2,
        max_global_cells: int = 2000000,
        max_local_cells: int = 100000,
        location_in_mesh: List[float] = [0.5, 0.5, 0.5]
):
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates/OF_files/')
    )

    template = jinja2_env.get_template('snappyHexMesh_template.txt')
    content = template.render(
        min_surface_refinement_lvl=min_surface_refinement_lvl,
        max_surface_refinement_lvl=max_surface_refinement_lvl,
        max_global_cells=max_global_cells,
        max_local_cells=max_local_cells,
        location_in_mesh_x=location_in_mesh[0],
        location_in_mesh_y=location_in_mesh[1],
        location_in_mesh_z=location_in_mesh[2]
    )
    with open(file_path, "w") as file:
        file.write(content)


def make_0_U(
        filePath: pathlib.Path,
        front_type: str,
        back_type: str,
        Re: float
):
    velocity = Re*1e-6

    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates/OF_files/')
    )

    template = jinja2_env.get_template('U_template.txt')
    content = template.render(
        v=velocity,
        front_bc_type=front_type,
        back_bc_type=back_type

    )
    with open(filePath, "w") as file:
        file.write(content)


def make_0_p(
        filePath: pathlib.Path,
        front_type: str,
        back_type: str
):
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates/OF_files/')
    )

    template = jinja2_env.get_template('P_template.txt')
    content = template.render(
        front_bc_type=front_type,
        back_bc_type=back_type

    )
    with open(filePath, "w") as file:
        file.write(content)
