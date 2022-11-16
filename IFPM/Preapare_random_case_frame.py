# Prototype of a grain: a square that has 1 x 1  [m] dimensions 
# In fact, for OpenFoam it also needs to have third dimension, but it will be 
# set to one cell with cfMesh -> cartesian2DMesh
#
# Firstly, let's try the method in which we start without any obstacles, 
# and then lets throw them randomly onto the mesh.
#       Let's start with a 64 x 64 grid and chose some of its cells and put 
#       grains there.
#       
#       There are two ways of making a random lattice
#           1.0 ---- define a random square matrix with n = 64.
#           1.1 ---- set a threshold to epsilon (porosity) and 
#                    set matrix element do 1 or 0 accordingly                     
#           2.0 ---- randomly pick 64*64*epsilon pair of (x.y) coordinates.
#
#           2.1 ----            0 <= x <= 64,    0 <= y <= 64
#           2.2 ---- in randomly picked coordinates put and obstacle (grain) 
#
#
# Seconldy, let's try the method in which we start with a full slab, and then 
# let's cherry-pick some of the grains until a certain porosity is achieved.
#       Again, there we can do it in two ways, but the Matrix method seems to be
#       almost exactly the same as in the first approach. The only difference 
#       would be changing the criterion wheather in our matrix we put 0 or 1
#       (simply speaking we would change > operator into < and the other way 
#       around). 
#   

from tkinter import N
import numpy as np
from stl import mesh
import stl
import prepare_initial_conditions as pic

def create_random_lattice(epsilon, n):
    '''
    returns a random matrix with 0 as free space and 1 as obstacle. 
    '''
    mat = np.random.random((n,n))
    for x in range(mat.shape[0]):
        for y in range(mat.shape[1]):
            if mat[x][y] < epsilon:
                mat[x][y] = 0
            else:
                mat[x][y] = 1
    return mat

# lattice = create_random_lattice(0.9, 64)
# print(np.sum(lattice))
# print(np.sum(lattice)/ 64**2)

def create_grain_ribbon_stl(i:float, j:float, k: float = 0.0,
                            d_i:float=1.0, d_j:float=1.0, d_k:float = 1.0):
    """_summary_

    Args:
        i (float): minimum X-axis coordinate
        j (float): minimum Y-axis coordinate
        k (float): minimum Z-axis coordinate. Defaults to 0.
        d_i (float, optional): length in X direction. Defaults to 1.0.
        d_j (float, optional): length in X direction. Defaults to 1.0.
        d_k (float, optional): lenght in Z direction. Defaults to 0.

    Returns:
        stl_object: a ribbon with 8 vertices 
                    (a cuboid with 4 rather than 6 faces)
    """
    vertices = np.array([\
        [i,     j,      k    ],
        [i+d_i, j,      k    ],
        [i+d_i, j+d_j,  k    ],
        [i,     j+d_j,  k    ],
        [i,     j,      k+d_k],
        [i+d_i, j,      k+d_k],
        [i+d_i, j+d_j,  k+d_k],
        [i,     j+d_j,  k+d_k]
        ])

    # Define the 12 triangles composing the cube
    faces = np.array([\
        # [0,3,1],
        # [1,3,2],
        [0,4,7],
        [0,7,3],
        # [4,5,6],
        # [4,6,7],
        [5,1,2],
        [5,2,6],
        [2,3,6],
        [3,7,6],
        [0,1,5],
        [0,5,4]])

    # Create the mesh
    cube = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            cube.vectors[i][j] = vertices[f[j],:]
    return  cube

def create_boundary_plane_stl(i:float, j:float, k:float, 
                            d_i:float, d_j:float, d_k:float):
    """_summary_

    Args:
        i (float): minimum X-axis coordinate
        j (float): minimum Y-axis coordinate
        k (float): minimum Z-axis coordinate
        d_i (float): length in X direction
        d_j (float): lenght in Y direction
        d_k (float): lenght in Z direction

    Returns:
        stl_object: a plane
    """
    vertices = np.array([\
        [i,     j,     k    ],
        [i+d_i, j,     k+d_k],
        [i,     j+d_j, k+d_k],
        [i+d_i, j+d_j, k    ],
        ])

    # Define the 2 triangles composing the plane
    if d_k == 0:
        faces = np.array([\
            [0,1,2],
            [3,1,2],
            ])
    elif d_i == 0:
        faces = np.array([\
            [0,1,2],
            [3,2,0],
            ])
    elif d_j == 0:
        faces = np.array([\
            [0,1,2],
            [3,1,0],
            ])
    else:
        faces = np.array([\
            [0,1,2],
            [2,3,0],
            ])
    # Create the mesh
    cube = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            cube.vectors[i][j] = vertices[f[j],:]
    return  cube

