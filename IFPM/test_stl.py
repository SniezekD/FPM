import numpy as np
from stl import mesh

# Define the 8 vertices of the cube
vertices = np.array([\
    [-1, -1, -1], #0
    [+1, -1, -1], #1
    [+1, +1, -1], #2
    [-1, +1, -1], #3
    [-1, -1, +1], #4
    [+1, -1, +1], #5
    [+1, +1, +1], #6
    [-1, +1, +1]  #7
    ])
# Define the 12 triangles composing the cube
# Delete 4 triangles to obtain a ribbon-like stl for 2D cfMesh
# Commented-out triangles are those which should be deleted
faces = np.array([\
    # [0,3,1],
    # [1,3,2],
    # [0,4,7],
    # [0,7,3],
    # [4,5,6],
    # [4,6,7],
    [5,1,2],
    [5,2,6],
    # [2,3,6],
    # [3,7,6],
    # [0,1,5],
    # [0,5,4]
    ])

# Create the mesh
cube = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
for i, f in enumerate(faces):
    for j in range(3):
        cube.vectors[i][j] = vertices[f[j],:]

# Write the mesh to file "cube.stl"
cube.save('cube.stl')