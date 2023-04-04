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
        self.cell_volumes = self.trimm_mesh()
        self.U_field      = self.cell_volumes.cell_data['U']
        self.p_field      = self.cell_volumes.cell_data['p']
        self.cell_volumes = self.cell_volumes['Volume']
        self.T            = self.calculate_tortuosity()
        self.pi           = self.calculate_pi()
        self.entropy      = self.calculate_entropy()

    def trimm_mesh(self):
        mesh = pv.read(self.vtk_path)
        mesh = mesh.clip('x', origin= (self.margin, 0,0), invert=False)
        mesh = mesh.clip(
            'x', 
            origin=(self.margin + self.size['x'],0,0),
            invert=True
        )
        mesh = mesh[0]
        mesh = mesh.compute_cell_sizes()

        return mesh

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
    

