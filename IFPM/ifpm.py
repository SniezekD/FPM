import os
import utils
import pathlib
from typing import List

import numpy as np
import pyvista as pv

import ifpm.mystl as mystl


class IFPM:
    def __init__(
            self,
            porosity: float,
            size: dict,
            in_margin: int,
            out_margin: int,
            working_dir: pathlib.Path,
            r_r: float,
            s_o: bool = False,
            lattice: np.ndarray = None
    ) -> None:
        """Inertial Flow in Porous Media class creator"""
        self.porosity = porosity
        self.size = size
        self.in_margin = in_margin
        self.out_margin = out_margin
        self.wd = working_dir
        self.rounding_r = r_r
        self.save_obs = s_o
        if lattice is None:
            self.lattice = self.porosity_lattice()
        else:
            self.lattice = lattice

        if self.rounding_r <= 0.866 and self.rounding_r > 0.5:

            print(("Creating 3D simulation geometry with "
                   "cubes rounded at the vertices with "
                   f"radius {self.rounding_r} as obstacles."))
        elif self.rounding_r <= 0.5:
            if self.size["z"] == 1:
                print(("Creating 2D simulation geometry with "
                       "cylinders as obstacles."))
            else:
                print(("Creating 3D simulation geometry with "
                       "spheres as obstacles."))
        elif self.rounding_r > 0.866:
            print(("Creating 3D simulation geometry with "
                   "sharp cubes as obstacles."))

        self.stls, self.obstacles_names = self.translate_into_stl()

    def porosity_lattice(self) -> np.ndarray:
        """
        Creates a random lattice with given porosity
        """
        lattice = np.zeros(list(self.size.values()), dtype=int)
        number_of_cells = np.prod(list(self.size.values()))
        number_of_obstacles = int((1 - self.porosity) * number_of_cells)
        if self.rounding_r < 0.5:
            number_of_obstacles *= 6 / np.pi
            number_of_obstacles = int(number_of_obstacles)
            print("Making More spheres than there would be cubes")

        for i in range(number_of_obstacles):
            rnd_x = np.random.randint(self.size['x'])
            rnd_y = np.random.randint(self.size['y'])
            rnd_z = np.random.randint(self.size['z'])
            lattice[rnd_x, rnd_y, rnd_z] = 1

        # ADD MARGINS:
        lattice = np.insert(
            lattice,
            0,
            np.zeros((self.in_margin, self.size['y'], self.size['z'])),

            axis=0
        )
        lattice = np.append(
            lattice,
            np.zeros((self.out_margin, self.size['y'], self.size['z'])),

            axis=0
        )
        lattice = lattice.transpose()

        return lattice

    def translate_into_fms(self):
        """
        Translates 2D geometry into .fms format. If geometry is 3D
        returns False.
        """
        if self.size["z"] == 1:
            for boundary in self.stls.keys():
                if boundary not in ['wall_front', 'wall_back']:
                    os.system(f'cat {boundary}.stl >> col_model.stl')
            return True
        else:
            return False

    def translate_into_stl(self):
        """
        Translates a lattice of zeros and ones into .stl format with
        obstacles of given shape.
        """
        print("    Translating the lattice into stl.")

        inlet = mystl.plane(0, 0, 0, 0, self.size['y'], self.size['z'])
        outlet = mystl.plane(
            self.size['x'] + self.in_margin + self.out_margin,
            0,
            0,
            0,
            self.size['y'],
            self.size['z']
        )
        wall_up = mystl.plane(
            0,
            self.size['y'],
            0,
            self.size['x'] + self.in_margin + self.out_margin,
            0,
            self.size['z']
        )
        wall_down = mystl.plane(
            0,
            0,
            0,
            self.size['x'] + self.in_margin + self.out_margin,
            0,
            self.size['z']
        )
        wall_front = mystl.plane(
            0,
            0,
            0,
            self.size['x'] + self.in_margin + self.out_margin,
            self.size['y'],
            0
        )
        wall_back = mystl.plane(
            0,
            0,
            self.size['z'],
            self.size['x'] + self.in_margin + self.out_margin,
            self.size['y'],
            0
        )

        obstacles = []
        obstacles_names = []

        grain_positions = np.argwhere(self.lattice == 1)
        for z, y, x in grain_positions:
            if self.lattice[z, y, x] == 1:
                if self.rounding_r > 0.866:
                    # if the case is 2D
                    if self.size["z"] == 1:
                        tmp_obstacle = mystl.ribbon(x, y, z)
                    else:
                        tmp_obstacle = mystl.cube(x, y, z)

                elif self.rounding_r <= 0.5:
                    # if the case is 2D:
                    if self.size["z"] == 1:
                        tmp_obstacle = mystl.cylinder(x, y, z)
                    else:
                        tmp_obstacle = mystl.sphere(x, y, z)
                else:
                    tmp_obstacle = mystl.rounded_cube(x, y, z, self.rounding_r)

                obstacles_names.append(tmp_obstacle.get_name())
                obstacles.append(tmp_obstacle.stl)

        obstacles_stl = obstacles[0]
        if self.save_obs:
            print("      Saving separate obstacles")
            for obs, obs_name in zip(obstacles, obstacles_names):
                obs.save(f"{obs_name}")

        for obs in obstacles[1:]:
            obstacles_stl = obstacles_stl.merge(obs)
        obstacles_stl = mystl.collective_grains(obstacles_stl)

        stls = {'inlet': inlet,
                'outlet': outlet,
                'wall_up': wall_up,
                'wall_down': wall_down,
                'wall_front': wall_front,
                'wall_back': wall_back,
                'grains': obstacles_stl}

        print("Lattice translated into stl")

        return stls, obstacles_names

    def prepare_model(self, ) -> None:
        print("    Preparing model")
        for stl_name in self.stls.keys():
            save_path = f"/home/user/MGR/IFPM/{stl_name}.stl"
            self.stls[stl_name].save(save_path)
        if self.size["z"] == 1:

            print("     Translating geometry into .fms format")
            self.translate_into_fms()

            utils.createMeshDict(
                self.wd.joinpath(
                    'OF_Model',
                    'system',
                    'meshDict'
                )
            )

        else:
            utils.createBlockMeshDict(
                self.wd.joinpath(
                    'OF_Model',
                    'system',
                    'blockMeshDict'
                ),
                self.size,
                self.in_margin,
                self.out_margin

            )
            utils.createSnappyHexMeshDict(
                self.wd.joinpath(
                    'OF_Model',
                    'system',
                    'snappyHexMeshDict'
                )
            )
        utils.run_cmd([r'./prep_model.sh'])

    def run_meshing(self) -> None:
        """
        Runs OpenFOAM meshing commands.
        Mesh is done with snappyHexMesh tool.
        """
        if self.size["z"] == 1:
            print("    Creating the mesh with cfMesh")
            utils.run_cmd([r'./run_meshing2D.sh'])
        else:
            print("    Creating the mesh with snappyHexMesh")
            utils.run_cmd([r'./run_meshing.sh'])

    def prepare_initial_conditions(self, Re: float) -> None:
        print("    Preparing Initial Conditions")

        U_file = self.wd.joinpath('OF_Model', '0', 'U')
        p_file = self.wd.joinpath('OF_Model', '0', 'p')
        utils.make_0_U(U_file, self.size, Re)
        utils.make_0_p(p_file, self.size)

    def run_single_simulation(self, Re: float, n_par: int = 6) -> None:
        """
        Runs SimpeFoam (an OpenFOAM solver) with parellisation
        into n_par processors. Setting the value of n_par into
        a value differnet than 6 (default) requires changes inside
        'decomposeParDict' inside OF case directory.
        """
        print("    Running the Simulation")
        utils.run_cmd([r'./run_simpleFoam.sh', f'{Re:0.4f}'])

    def save_as_VTK(self) -> None:
        print("    Saving results in VTK format")

    def prep_convergence(self, Re: float) -> None:
        print("    Running foamLog")
        utils.run_cmd([r'./calc_convergence.sh', f'{Re:0.4f}'])