def create_lattice_stl(lattice : np.array, save_name : str = None, n : int = 64, m: int = 4) -> mesh.Mesh:
    '''
    Converts a given lattice into a stl file.
    '''
    # Firstly, lets concateate four columns at the beginning and four at the end
    # The columns will have only 0 elements
    zero_col = np.zeros((lattice.shape[0], m))
    lattice = np.column_stack((zero_col, lattice, zero_col))
    lattice = lattice.transpose()

    grains = []
    grains_names = []
    for x in range(lattice.shape[0]):
        for y in range(lattice.shape[1]):
            if lattice[x][y] == 1:
                grain =create_grain_ribbon_stl(x, y)
                name = f"grain_{x}_{y}.stl"
                grain.save(name, mode=stl.Mode.ASCII)
                grains_names.append(name)
                grains.append(create_grain_ribbon_stl(x, y))

    # create and save boundary stls
    inlet      = create_boundary_plane_stl(0,     0, 0, 0,     n, 1)
    outlet     = create_boundary_plane_stl(n+2*m, 0, 0, 0,     n, 1)
    wall_up    = create_boundary_plane_stl(0,     n, 0, n+2*m, 0, 1)
    wall_down  = create_boundary_plane_stl(0,     0, 0, n+2*m, 0, 1)
    cover_up   = create_boundary_plane_stl(0,     0, 0, n+2*m, n, 0)
    cover_down = create_boundary_plane_stl(0,     0, 1, n+2*m, n, 0)

    lattice_stl = mesh.Mesh(np.concatenate([g.data for g in grains] + 
                                            [inlet.data] + [outlet.data] + 
                                            [wall_up.data] + [wall_down.data]
                                            ))
    if save_name is not None:
        lattice_stl.save(f"{save_name}.stl", mode=stl.Mode.ASCII)
        inlet.save(      "inlet.stl",        mode=stl.Mode.ASCII)
        outlet.save(     "outlet.stl",       mode=stl.Mode.ASCII)
        wall_up.save(    "wall_up.stl",      mode=stl.Mode.ASCII)
        wall_down.save(  "wall_down.stl",    mode=stl.Mode.ASCII)
        cover_up.save(   "cover_up.stl",     mode=stl.Mode.ASCII)
        cover_down.save( "cover_down.stl",   mode=stl.Mode.ASCII)

    for boundary in ["inlet.stl", "outlet.stl", "wall_up.stl",
                     "wall_down.stl"]:
        os.system(f'cat {boundary} >> col_model.stl')
    for grain in grains_names:
        os.system(f'cat {grain} >> col_model.stl')

    return lattice_stl, grains_names

n = 64
m = 4
import os
name = r"model"
lattice, grains_names = create_lattice_stl(create_random_lattice(0.9,n), save_name=name, n=n, m = m)
os.system(r'rm -r OF_Model/constant/triSurface/*')
os.system(r'mv grain* OF_Model/constant/triSurface')
os.system(r'mv *.stl OF_Model/constant/triSurface')


os.system(r'rm OF_Model/0/p')
os.system(r'touch OF_Model/0/p')
os.system(r'rm OF_Model/0/U')
os.system(r'touch OF_Model/0/U')
p_file = open('OF_Model/0/p','w')
U_file = open('OF_Model/0/U','w')
pic.make_0_U(grains_names, U_file)
pic.make_0_p(grains_names, p_file)

#convert stl to fms:
os.system(r'. /usr/lib/openfoam/openfoam2206/etc/bashrc')
os.system(r'surfaceFeatureEdges OF_Model/constant/triSurface/col_model.stl OF_Model/constant/triSurface/col_model.fms')



