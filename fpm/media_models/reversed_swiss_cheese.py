import pyvista as pv
import numpy as np
import fpm.geometry.shapes as shapes
from fpm.media_models.porous_medium import porousMedium


class ReversedSwissCheese(porousMedium):
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
        max_radius: float
    ) -> None:
        self.porosity = porosity
        self.bounds = bounds
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.walls = None

    def create_walls(self):
        """Create walls that will be used as geometrical
        boundaries to the model.
        """
        upper_wall = shapes.Plane(
            i=self.bounds[0],
            j=self.bounds[3],
            k=self.bounds[4],
            d_i=self.bounds[1] - self.bounds[0],
            d_j=0,
            d_k=self.bounds[5] - self.bounds[4]
        )

        lower_wall = shapes.Plane(
            i=self.bounds[0],
            j=self.bounds[2],
            k=self.bounds[4],
            d_i=self.bounds[1] - self.bounds[0],
            d_j=0,
            d_k=self.bounds[5] - self.bounds[4]
        )

        right_wall = shapes.Plane(
            i=self.bounds[1],
            j=self.bounds[2],
            k=self.bounds[4],
            d_i=0,
            d_j=self.bounds[3] - self.bounds[2],
            d_k=self.bounds[5] - self.bounds[4]
        )

        left_wall = shapes.Plane(
            i=self.bounds[0],
            j=self.bounds[2],
            k=self.bounds[4],
            d_i=0,
            d_j=self.bounds[3] - self.bounds[2],
            d_k=self.bounds[5] - self.bounds[4]
        )

        front_wall = shapes.Plane(
            i=self.bounds[0],
            j=self.bounds[2],
            k=self.bounds[5],
            d_i=self.bounds[1] - self.bounds[0],
            d_j=self.bounds[3] - self.bounds[2],
            d_k=0
        )

        back_wall = shapes.Plane(
            i=self.bounds[0],
            j=self.bounds[2],
            k=self.bounds[4],
            d_i=self.bounds[1] - self.bounds[0],
            d_j=self.bounds[3] - self.bounds[2],
            d_k=0
        )

        walls = {
            "upper": upper_wall,
            "lower": lower_wall,
            "right": right_wall,
            "left": left_wall,
            "front": front_wall,
            "back": back_wall,
        }

        return walls

    def create_obstacles(self, geometry_bounds_type: str):
        """Create set of obstacles inside boundaries.
        The obstacles are spheres with random radii placed in
        random positions. If geometr boundary conditions are
        set as periodic in any direction, then if an obstacle
        collides with a wall then a copy of it would be created
        to reflect those geometrical boundary condition.
        """
        if geometry_bounds_type not in self.GEOMETRY_BOUNDARY_CONDITIONS:
            raise ValueError("Possible types of geometry boundary conditions "
                             f"are: {self.GEOMETRY_BOUNDARY_CONDITIONS}")

        if self.walls is None:
            self.walls = self.create_walls()

        obstacles = []
        bounds_volume = (
            (self.bounds[1] - self.bounds[0])
            * (self.bounds[3] - self.bounds[2])
            * (self.bounds[5] - self.bounds[4])
        )
        tmp_porosity = 1.0
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
                i=x_pos,
                j=y_pos,
                k=z_pos,
                diameter=2*radius
            )
            if geometry_bounds_type == 'non_periodic':
                obstacles.append(tmp_sphere)

            elif geometry_bounds_type == 'periodic_x':
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

            elif geometry_bounds_type == 'periodic_y':
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

            elif geometry_bounds_type == 'periodic_z':
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

            elif geometry_bounds_type == 'periodic_xy':
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
                            if j ==i:
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

            elif geometry_bounds_type == 'periodic_xz':
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

            elif geometry_bounds_type == 'periodic_yz':
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

            elif geometry_bounds_type == 'periodic_xyz':
                walls_of_interest = [
                    self.walls['upper'], self.walls['lower'],
                    self.walls['upper'], self.walls['lower'],
                    self.walls['front'], self.walls['back']
                ]
                translation_vectors = [
                    [-(self.bounds[1] - self.bounds[0]),0, 0],
                    [(self.bounds[1] - self.bounds[0]),0, 0],
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

            # Update porosity
            tmp_stls = [o.stl for o in obstacles]
            tmp_collective_obstacles = pv.MultiBlock(tmp_stls).combine()
            tmp_porosity = (
                1.0 - tmp_collective_obstacles.volume / bounds_volume
            )
