import os
import stl
import numpy as np
from stl import mesh

class grain:
    def __init__(self,  i:float, j:float, k: float = 0.0,
                        d_i:float=1.0, d_j:float=1.0, d_k:float = 1.0) -> None:
        self.x  = i
        self.y  = j
        self.z  = k
        self.dx = d_i
        self.dy = d_j
        self.dz = d_k
        self.vertices =  np.array([\
                        [self.x,         self.y,          self.z        ],
                        [self.x+self.dx, self.y,          self.z        ],
                        [self.x+self.dx, self.y+self.dy,  self.z        ],
                        [self.x,         self.y+self.dy,  self.z        ],
                        [self.x,         self.y,          self.z+self.dz],
                        [self.x+self.dx, self.y,          self.z+self.dz],
                        [self.x+self.dx, self.y+self.dy,  self.z+self.dz],
                        [self.x,         self.y+self.dy,  self.z+self.dz]
                        ])
        self.faces = {'2d': np.array([\
                        [0,4,7],
                        [0,7,3],
                        [5,1,2],
                        [5,2,6],
                        [2,3,6],
                        [3,7,6],
                        [0,1,5],
                        [0,5,4]]),
                    '3d': np.array([\
                        [0,3,1],
                        [1,3,2],
                        [0,4,7],
                        [0,7,3],
                        [4,5,6],
                        [4,6,7],
                        [5,1,2],
                        [5,2,6],
                        [2,3,6],
                        [3,7,6],
                        [0,1,5],
                        [0,5,4]])
                    }
        self.cube   = self.generate_stl('3d')
        self.ribbon = self.generate_stl('2d')
        self.name   = f"grain_{self.x}_{self.y}_{self.z}.stl"

    def generate_stl(self, dim: str):
        cube = mesh.Mesh(np.zeros(self.faces[dim].shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(self.faces[dim]):
            for j in range(3):
                cube.vectors[i][j] = self.vertices[f[j],:]
        return  cube
    
    def save(self, save_path, mode) -> None:
        self.cube.save(save_path, mode=mode)


class plane(grain):
    def __init__(self, i:float, j:float, k:float, 
                d_i:float, d_j:float, d_k:float) -> None:
        self.x  = i
        self.y  = j
        self.z  = k
        self.dx = d_i
        self.dy = d_j
        self.dz = d_k

        self.vertices = np.array([\
        [self.x,         self.y,         self.z        ],
        [self.x+self.dx, self.y,         self.z+self.dz],
        [self.x,         self.y+self.dy, self.z+self.dz],
        [self.x+self.dx, self.y+self.dy, self.z        ],
        ])

        # Define the 2 triangles composing the plane
        if self.dx == 0:
            self.faces = {'2d': np.array([\
                [0,1,2],
                [3,1,2],
                ])}
        elif self.dy == 0:
            self.faces = {'2d': np.array([\
                [0,1,2],
                [3,2,0],
                ])}
        elif self.dz == 0:
            self.faces = {'2d': np.array([\
                [0,1,2],
                [3,1,0],
                ])}
        else:
            self.faces = {'2d': np.array([\
                [0,1,2],
                [2,3,0],
                ])}
        self.plane = self.generate_stl('2d')
    
    def save(self, save_path, mode) -> None:
        self.plane.save(save_path, mode=mode)