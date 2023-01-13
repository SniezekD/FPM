import os
import stl
import random
import numpy as np

from stl import mesh

def create_random_lattice3D(epsilon, n):
    '''
    Returns a random 3D lattice with 0 as free space and 1 as obstacle. 
    '''
    mat = np.random.random((n,n,n)) # 3D lattice
    for i in range(int((1-epsilon)*n**3)):
        rand_x = random.randint(0, n-1)
        rand_y = random.randint(0, n-1)
        rand_z = random.randint(0, n-1)
        mat[rand_x][rand_y][rand_z] = 1
    return mat

def create_grain_stl(i:float, j:float, k: float = 0.0,
                     d_i:float=1.0, d_j:float=1.0, d_k:float = 1.0):
    """_summary_

    Args:
        i (float): minimum X-axis coordinate
        j (float): minimum Y-axis coordinate
        k (float): minimum Z-axis coordinate. Defaults to 0.
        d_i (float, optional): length in X direction. Defaults to 1.0.
        d_j (float, optional): length in X direction. Defaults to 1.0.
        d_k (float, optional): lenght in Z direction. Defaults to 1.0.

    Returns:
        stl_object: aa cuboid with 6 faces
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
        [0,4,1],
        [1,4,5]])

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

def create_lattice_stl(epsilon: float , save_name : str = None, n : int = 64, m: int = 4) -> mesh.Mesh:
    '''
    Converts a given lattice into a stl file.
    '''
    # Firstly, lets concateate m nxn matrices at the beginning and at the end
    # The columns will have only 0 elements
    lattice = create_random_lattice3D(epsilon, n)
    lattice = np.insert(lattice, 0, np.zeros((m,n,n)), axis=0)
    lattice = np.append(lattice,    np.zeros((m,n,n)), axis=0)


    grains = []
    grains_names = []
    for x in range(lattice.shape[0]):
        for y in range(lattice.shape[1]):
            for z in range(lattice.shape[2]):
                if lattice[x][y][z] == 1:
                    grain = create_grain_stl(x, y, z)
                    name  = f"grain_{x}_{y}_{z}.stl"
                    grain.save(name, mode=stl.Mode.ASCII)
                    grains_names.append(name)
                    grains.append(create_grain_stl(x, y, z))

    # create and save boundary stls
    inlet      = create_boundary_plane_stl(0,     0, 0, 0,     n, n)
    outlet     = create_boundary_plane_stl(n+2*m, 0, 0, 0,     n, n)
    wall_up    = create_boundary_plane_stl(0,     n, 0, n+2*m, 0, n)
    wall_down  = create_boundary_plane_stl(0,     0, 0, n+2*m, 0, n)
    cover_up   = create_boundary_plane_stl(0,     0, 0, n+2*m, n, 0)
    cover_down = create_boundary_plane_stl(0,     0, n, n+2*m, n, 0)

    lattice_stl = mesh.Mesh(np.concatenate([g.data for g in grains] + 
                                            [inlet.data] + [outlet.data] + 
                                            [wall_up.data] + [wall_down.data] +
                                            [cover_up.data] + [cover_down.data]
                                            ))
    if save_name is not None:
        lattice_stl.save(f"{save_name}.stl", mode=stl.Mode.ASCII)
        inlet.save(      "inlet.stl",        mode=stl.Mode.ASCII)
        outlet.save(     "outlet.stl",       mode=stl.Mode.ASCII)
        wall_up.save(    "wall_up.stl",      mode=stl.Mode.ASCII)
        wall_down.save(  "wall_down.stl",    mode=stl.Mode.ASCII)
        cover_up.save(   "cover_up.stl",     mode=stl.Mode.ASCII)
        cover_down.save( "cover_down.stl",   mode=stl.Mode.ASCII)

    # for boundary in ["inlet.stl", "outlet.stl", "wall_up.stl",
                    #  "wall_down.stl", "cover_up.stl", "cover_down.stl"]:
        # os.system(f'cat {boundary} >> col_model.stl')
    # for grain in grains_names:
        # os.system(f'cat {grain} >> col_model.stl')
    for grain in grains_names:
        os.system(f'cat {grain} >> grains.stl')

    return lattice_stl, grains_names
