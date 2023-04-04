import os
import stl
import numpy as np
import pyvista as pv

class grain:
    def __init__(self,  i:float, j:float, k: float = 0.0,
                        d_i:float=1.0, d_j:float=1.0, d_k:float = 1.0) -> None:
        self.x  = i
        self.y  = j
        self.z  = k
        self.dx = d_i
        self.dy = d_j
        self.dz = d_k

        self.bounding_box = (
            self.x, self.x+self.dx,
            self.y, self.y+self.dy,
            self.z, self.z+self.dz
        )

        self.cube = pv.Cube(
            bounds = self.bounding_box
        )

        self.ribbon = self.generate_ribbon()
        self.name   = f"grain_{self.x}_{self.y}_{self.z}.stl"

    def generate_ribbon(self):
        points = [
            [self.x,         self.y,         self.z],           #  0
            [self.x+self.dx, self.y,         self.z],           #  1
            [self.x,         self.y+self.dy, self.z],           #  2
            [self.x+self.dx, self.y+self.dy, self.z],           #  3
            [self.x,         self.y,         self.z+self.dz],   #  4
            [self.x+self.dx, self.y,         self.z+self.dz],   #  5
            [self.x,         self.y+self.dy, self.z+self.dz],   #  6
            [self.x+self.dx, self.y+self.dy, self.z+self.dz]    #  7

        ]
        
        rectangles = [
            pv.Rectangle([points[0],points[4],points[6],points[2]]),
            pv.Rectangle([points[0],points[1],points[5],points[4]]),
            pv.Rectangle([points[2],points[3],points[7],points[6]]),
            pv.Rectangle([points[1],points[3],points[5],points[7]])
        ]

        ribbon = rectangles[0]
        for rec in rectangles[1:]:
            ribbon = ribbon.merge(rec)
        return ribbon
    
    def save(self, save_path) -> None:
        if self.dz == 1.0: 
            # 2D case
            self.ribbon.save(save_path)
        else:
            # 3D case
            self.cube.save(save_path)


class plane(grain):
    def __init__(self, i:float, j:float, k:float, 
                d_i:float, d_j:float, d_k:float) -> None:
        self.x  = i
        self.y  = j
        self.z  = k
        self.dx = d_i
        self.dy = d_j
        self.dz = d_k

        if self.dx == 0:
            self.normal = (1,0,0)
            self.i_size = self.dy
            self.j_size = self.dz
        elif self.dy == 0:
            self.normal = (0,1,0)
            self.i_size = self.dx
            self.j_size = self.dz
        elif self.dz == 0:
            self.normal = (0,0,1)
            self.i_size = self.dx
            self.j_size = self.dy

        self.center = [
            self.x + 0.5*self.dx,
            self.y + 0.5*self.dy,
            self.z + 0.5*self.dz,
        ]

        self.plane = pv.Plane(
            center = self.center,
            direction = self.normal,
            i_size = self.i_size,
            j_size = self.j_size,
            i_resolution = 1,
            j_resolution = 1
        )

    def save(self, save_path) -> None:
        self.plane.save(save_path)


class sphere:
    def __init__(self,  i:float, j:float, k: float = 0.0, 
                 diameter:float=1.0) -> None:
        self.radius = diameter/2
        self.x = i
        self.y = j
        self.z = k
        self.name   = f"sphere_{self.x}_{self.y}_{self.z}.stl"

        self.sphere = pv.Sphere(
            self.radius,
            center=[self.x+0.5, self.y+0.5, self.z+0.5],
            theta_resolution=30,
            phi_resolution=30
        )
