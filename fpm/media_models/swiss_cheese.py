import pathlib

import pyvista as pv
import numpy as np
import pandas as pd

import fpm.geometry.shapes as shapes
from fpm.media_models.porous_medium import PorousMedium
from fpm.utilities.calculate_porosity import calculate_porosity


class SwissCheese(PorousMedium):
    GEOMETRY_BOUNDARY_CONDITIONS = [
        'periodic_xyz',
        'periodic_xy',
        'periodic_xz',
        'periodic_yz',
        'periodic_x',
        'periodic_y',
        'periodic_z',
        'non_periodic'
    ]

    def __init__(
        self,
        porosity: float,
        bounds: list,
        min_radius: float,
        max_radius: float,
        geometry_bounds_type: str
    ) -> None:
        """Crate a swissCheese porous medium object.
        The obstacles are modelled as spheres with random radii that are
        choosen from uniform distribution between given minimum and maximum
        values.

        Args:
            porosity (float): Desired porosity of the medium.
            bounds (list): bounding box coordinates
                    [x_min, x_max, y_min, y_max, z_min, z_max].
            min_radius (float): Minimal obstacle radius.
            max_radius (float): Maximal obstacle radius.
        """
        if geometry_bounds_type not in self.GEOMETRY_BOUNDARY_CONDITIONS:
            raise ValueError("Possible types of geometry boundary conditions "
                             f"are: {self.GEOMETRY_BOUNDARY_CONDITIONS}")

        self.porosity = porosity
        self.bounds = bounds
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.walls = None
        self.obstacles = None
        self.geometry_bounds_type = geometry_bounds_type

    def create_boundary_walls(self):
        """Create walls that will be used as geometrical
        boundaries to the model.
        """
        upper_wall = shapes.Plane(
            position=[self.bounds[0], self.bounds[3], self.bounds[4]],
            size=[
                self.bounds[1] - self.bounds[0],
                0,
                self.bounds[5] - self.bounds[4]
            ]
        )

        lower_wall = shapes.Plane(
            position=[self.bounds[0], self.bounds[2], self.bounds[4]],
            size=[
                self.bounds[1] - self.bounds[0],
                0,
                self.bounds[5] - self.bounds[4]
            ]
        )

        right_wall = shapes.Plane(
            position=[self.bounds[1], self.bounds[2], self.bounds[4]],
            size=[
                0,
                self.bounds[3] - self.bounds[2],
                self.bounds[5] - self.bounds[4]
            ]
        )

        left_wall = shapes.Plane(
            position=[self.bounds[0], self.bounds[2], self.bounds[4]],
            size=[
                0,
                self.bounds[3] - self.bounds[2],
                self.bounds[5] - self.bounds[4]
            ]
        )

        front_wall = shapes.Plane(
            position=[self.bounds[0], self.bounds[2], self.bounds[5]],
            size=[
                self.bounds[1] - self.bounds[0],
                self.bounds[3] - self.bounds[2],
                0
            ]
        )

        back_wall = shapes.Plane(
            position=[self.bounds[0], self.bounds[2], self.bounds[4]],
            size=[
                self.bounds[1] - self.bounds[0],
                self.bounds[3] - self.bounds[2],
                0
            ]
        )

        walls = {
            "porous_medium_wall_up": upper_wall,
            "porous_medium_wall_down": lower_wall,
            "porous_medium_wall_right": right_wall,
            "porous_medium_wall_left": left_wall,
            "porous_medium_wall_front": front_wall,
            "porous_medium_wall_back": back_wall,
        }

        return walls

    def create_obstacles(self):
        """Create set of obstacles inside boundaries.
        The obstacles are spheres with random radii placed in
        random positions. If geometr boundary conditions are
        set as periodic in any direction, then if an obstacle
        collides with a wall then a copy of it would be created
        to reflect those geometrical boundary condition.
        """

        if self.walls is None:
            self.walls = self.create_boundary_walls()

        obstacles = []
        bounds_volume = (
            (self.bounds[1] - self.bounds[0])
            * (self.bounds[3] - self.bounds[2])
            * (self.bounds[5] - self.bounds[4])
        )
        print(bounds_volume)
        tmp_porosity = 1.0
        saved_state_for_porosity = None
        while tmp_porosity > self.porosity:
            x_pos = np.random.uniform(
                low=self.bounds[0],
                high=self.bounds[1]
            )
            y_pos = np.random.uniform(
                low=self.bounds[2],
                high=self.bounds[3]
            )
            z_pos = np.random.uniform(
                low=self.bounds[4],
                high=self.bounds[5]
            )
            radius = np.random.uniform(
                low=self.min_radius,
                high=self.max_radius
            )

            tmp_sphere = shapes.Sphere(
                position=[x_pos, y_pos, z_pos],
                radius=radius
            )
            if self.geometry_bounds_type == 'non_periodic':
                # print(f"sphere volume {tmp_sphere.to_stl().volume}")
                obstacles.append(tmp_sphere)

            elif self.geometry_bounds_type == 'periodic_x':
                walls_of_interest = [self.walls['right'], self.walls['left']]
                translation_vectors = [
                    [-(self.bounds[1] - self.bounds[0]), 0, 0],
                    [(self.bounds[1] - self.bounds[0]), 0, 0]
                ]
                n_collision_cells = [
                    tmp_sphere.stl.collision(w)[1] for w in walls_of_interest
                ]
                for i, n_coll_i in enumerate(n_collision_cells):
                    if n_coll_i != 0:
                        translated_tmp_sphere = tmp_sphere.translate(
                            translation_vector=translation_vectors[i]
                        )
                        obstacles.append(translated_tmp_sphere)

            elif self.geometry_bounds_type == 'periodic_y':
                walls_of_interest = [self.walls['upper'], self.walls['lower']]
                translation_vectors = [
                    [0, -(self.bounds[3] - self.bounds[2]), 0],
                    [0, (self.bounds[3] - self.bounds[2]), 0]
                ]
                n_collision_cells = [
                    tmp_sphere.stl.collision(w)[1] for w in walls_of_interest
                ]
                for j, n_coll_j in enumerate(n_collision_cells):
                    if n_coll_j != 0:
                        translated_tmp_sphere = tmp_sphere.translate(
                            translation_vector=translation_vectors[j]
                        )
                        obstacles.append(translated_tmp_sphere)

            elif self.geometry_bounds_type == 'periodic_z':
                walls_of_interest = [self.walls['front'], self.walls['back']]
                translation_vectors = [
                    [0, 0, -(self.bounds[5] - self.bounds[4])],
                    [0, 0, (self.bounds[5] - self.bounds[4])]
                ]
                n_collision_cells = [
                    tmp_sphere.stl.collision(w)[1] for w in walls_of_interest
                ]
                for k, n_coll_k in enumerate(n_collision_cells):
                    if n_coll_k != 0:
                        translated_tmp_sphere = tmp_sphere.translate(
                            translation_vector=translation_vectors[k]
                        )
                        obstacles.append(translated_tmp_sphere)

            elif self.geometry_bounds_type == 'periodic_xy':
                walls_of_interest = [
                    self.walls['right'], self.walls['left'],
                    self.walls['upper'], self.walls['lower']
                ]
                translation_vectors = [
                    [-(self.bounds[1] - self.bounds[0]), 0, 0],
                    [(self.bounds[1] - self.bounds[0]), 0, 0],
                    [0, -(self.bounds[3] - self.bounds[2]), 0],
                    [0, (self.bounds[3] - self.bounds[2]), 0]
                ]
                n_collision_cells = [
                    tmp_sphere.stl.collision(w)[1] for w in walls_of_interest
                ]
                for i, n_coll_i in enumerate(n_collision_cells):
                    if n_coll_i != 0:
                        translated_tmp_sphere = tmp_sphere.translate(
                            translation_vector=translation_vectors[i]
                        )
                        obstacles.append(translated_tmp_sphere)
                        for j, n_coll_j in enumerate(n_collision_cells):
                            if j == i:
                                continue
                            if n_coll_j != 0:
                                trans_vec = (
                                    np.array(translation_vectors[i])
                                    + np.array(translation_vectors[j])
                                )
                                translated_tmp_sphere = tmp_sphere.translate(
                                    translation_vector=trans_vec
                                )
                                obstacles.append(translated_tmp_sphere)

            elif self.geometry_bounds_type == 'periodic_xz':
                walls_of_interest = [
                    self.walls['right'], self.walls['left'],
                    self.walls['front'], self.walls['back']
                ]
                translation_vectors = [
                    [-(self.bounds[1] - self.bounds[0]), 0, 0],
                    [(self.bounds[1] - self.bounds[0]), 0, 0],
                    [0, 0, -(self.bounds[5] - self.bounds[4])],
                    [0, 0, (self.bounds[5] - self.bounds[4])]
                ]
                n_collision_cells = [
                    tmp_sphere.stl.collision(w)[1] for w in walls_of_interest
                ]
                for i, n_coll_i in enumerate(n_collision_cells):
                    if n_coll_i != 0:
                        translated_tmp_sphere = tmp_sphere.translate(
                            translation_vector=translation_vectors[i]
                        )
                        obstacles.append(translated_tmp_sphere)
                        for k, n_coll_k in enumerate(n_collision_cells):
                            if k == i:
                                continue
                            if n_coll_k != 0:
                                trans_vec = (
                                    np.array(translation_vectors[i])
                                    + np.array(translation_vectors[k])
                                )
                                translated_tmp_sphere = tmp_sphere.translate(
                                    translation_vector=trans_vec
                                )
                                obstacles.append(translated_tmp_sphere)

            elif self.geometry_bounds_type == 'periodic_yz':
                walls_of_interest = [
                    self.walls['upper'], self.walls['lower'],
                    self.walls['front'], self.walls['back']
                ]
                translation_vectors = [
                    [0, -(self.bounds[3] - self.bounds[2]), 0],
                    [0, (self.bounds[3] - self.bounds[2]), 0],
                    [0, 0, -(self.bounds[5] - self.bounds[4])],
                    [0, 0, (self.bounds[5] - self.bounds[4])]
                ]
                n_collision_cells = [
                    tmp_sphere.stl.collision(w)[1] for w in walls_of_interest
                ]
                for j, n_coll_j in enumerate(n_collision_cells):
                    if n_coll_j != 0:
                        translated_tmp_sphere = tmp_sphere.translate(
                            translation_vector=translation_vectors[j]
                        )
                        obstacles.append(translated_tmp_sphere)
                        for k, n_coll_k in enumerate(n_collision_cells):
                            if k == j:
                                continue
                            if n_coll_k != 0:
                                trans_vec = (
                                    np.array(translation_vectors[j])
                                    + np.array(translation_vectors[k])
                                )
                                translated_tmp_sphere = tmp_sphere.translate(
                                    translation_vector=trans_vec
                                )
                                obstacles.append(translated_tmp_sphere)

            elif self.geometry_bounds_type == 'periodic_xyz':
                walls_of_interest = [
                    self.walls['upper'], self.walls['lower'],
                    self.walls['upper'], self.walls['lower'],
                    self.walls['front'], self.walls['back']
                ]
                translation_vectors = [
                    [-(self.bounds[1] - self.bounds[0]), 0, 0],
                    [(self.bounds[1] - self.bounds[0]), 0, 0],
                    [0, -(self.bounds[3] - self.bounds[2]), 0],
                    [0, (self.bounds[3] - self.bounds[2]), 0],
                    [0, 0, -(self.bounds[5] - self.bounds[4])],
                    [0, 0, (self.bounds[5] - self.bounds[4])]
                ]
                n_collision_cells = [
                    tmp_sphere.stl.collision(w)[1] for w in walls_of_interest
                ]
                for i, n_coll_i in enumerate(n_collision_cells):
                    if n_coll_i != 0:
                        translated_tmp_sphere = tmp_sphere.translate(
                            translation_vector=translation_vectors[i]
                        )
                        obstacles.append(translated_tmp_sphere)
                        for j, n_coll_j in enumerate(n_collision_cells):
                            if j == i:
                                continue
                            if n_coll_j != 0:
                                trans_vec = (
                                    np.array(translation_vectors[i])
                                    + np.array(translation_vectors[j])
                                )
                                translated_tmp_sphere = tmp_sphere.translate(
                                    translation_vector=trans_vec
                                )
                                obstacles.append(translated_tmp_sphere)
                                for k, n_coll_k in enumerate(
                                    n_collision_cells
                                ):
                                    if k in (j, i):
                                        continue
                                    if n_coll_k != 0:
                                        trans_vec = (
                                            np.array(translation_vectors[i])
                                            + np.array(translation_vectors[j])
                                            + np.array(translation_vectors[k])
                                        )
                                        translated_tmp_sphere = \
                                            tmp_sphere.translate(
                                                translation_vector=trans_vec
                                            )
                                        obstacles.append(translated_tmp_sphere)

            tmp_porosity, saved_state_for_porosity = calculate_porosity(
                porous_medium=self,
                obstacles=obstacles,
                discretization=(100, 100, 100),
                saved_state=saved_state_for_porosity
            )
        return obstacles

    def save_stls(self, savepath: pathlib.Path) -> None:
        savepath.mkdir(parents=True, exist_ok=True)

        if self.walls is not None:
            for name, o in self.walls.items():
                dest = savepath / f"{name}.stl"
                o.save_stl(destination=dest, binary=False)

        if self.obstacles is not None:
            dest = savepath / "obstacles.stl"
            all_obstacles = pv.merge([o.to_stl() for o in self.obstacles])
            all_obstacles.save(dest, binary=False)

    def save_spec_to_file(
        self,
        savepath: pathlib.Path,
    ) -> None:
        data_dict = {
            'porosity': [self.porosity],
            'x_min': [self.bounds[0]],
            'x_max': [self.bounds[1]],
            'y_min': [self.bounds[2]],
            'y_max': [self.bounds[3]],
            'z_min': [self.bounds[4]],
            'z_max': [self.bounds[5]],
            'min_radius': [self.min_radius],
            'max_radius': [self.max_radius],
            'geometry_bounds_type': [self.geometry_bounds_type]
        }

        df = pd.DataFrame.from_dict(data_dict)
        df.to_csv(savepath, index=False)
