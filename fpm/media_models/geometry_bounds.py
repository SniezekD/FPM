"""Allowed periodicity modes for porous-media geometry generation."""
from enum import StrEnum


class GeometryBoundsType(StrEnum):
    NON_PERIODIC = "non_periodic"
    PERIODIC_X = "periodic_x"
    PERIODIC_Y = "periodic_y"
    PERIODIC_Z = "periodic_z"
    PERIODIC_XY = "periodic_xy"
    PERIODIC_XZ = "periodic_xz"
    PERIODIC_YZ = "periodic_yz"
    PERIODIC_XYZ = "periodic_xyz"