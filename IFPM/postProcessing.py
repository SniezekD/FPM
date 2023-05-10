import numpy as np
import utils
from ifpm import IFPM
import pyvista as pv
import re 
from pathlib import Path


class IFPM_postProc:
    def __init__(self, vtk_path:Path, margin:float, size:dict) -> None:
        self.margin       = margin
        self.size         = size
        self.vtk_path     = vtk_path
        self.cell_volumes, self.inlet_cells, self.outlet_cells = self.trimm_mesh()
        self.U_field      = self.cell_volumes.cell_data['U']
        self.p_field      = self.cell_volumes.cell_data['p']
        self.cell_volumes = self.cell_volumes['Volume']
        self.T            = self.calculate_tortuosity()
        self.pi           = self.calculate_pi()
        # self.entropy      = self.calculate_entropy()
        self.delta_p      = self.calculate_avg_pressure_drop()


    def trimm_mesh(self):
        mesh = pv.read(self.vtk_path)
        inlet_marg = mesh.clip('x', origin= (self.margin, 0,0), invert=True) 
        outlet_marg = mesh.clip(
            'x', 
            origin=(self.margin + self.size['x'],0,0),
            invert=False
        ) 
        mesh = mesh.clip('x', origin= (self.margin, 0,0), invert=False)
        mesh = mesh.clip(
            'x', 
            origin=(self.margin + self.size['x'],0,0),
            invert=True
        )
        mesh = mesh[0]
        mesh = mesh.compute_cell_sizes()
        inlet_marg = inlet_marg[0]
        inlet_marg = inlet_marg.compute_cell_sizes()
        outlet_marg = outlet_marg[0]
        outlet_marg = outlet_marg.compute_cell_sizes()

        return mesh, inlet_marg, outlet_marg


    def calculate_pi(self) -> float:
        print("    Calculating Participation Number")
        n = len(self.U_field)

        e_values = [
            s*(u[0]**2 + u[1]**2 + u[2]**2) for u, s in zip(
                self.U_field,
                self.cell_volumes
                )
            ]
        total_volume = np.sum(self.cell_volumes)
        e_tot = sum(e_values)
        q_values_squared = [(e/e_tot)**2 for e in e_values]
        pi = (n*sum(q_values_squared))**(-1)
        print(f"     {pi}")

        return pi
    

    def calculate_tortuosity(self) -> float:
        print("    Calculating Tortuosity")

        uMag_sum = sum([np.sqrt(u[0]**2+u[1]**2+u[2]**2) for u in self.U_field])
        uX_sum   = sum([np.sqrt(u[0]**2) for u in self.U_field])
        print(f"     {uMag_sum / uX_sum}")

        return uMag_sum / uX_sum
    

    def calculate_entropy(self) -> float:
        print("    Calculating Gibbs Entorpy")

        all_e_values = [u[0]**2 + u[1]**2 + u[2]**2 for u in self.U_field]
        e_tot        = sum(all_e_values)
        all_q_values = [e/e_tot for e in all_e_values]
        entropy      = -sum([q*np.log(q) for q in all_q_values])
        print(f"     {entropy}")

        return entropy
    

    def calculate_avg_pressure_drop(self) -> float:
        print("    Calculating Average Pressure Drop")
        p_inlet = self.inlet_cells.cell_data['p']
        p_outlet = self.outlet_cells.cell_data['p']

        avg_p_inlet = np.mean(p_inlet)
        avg_p_outlet = np.mean(p_outlet)

        delta_p = abs(avg_p_inlet - avg_p_outlet)
        delta_p_on_L = delta_p / self.size['x'] - 2*self.margin

        print(f"     {delta_p}")

        
        return delta_p

