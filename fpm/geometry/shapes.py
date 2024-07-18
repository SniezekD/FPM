import os
import pathlib
from abc import ABC, abstractmethod

import numpy as np
import pyvista as pv


class Shape(ABC):
    @property
    @abstractmethod
    def position(self) -> np.ndarray:
        return self._position

    @position.setter
    @abstractmethod
    def position(self, pos):
        pass

    @abstractmethod
    def type(self) -> str:
        return self._type

    @abstractmethod
    def save_stl(self, destination) -> None:
        pass


class Sphere(Shape):
    def __init__(
        self,
        position: np.ndarray,
        radius: float
    ) -> None:
        self._position = position
        self._type = "sphere"
        self._radius = radius

    @property
    def position(self) -> np.ndarray:
        return self._position

    @property
    def type(self) -> str:
        return self._type

    @property
    def radius(self) -> float:
        return self._radius

    def save_stl(self, destination: pathlib.Path):
        pv_sphere = pv.Sphere(
            radius=self.radius,
            center=self.position,
        )
        try:
            pv_sphere.save(destination)
        except ValueError:
            print("ERROR!: Specified path does not exist!"
                  f"         I was trying to save {self}.")


class Cube(Shape):
    def __init__(
        self,
        position: np.ndarray,
        size: np.ndarray,
        rotation: np.ndarray,
    ) -> None:
        self._position = position
        self._type = "cube"
        self._size = size
        self._rotation = rotation

    @property
    def position(self) -> np.ndarray:
        return self._position

    @property
    def type(self) -> str:
        return self._type

    @property
    def rotation(self) -> float:
        return self._rotation

    @property
    def size(self) -> float:
        return self._size

    def save_stl(self, destination: pathlib.Path):
        min_bounds = list(self.position)
        max_bounds = list(self.position + self.size)
        pv_cube = pv.Cube(
            bounds=min_bounds + max_bounds,
            clean=True,
            point_dtype='float32',
        )
        try:
            pv_cube.save(destination)
        except ValueError:
            print("ERROR!: Specified path does not exist!"
                  f"         I was trying to save {self}.")


class Plane(Shape):
    def __init__(
        self,
        position: np.ndarray,
        size: np.ndarray,
    ) -> None:
        self._position = position
        self._type = "plane"
        self._size = size

    @property
    def position(self) -> np.ndarray:
        return self._position

    @property
    def type(self) -> str:
        return self._type

    @property
    def size(self) -> float:
        return self._size

    def save_stl(self, destination: pathlib.Path):
        if self.size[0] == 0:
            self.normal = (1, 0, 0)
            self.i_size = self.size[2]
            self.j_size = self.size[1]
        elif self.size[1] == 0:
            self.normal = (0, 1, 0)
            self.i_size = self.size[0]
            self.j_size = self.size[2]
        elif self.size[2] == 0:
            self.normal = (0, 0, 1)
            self.i_size = self.size[0]
            self.j_size = self.size[1]

        self.center = [
            self.x + 0.5*self.dx,
            self.y + 0.5*self.dy,
            self.z + 0.5*self.dz,
        ]

        pv_plane = pv.Plane(
            center=self.center,
            direction=self.normal,
            i_size=self.i_size,
            j_size=self.j_size,
            i_resolution=1,
            j_resolution=1
        )
        try:
            pv_plane.save(destination)
        except ValueError:
            print("ERROR!: Specified path does not exist!"
                  f"         I was trying to save {self}.")


class RoundedCube(Shape):
    def __init__(
        self,
        position: np.ndarray,
        size: np.ndarray,
        rotation: np.ndarray,
        rounding_radius: float
    ) -> None:
        self._position = position
        self._type = "reounded cube"
        self._size = size
        self._rotation = rotation
        self._rounding_radius = rounding_radius

    @property
    def position(self) -> np.ndarray:
        return self._position

    @property
    def type(self) -> str:
        return self._type

    @property
    def rotation(self) -> float:
        return self._rotation

    @property
    def size(self) -> float:
        return self._size

    @property
    def rounding_darius(self) -> float:
        return self._rounding_radius

    def save_stl(self, destination: pathlib.Path):
        min_bounds = list(self.position)
        max_bounds = list(self.position + self.size)
        bounding_box = min_bounds + max_bounds

        pv_cube = pv.Box(
            bounds=bounding_box,
            level=19,
            quads=False
        )

        sphere_center = self.position + self.size / 2

        pv_sphere = pv.Sphere(
            self.rounding_radius,
            center=sphere_center,
            theta_resolution=30,
            phi_resolution=30
        )

        rounded_cube = pv_sphere.boolean_intersection(pv_cube)
        try:
            rounded_cube.save(destination)
        except ValueError:
            print("ERROR!: Specified path does not exist!"
                  f"         I was trying to save {self}.")


class Cylinder(Shape):
    def __init__(
        self,
        position: np.ndarray,
        radius: float,
        height: float,
        rotation: np.ndarray,
    ) -> None:
        self._position = position
        self._type = "cylinder"
        self._radius = radius
        self._height = height
        self._rotation = rotation

    @property
    def position(self) -> np.ndarray:
        return self._position

    @property
    def type(self) -> str:
        return self._type

    @property
    def rotation(self) -> float:
        return self._rotation

    @property
    def height(self) -> float:
        return self._height

    @property
    def radius(self) -> float:
        return self._radius

    def save_stl(self, destination: pathlib.Path):
        pv_cylinder = pv.Cylinder(
            center=self.position,
            direction=self.rotation,
            radius=self.radius,
            height=self.height,
        )
        try:
            pv_cylinder.save(destination)
        except ValueError:
            print("ERROR!: Specified path does not exist!"
                  f"         I was trying to save {self}.")
