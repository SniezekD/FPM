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

    @property
    @abstractmethod
    def stl(self) -> pv.PolyData:
        return self.stl

    @abstractmethod
    def to_stl(self) -> pv.PolyData:
        return self._type

    @abstractmethod
    def type(self) -> str:
        return self._type

    @abstractmethod
    def save_stl(self, destination: pathlib.Path, binary: bool = False) -> None:
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
        self._stl = None

    @property
    def position(self) -> np.ndarray:
        return self._position

    @property
    def type(self) -> str:
        return self._type

    @property
    def radius(self) -> float:
        return self._radius

    @property
    def stl(self) -> pv.PolyData:
        return self._stl

    @stl.setter
    def stl(self, obj: pv.PolyData) -> None:
        self._stl = obj

    def to_stl(self):
        if self.stl is not None:
            return self.stl
        else:
            pv_sphere = pv.Sphere(
                    radius=self.radius,
                    center=self.position,
                )
            self.stl = pv_sphere
            return pv_sphere

    def save_stl(self, destination: pathlib.Path, binary: bool = False):
        if self.stl is not None:
            pv_sphere = self.stl
        else:
            pv_sphere = pv.Sphere(
                radius=self.radius,
                center=self.position,
            )

        try:
            pv_sphere.save(destination, binary=binary)
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
        """_summary_

        Args:
            position (np.ndarray): point in 3D cartesian space, center of the
                cube.
            size (np.ndarray): length of each of three sides
            rotation (np.ndarray): rotation vector
        """
        self._position = position
        self._type = "cube"
        self._size = size
        self._rotation = rotation
        self._stl = None

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
    def stl(self) -> pv.PolyData:
        return self._stl

    @stl.setter
    def stl(self, obj: pv.PolyData) -> None:
        self._stl = obj

    def to_stl(self):
        if self.stl is not None:
            return self.stl
        else:
            half_size = self.size / 2
            min_bounds = list(self.position - half_size)
            max_bounds = list(self.position + half_size)
            pv_cube = pv.Cube(
                bounds=[
                    min_bounds[0], max_bounds[0],
                    min_bounds[1], max_bounds[1],
                    min_bounds[2], max_bounds[2]
                ],
                clean=True,
                point_dtype='float32',
            )
            self.stl = pv_cube
            return pv_cube

    def save_stl(self, destination: pathlib.Path, binary: bool = False):
        if self.stl is not None:
            pv_cube = self.stl
        else:
            half_size = self.size / 2
            min_bounds = list(self.position - half_size)
            max_bounds = list(self.position + half_size)
            pv_cube = pv.Cube(
                bounds=min_bounds + max_bounds,
                clean=True,
                point_dtype='float32',
            )

        try:
            pv_cube.save(destination, binary=binary)
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
        self._stl = None

    @property
    def position(self) -> np.ndarray:
        return self._position

    @property
    def type(self) -> str:
        return self._type

    @property
    def size(self) -> float:
        return self._size

    @property
    def stl(self) -> pv.PolyData:
        return self._stl

    @stl.setter
    def stl(self, obj: pv.PolyData) -> None:
        self._stl = obj

    def to_stl(self):
        if self.stl is not None:
            return self.stl
        else:
            if self.size[0] == 0:
                normal = (1, 0, 0)
                i_size = self.size[2]
                j_size = self.size[1]
            elif self.size[1] == 0:
                normal = (0, 1, 0)
                i_size = self.size[0]
                j_size = self.size[2]
            elif self.size[2] == 0:
                normal = (0, 0, 1)
                i_size = self.size[0]
                j_size = self.size[1]

            center = [
                self.position[0] + 0.5*self.size[0],
                self.position[1] + 0.5*self.size[1],
                self.position[2] + 0.5*self.size[2],
            ]

            pv_plane = pv.Plane(
                center=center,
                direction=normal,
                i_size=i_size,
                j_size=j_size,
                i_resolution=1,
                j_resolution=1
            )
            self.stl = pv_plane

            return pv_plane

    def save_stl(self, destination: pathlib.Path, binary: bool = False):
        if self.stl is not None:
            pv_plane = self.stl
        else:
            if self.size[0] == 0:
                normal = (1, 0, 0)
                i_size = self.size[2]
                j_size = self.size[1]
            elif self.size[1] == 0:
                normal = (0, 1, 0)
                i_size = self.size[0]
                j_size = self.size[2]
            elif self.size[2] == 0:
                normal = (0, 0, 1)
                i_size = self.size[0]
                j_size = self.size[1]

            center = [
                self.position[0] + 0.5*self.size[0],
                self.position[1] + 0.5*self.size[1],
                self.position[2] + 0.5*self.size[2],
            ]

            pv_plane = pv.Plane(
                center=center,
                direction=normal,
                i_size=i_size,
                j_size=j_size,
                i_resolution=1,
                j_resolution=1
            )

        try:
            pv_plane.save(destination, binary=binary)
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
        self._type = "RoundedCube"
        self._size = size
        self._rotation = rotation
        self._rounding_radius = rounding_radius
        self._stl = None

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

    @property
    def stl(self) -> pv.PolyData:
        return self._stl

    @stl.setter
    def stl(self, obj: pv.PolyData) -> None:
        self._stl = obj

    def to_stl(self):
        if self.stl is not None:
            return self.stl
        else:
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
            self.stl = rounded_cube
            return rounded_cube

    def save_stl(self, destination: pathlib.Path, binary: bool = False) -> None:
        if self.stl is not None:
            rounded_cube = self.stl
        else:
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
            rounded_cube.save(destination, binary=binary)
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
        self._type = "Cylinder"
        self._radius = radius
        self._height = height
        self._rotation = rotation
        self._stl = None

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

    @property
    def stl(self) -> pv.PolyData:
        return self._stl

    @stl.setter
    def stl(self, obj: pv.PolyData) -> None:
        self._stl = obj

    def to_stl(self):
        if self.stl is not None:
            return self.stl
        else:
            pv_cylinder = pv.Cylinder(
                center=self.position,
                direction=self.rotation,
                radius=self.radius,
                height=self.height,
            )
            self.stl = pv_cylinder
            return pv_cylinder

    def save_stl(self, destination: pathlib.Path, binary: bool = False):
        if self.stl is not None:
            pv_cylinder = self.stl
        else:
            pv_cylinder = pv.Cylinder(
                center=self.position,
                direction=self.rotation,
                radius=self.radius,
                height=self.height,
            )
        try:
            pv_cylinder.save(destination, binary=binary)
        except ValueError:
            print("ERROR!: Specified path does not exist!"
                  f"         I was trying to save {self}.")
