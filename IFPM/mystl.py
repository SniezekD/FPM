import os
import stl
import numpy as np
import pyvista as pv

class grain:
    def __init__(self, i:float, j:float, k: float = 0.0,
                       d_i:float=1.0, d_j:float=1.0, d_k:float = 1.0) -> None:
        self.x  = i
        self.y  = j
        self.z  = k
        self.dx = d_i
        self.dy = d_j
        self.dz = d_k
        self.stl = None

    def get_name(self):
        return f"grain_{self.x}_{self.y}_{self.z}.stl"

    def save(self, save_path) -> None:
        if self.stl is not None:
            self.stl.save(save_path)
        else:
            print("No stl to save!")


class cube(grain):
    def __init__(self, i: float, j: float, k: float = 0, d_i: float = 1, d_j: float = 1, d_k: float = 1) -> None:
        super().__init__(i, j, k, d_i, d_j, d_k)
        self.bounding_box = (
            self.x, self.x+self.dx,
            self.y, self.y+self.dy,
            self.z, self.z+self.dz
        )

        self.stl = pv.Cube(
            bounds = self.bounding_box
        )


class ribbon(grain):
    def __init__(self, i:float, j:float, k: float = 0.0,
                        d_i:float=1.0, d_j:float=1.0, d_k:float = 1.0) -> None:
        self.stl = self.generate_ribbon()
        super().__init__(i, j, k, d_i, d_j, d_k)

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


class plane(grain):
    def __init__(self, i: float, j: float, k: float = 0,
                       d_i: float = 1, d_j: float = 1, d_k: float = 1) -> None:
        super().__init__(i, j, k, d_i, d_j, d_k)

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

        self.stl = pv.Plane(
            center = self.center,
            direction = self.normal,
            i_size = self.i_size,
            j_size = self.j_size,
            i_resolution = 1,
            j_resolution = 1
        )

    def save(self, save_path) -> None:
        self.stl.save(save_path)


class sphere(grain):
    def __init__(self,  i:float, j:float, k: float, 
                 diameter:float=1.0) -> None:
        self.radius = diameter/2
        self.x = i
        self.y = j
        self.z = k
    

        self.stl = pv.Sphere(
            self.radius,
            center=[self.x+0.5, self.y+0.5, self.z+0.5],
            theta_resolution=30,
            phi_resolution=30
        )


class rounded_cube(grain):
    def __init__(self, i: float, j: float, k: float, r_r:float, d_i: float = 1, d_j: float = 1, d_k: float = 1) -> None:
        super().__init__(i, j, k, d_i, d_j, d_k)
        self.rounding_r = r_r

        self.bounding_box = (
            self.x, self.x+self.dx,
            self.y, self.y+self.dy,
            self.z, self.z+self.dz
        )

        self.cube = pv.Box(
            bounds=self.bounding_box,
            level=19,
            quads=False
        )

        self.sphere_center = [
            self.x + self.dx/2,
            self.y + self.dy/2,
            self.z + self.dz/2
        ]
        
        self.sphere = pv.Sphere(
            self.rounding_r,
            center=self.sphere_center,
            theta_resolution=30,
            phi_resolution=30
        ) 

        self.stl = self.sphere.boolean_intersection(self.cube)
