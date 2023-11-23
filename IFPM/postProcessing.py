import numpy as np
import pyvista as pv
import pathlib
import matplotlib.pyplot as plt
from pathlib import Path


class IFPM_postProc:
    def __init__(
            self,
            vtk_path: Path,
            in_margin: float,
            out_margin: float,
            size: dict
    ) -> None:
        self.in_margin = in_margin
        self.out_margin = out_margin
        self.size = size
        self.vtk_path = vtk_path

        self.body_cells, self.inlet_cells, self.outlet_cells = self.trimm_mesh()

        self.U_field = self.body_cells.cell_data['U']
        self.p_field = self.body_cells.cell_data['p']

        self.cell_volume_values = self.body_cells['Volume']

        self.T, self.uMag_avg, self.uX_avg = self.calculate_tortuosity()
        self.inplet_press_plane, self.outlet_perss_plane = \
            self.get_pressure_meas_planes()

        self.pi = self.calculate_pi()
        self.delta_p = self.calculate_avg_pressure_drop()
        self.friction_factor, self.re_Dash = self.calculate_friction_factor()

    def trimm_mesh(self):
        mesh = pv.read(self.vtk_path)
        inlet_marg = mesh.clip('x', origin=(self.in_margin, 0, 0), invert=True)
        outlet_marg = mesh.clip(
            'x',
            origin=(self.out_margin + self.size['x'], 0, 0),
            invert=False
        )
        mesh = mesh.clip('x', origin=(self.in_margin, 0, 0), invert=False)
        mesh = mesh.clip(
            'x',
            origin=(self.out_margin + self.size['x'], 0, 0),
            invert=True
        )
        mesh = mesh[0]
        mesh = mesh.compute_cell_sizes()
        inlet_marg = inlet_marg[0]
        inlet_marg = inlet_marg.compute_cell_sizes()
        outlet_marg = outlet_marg[0]
        outlet_marg = outlet_marg.compute_cell_sizes()

        return mesh, inlet_marg, outlet_marg

    def get_pressure_meas_planes(self):
        mesh = pv.read(self.vtk_path)
        inlet_pressure_plane = mesh.clip(
            'x',
            origin=(self.in_margin-1, 0, 0),
            invert=True
        )
        inlet_pressure_plane = inlet_pressure_plane.clip(
            'x',
            origin=(self.in_margin-2, 0, 0),
            invert=False
        )
        outlet_pressure_plane = mesh.clip(
            'x',
            origin=(self.out_margin + self.size['x'] + 1, 0, 0),
            invert=False
        )
        outlet_pressure_plane = outlet_pressure_plane.clip(
            'x',
            origin=(self.out_margin + self.size['x'] + 2, 0, 0),
            invert=True
        )

        inlet_pressure_plane = inlet_pressure_plane[0]
        inlet_pressure_plane = inlet_pressure_plane.compute_cell_sizes()
        outlet_pressure_plane = outlet_pressure_plane[0]
        outlet_pressure_plane = outlet_pressure_plane.compute_cell_sizes()

        return inlet_pressure_plane, outlet_pressure_plane

    def calculate_pi(self) -> float:
        print("    Calculating Participation Number")
        n = len(self.U_field)

        e_values = [
            s*(u[0]**2 + u[1]**2 + u[2]**2) for u, s in zip(
                self.U_field,
                self.cell_volume_values
                )
            ]
        e_tot = sum(e_values)
        q_values_squared = [(e/e_tot)**2 for e in e_values]
        pi = (n*sum(q_values_squared))**(-1)
        print(f"     {pi}")

        return pi

    def calculate_tortuosity(self) -> tuple:
        print("    Calculating Tortuosity")

        uMag = [np.sqrt(u[0]**2+u[1]**2+u[2]**2) for u in self.U_field]
        uX = [np.sqrt(u[0]**2) for u in self.U_field]
        uMag_sum = sum(uMag)
        uX_sum = sum(uX)

        uMag_avg = np.mean(uMag)
        uX_avg = np.mean(uX)

        tortuosity = uMag_sum / uX_sum
        print(f"     {tortuosity}")

        return tortuosity, uMag_avg, uX_avg, uMag_sum, uX_sum

    def calculate_entropy(self) -> float:
        print("    Calculating Gibbs Entorpy")

        all_e_values = [u[0]**2 + u[1]**2 + u[2]**2 for u in self.U_field]
        e_tot = sum(all_e_values)
        all_q_values = [e/e_tot for e in all_e_values]
        entropy = -sum([q*np.log(q) for q in all_q_values])
        print(f"     {entropy}")

        return entropy

    def calculate_avg_pressure_drop(self) -> float:
        """
        Calculate pressure difference between begining of the porous
        zone and the end of porous zone in OpenFOAM units [m^2 / s^2].
        delta_p = p_outlet - p_inlet
        """
        print("    Calculating Average Pressure Drop")
        p_inlet = self.inplet_press_plane.cell_data['p']
        p_outlet = self.outlet_perss_plane.cell_data['p']

        avg_p_inlet = np.mean(p_inlet)
        avg_p_outlet = np.mean(p_outlet)

        delta_p = abs(avg_p_outlet - avg_p_inlet)
        print(f"     {delta_p}")

        return delta_p

    def calculate_friction_factor(self) -> tuple:
        dp = self.delta_p  # In OF units [m^2 / s^2].
        model_length = (self.size['x'])
        print(f"Model Length is {model_length}")
        beta = 1.0
        # In OpenFOAM pressure field is really pressure / density
        f = -dp / (model_length * beta * self.uMag_avg**2)
        nu = 1.0e-6
        alpha = 1.0
        Re_dash = beta * self.uMag_avg / (alpha * nu)
        print(f"Re' = {Re_dash},  f = {f}")
        return f, Re_dash

    def calculate_mean_kinetic_energy_in_vortices(
            self,
            normalize: bool = False
            ):
        velocities = self.U_field
        vel_x = velocities[:, 0]
        volumes = self.cell_volume_values
        total_fuid_volume = np.sum(volumes)

        negative_vel_x_mask = vel_x < 0
        kinetic_energy_vortex = np.sum(
            2*vel_x[negative_vel_x_mask]**2 * volumes[negative_vel_x_mask]
        )

        mean_kin_energy_vortex = kinetic_energy_vortex / total_fuid_volume

        if normalize:
            min_value = np.min(mean_kin_energy_vortex)
            max_value = np.max(mean_kin_energy_vortex)
            mean_kin_energy_vortex = \
                (mean_kin_energy_vortex - min_value) / (max_value - min_value)

        return mean_kin_energy_vortex

    def velocity_distribution(
            self,
            save_path: pathlib.Path = None
            ) -> tuple:
        velocities = self.U_field
        print(velocities.shape)
        vel_x = velocities[:, 0]
        vel_y = velocities[:, 1]
        vel_z = velocities[:, 2]
        volumes = self.cell_volume_values
        volumes_ratio = volumes / np.sum(volumes)
        print(f"Total Volume: {np.sum(volumes)}")
        print(f"Total Volume Ratio: {np.sum(volumes_ratio)}")

        if save_path:
            fig, (ax1, ax2, ax3) = plt.subplots(
                nrows=1,
                ncols=3,
                figsize=(8, 4)
            )
            ax1.plot(vel_x, volumes_ratio, 'o', label="U_x")
            ax2.plot(vel_y, volumes_ratio, 'o', label="U_y")
            ax3.plot(vel_z, volumes_ratio, 'o', label="U_z")
            plt.legend()
            plt.savefig(save_path)

        vortex_velocity_x = np.sum(
            np.where(vel_x <= 0, vel_x, 0) * volumes_ratio
        )
        print(vortex_velocity_x)

        vel_mag = np.sqrt(vel_x**2 + vel_y**2 + vel_z**2)
        vortex_velocity_magnitude = np.sum(
            np.where(vel_x <= 0, vel_mag, 0) * volumes_ratio
        )
        print(vortex_velocity_magnitude)

        return vortex_velocity_x, vortex_velocity_magnitude

    def calculate_velocity_histogram(
        self,
        n_bins: int,
        normalized: bool = False,
        save_path: pathlib.Path = None
    ):
        velocity_field = self.U_field
        velocity_mag = np.linalg.norm(velocity_field, axis=1)
        mean_velocity = np.mean(velocity_mag)
        velocity_mag /= mean_velocity
        velocity_x = np.array(velocity_field[:, 0]) / mean_velocity
        velocity_y = np.array(velocity_field[:, 1]) / mean_velocity
        velocity_z = np.array(velocity_field[:, 2]) / mean_velocity
        velocity_transverse = [
            np.sqrt(v_y**2 + v_z**2) for v_y, v_z in zip(velocity_y, velocity_z)
        ]
        velocity_transverse = np.array(velocity_transverse) / mean_velocity

        volumes = np.array(self.cell_volume_values)

        histogram_mag = np.histogram(
            velocity_mag,
            bins=n_bins,
            weights=volumes,
            density=normalized
        )

        histogram_x = np.histogram(
            velocity_x,
            bins=n_bins,
            weights=volumes,
            density=normalized
        )

        histogram_y = np.histogram(
            velocity_y,
            bins=n_bins,
            weights=volumes,
            density=normalized
        )

        histogram_z = np.histogram(
            velocity_z,
            bins=n_bins,
            weights=volumes,
            density=normalized
        )

        histogram_transverse = np.histogram(
            velocity_transverse,
            bins=n_bins,
            weights=volumes,
            density=normalized
        )

        histograms = (
            histogram_mag,
            histogram_x,
            histogram_y,
            histogram_z,
            histogram_transverse
        )

        if save_path is not None:
            plt.cla()
            plt.clf()
            fig, ax = plt.subplots(1, 4, figsize=(16, 4))
            ax[0].hist(velocity_mag, weights=volumes, bins=n_bins, density=True)
            ax[0].set_title("Velocity magnitude")
            ax[0].set_xlabel("u/<u>")

            ax[1].hist(velocity_x, weights=volumes, bins=n_bins, density=True)
            ax[1].set_title("Longitudinal velocity")
            ax[1].set_xlabel(f"$u_x$/<u>")

            ax[2].hist(velocity_y, weights=volumes, bins=n_bins, density=True)
            ax[2].set_title("Transverse (y) velocity")
            ax[2].set_xlabel(f"$u_y$/<u>")

            ax[3].hist(velocity_z, weights=volumes, bins=n_bins, density=True)
            ax[3].set_title("Transverse (z) velocity")
            ax[3].set_xlabel(f"$u_z$/<u>")

            plt.savefig(save_path)
            plt.cla()
            plt.clf()

        return histograms

    def calculate_streamlines(self):
        mesh = self.body_cells
        internal_mesh = mesh.get(0)
        print(mesh.cells)
        print()
        print(mesh.cells_connectivity)