class Point:
    def __init__(self, x: float, y: float, z: float = 0) -> None:
        self.x = x
        self.y = y
        self.z = z

    def move(self, dx: float, dy: float, dz: float):
        new_x = self.x + dx
        new_y = self.y + dy
        new_z = self.z + dz

        return Point(new_x, new_y, new_z)

    def position(self):
        return np.array([self.x, self.y, self.z])

    def calc_dist(self, pt):
        return np.linalg.norm(self.position() - pt.position())

    def __str__(self) -> str:
        return f"[{self.x}, {self.y}, {self.z}]"


def get_points_from_diagonal_points(pt1: Point, pt2: Point):
    """
    This function calculates the position of all square
    of cube vertices when the diagonal points are given.
    """
    x_coords = [pt1.x, pt2.x]
    y_coords = [pt1.y, pt2.y]
    z_coords = [pt1.z, pt2.z]

    points = []
    for x in x_coords:
        for y in y_coords:
            if z_coords[0] != z_coords[1]:
                for z in z_coords:
                    tmp_pt = Point(x, y, z)
                    points.append(tmp_pt)
            else:
                tmp_pt = Point(x, y)
                points.append(tmp_pt)
    return points


class FractalIFPM(IFPM):
    def __init__(
            self,
            fractal_level: int,
            size: dict,
            working_dir: pathlib.Path,
            in_margin: int,
            out_margin: int,
            s_o: bool = False
    ) -> None:

        self.f_level = fractal_level
        self.sys_size = size["x"]
        self.wd = working_dir
        self.obstacles = []
        self.size = size
        self.in_margin = in_margin
        self.out_margin = out_margin

        if self.size["z"] == 1:
            self.points = [
                Point(0, 0),
                Point(0, self.sys_size),
                Point(self.sys_size, 0),
                Point(self.sys_size, self.sys_size)
            ]
        else:
            self.points = [
                Point(0, 0, 0),
                Point(0, self.sys_size, 0),
                Point(self.sys_size, 0, 0),
                Point(self.sys_size, self.sys_size, 0),
                Point(0, 0, self.sys_size),
                Point(0, self.sys_size, self.sys_size),
                Point(self.sys_size, 0, self.sys_size),
                Point(self.sys_size, self.sys_size, self.sys_size)
            ]

        self.create_carpet(self.f_level, self.points)

        super().__init__(
            0,
            size,
            in_margin,
            out_margin,
            working_dir,
            0,
            s_o
        )

        self.stls, self.obstacles_names = self.translate_into_stl()

    def single_sierp(self, points_list: List[Point]):
        """
        This preforms a single iteration of making a Sierpiński carpet in 2D
        or 3D. This means, that the edges of the initial
        square's (2D) or cube's (3D) edge is divided into 3 pieces.
        That means that the intial figure is divided into 9 and 27 pieces
        for 2D and 3D respectively. The function returns a ribbon (2D) or
        cube (3D) that should be cut out of the initial geometry.
        """

        z_coords = [pt.z for pt in points_list]
        unique_z_coords = set(z_coords)

        if len(unique_z_coords) != 0:
            dimension = 3
        else:
            dimension = 2

        up_left_point = points_list[0].position()
        edge_len = points_list[0].calc_dist(points_list[1]) / 3

        if dimension == 2:
            # 2D case
            cutout = mystl.ribbon(
                i=up_left_point[0] + edge_len + self.in_margin,
                j=up_left_point[1] + edge_len,
                d_i=edge_len,
                d_j=edge_len
            )

        elif dimension == 3:
            cutout = mystl.cube(
                i=up_left_point[0] + edge_len + self.in_margin,
                j=up_left_point[1] + edge_len,
                k=up_left_point[2] + edge_len,
                d_i=edge_len,
                d_j=edge_len,
                d_k=edge_len
            )

        else:
            cutout = None

        return cutout

    def create_carpet(self, i: int, points_list: List[Point]) -> None:
        if i > 0:
            squares = []
            a_point = points_list[0]
            dist = a_point.calc_dist(points_list[1]) / 3
            for n in range(3):
                for m in range(3):
                    if self.size["z"] == 1:
                        squares.append(get_points_from_diagonal_points(
                            a_point.move(n*dist, m*dist, 0),
                            a_point.move((n+1)*dist, (m+1)*dist, 0)
                        ))
                    else:
                        for k in range(3):
                            squares.append(get_points_from_diagonal_points(
                                a_point.move(n*dist, m*dist, k*dist),
                                a_point.move(
                                    (n + 1) * dist,
                                    (m + 1) * dist,
                                    (k + 1) * dist
                                )
                            ))
            for square in squares:
                self.create_carpet(i-1, square)

            pt_list = [pt for pt in points_list]
            cutout = self.single_sierp(pt_list)

            self.obstacles.append(cutout)

    def translate_into_fms(self):
        """
        Translates 2D geometry into .fms format.
        If geometry is 3D returns False.
        """
        if self.size["z"] == 1:
            for boundary in self.stls.keys():
                if boundary not in ['wall_front', 'wall_back']:
                    os.system(f'cat {boundary}.stl >> col_model.stl')
            return True
        else:
            return False

    def translate_into_stl(self):
        """
        Translates a lattice of zeros and ones into .stl format with
        obstacles of given shape.
        """
        print("    Translating the lattice into stl.")

        inlet = mystl.plane(0, 0, 0, 0, self.size['y'], self.size['z'])
        outlet = mystl.plane(
            self.size['x'] + self.in_margin + self.out_margin,
            0,
            0,
            0,
            self.size['y'],
            self.size['z']
        )
        wall_up = mystl.plane(
            0,
            self.size['y'],
            0,
            self.size['x'] + self.in_margin + self.out_margin,
            0,
            self.size['z']
        )
        wall_down = mystl.plane(
            0,
            0,
            0,
            self.size['x'] + self.in_margin + self.out_margin,
            0,
            self.size['z']
        )
        wall_front = mystl.plane(
            0,
            0,
            0,
            self.size['x'] + self.in_margin + self.out_margin,
            self.size['y'],
            0
        )
        wall_back = mystl.plane(
            0,
            0,
            self.size['z'],
            self.size['x'] + self.in_margin + self.out_margin,
            self.size['y'],
            0
        )

        obstacles = [obstacle.stl for obstacle in self.obstacles]
        obstacles_names = [obstacle.get_name() for obstacle in self.obstacles]

        if self.save_obs:
            print("      Saving separate obstacles")
            for obs, obs_name in zip(obstacles, obstacles_names):
                obs.save(f"{obs_name}")

        obstacles_stl = obstacles[0]
        for obs in obstacles[1:]:
            obstacles_stl = obstacles_stl.merge(obs)
        obstacles_stl = mystl.collective_grains(obstacles_stl)

        stls = {'inlet': inlet,
                'outlet': outlet,
                'wall_up': wall_up,
                'wall_down': wall_down,
                'wall_front': wall_front,
                'wall_back': wall_back,
                'grains': obstacles_stl}

        print("Lattice translated into stl")

        return stls, obstacles_names
