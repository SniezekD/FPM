from dataclasses import dataclass, fields
from typing import Any
import pathlib
import tomllib

from fpm.media_models.geometry_bounds import GeometryPeriodicityType


class ConfigError(Exception):
    """Missing keys, wrong types, or invariant violations in a config file."""


VALID_BC_TYPES = {"fixedValue", "zeroGradient", "noSlip"}
FACES = ("left", "right", "up", "down", "front", "back", "obstacles")


def _require(table: dict, path: str, expected, *, filename: str) -> Any:
    """Fetch a required key by dotted path, or raise ConfigError naming it."""
    node = table
    for i, segment in enumerate(path.split(".")):
        if not isinstance(node, dict) or segment not in node:
            missing = ".".join(path.split(".")[: i + 1])
            raise ConfigError(f"{filename}: missing required key '{missing}'")
        node = node[segment]
    if not isinstance(node, expected):
        raise ConfigError(
            f"{filename}: key '{path}' must be {expected}, got {type(node).__name__}"
        )
    return node


def _optional(table: dict, path: str, expected, *, filename: str, default=None) -> Any:
    """Like _require, but returns `default` when the key is absent."""
    node = table
    for segment in path.split("."):
        if not isinstance(node, dict) or segment not in node:
            return default
        node = node[segment]
    if not isinstance(node, expected):
        raise ConfigError(
            f"{filename}: key '{path}' must be {expected}, got {type(node).__name__}"
        )
    return node


def _exact_table(table: dict, path: str, cls_, *, filename: str) -> dict:
    d = _require(table, path, dict, filename=filename)
    expected = {f.name for f in fields(cls_)}
    missing = sorted(expected - d.keys())
    extra = sorted(d.keys() - expected)
    if missing or extra:
        raise ConfigError(
            f"{filename}: table '{path}' has wrong keys; "
            f"missing={missing}, unexpected={extra}"
        )
    return d


def _normalize_none(value) -> Any:
    """Collapse the TOML sentinel string 'none' (any case) to Python None."""
    if value is None or (isinstance(value, str) and value.lower() == "none"):
        return None
    return value


@dataclass(frozen=True)
class ControlDict:
    end_time: float
    time_step: float
    solver_name: str
    write_interval: float

    def __post_init__(self):
        if self.end_time <= 0 or self.time_step <= 0 or self.write_interval <= 0:
            raise ConfigError(
                "controlDict: end_time, time_step, write_interval must be > 0"
            )


@dataclass(frozen=True)
class Parallelism:
    number_of_procs: int
    decompose_method: str | None

    def __post_init__(self):
        if self.number_of_procs < 1:
            raise ConfigError("parallelism.number_of_procs must be >= 1")


@dataclass(frozen=True)
class BoundingBox:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float

    def __post_init__(self):
        for lo, hi, ax in (
            (self.x_min, self.x_max, "x"),
            (self.y_min, self.y_max, "y"),
            (self.z_min, self.z_max, "z"),
        ):
            if lo >= hi:
                raise ConfigError(
                    f"boundingBox: {ax}_min ({lo}) must be < {ax}_max ({hi})"
                )

    def as_dict(self) -> dict:
        return {
            "x_min": self.x_min, "x_max": self.x_max,
            "y_min": self.y_min, "y_max": self.y_max,
            "z_min": self.z_min, "z_max": self.z_max,
        }


@dataclass(frozen=True)
class Discretization:
    dx: int
    dy: int
    dz: int

    def __post_init__(self):
        for name, v in (("dx", self.dx), ("dy", self.dy), ("dz", self.dz)):
            if v < 1:
                raise ConfigError(f"discretization.{name} must be >= 1")

    def as_dict(self) -> dict:
        return {"dx": self.dx, "dy": self.dy, "dz": self.dz}


@dataclass(frozen=True)
class BlockMesh:
    bounding_box: BoundingBox
    discretization: Discretization
    boundary_types: dict[str, str]

    def __post_init__(self):
        for face, kind in self.boundary_types.items():
            if kind not in {"wall", "patch"}:
                raise ConfigError(
                    f"blockMesh.boundaryTypes.{face}: must be 'wall' or 'patch',"
                    f" got '{kind}'"
                )
        for face in ("left", "right"):
            if self.boundary_types.get(face) != "patch":
                raise ConfigError(
                    f"blockMesh.boundaryTypes.{face}: inlet/outlet must be 'patch'"
                )


@dataclass(frozen=True)
class SnappyHexMesh:
    seed_location_in_mesh: tuple[float, float, float]
    max_local_cells: int
    max_global_cells: int
    min_surface_refinement_lvl: int
    max_surface_refinement_lvl: int

    def __post_init__(self):
        if len(self.seed_location_in_mesh) != 3:
            raise ConfigError("snappyHexMesh.seed_location_in_mesh needs 3 values")
        if self.min_surface_refinement_lvl > self.max_surface_refinement_lvl:
            raise ConfigError(
                "snappyHexMesh: min_surface_refinement_lvl must be "
                "<= max_surface_refinement_lvl"
            )
        if self.max_local_cells <= 0 or self.max_global_cells <= 0:
            raise ConfigError("snappyHexMesh: cell counts must be > 0")


@dataclass(frozen=True)
class Fluid:
    fluid_kinematic_viscosity: float
    turbulence_model: str | None
    transport_model: str | None

    def __post_init__(self):
        if self.fluid_kinematic_viscosity <= 0:
            raise ConfigError("fluid.fluid_kinematic_viscosity must be > 0")


@dataclass(frozen=True)
class BoundaryConditions:
    u: dict[str, str]
    p: dict[str, str]

    def __post_init__(self):
        expected = {f"{face}_bc_type" for face in FACES}
        for name, faces in (("u", self.u), ("p", self.p)):
            if set(faces) != expected:
                missing = sorted(expected - set(faces))
                extra = sorted(set(faces) - expected)
                raise ConfigError(
                    f"boundaryConditions.{name}: keys must be exactly "
                    f"{sorted(expected)}; missing={missing}, unexpected={extra}"
                )
            for key, bc in faces.items():
                if bc not in VALID_BC_TYPES:
                    raise ConfigError(
                        f"boundaryConditions.{name}.{key}: unknown boundary type "
                        f"'{bc}' (allowed: {sorted(VALID_BC_TYPES)})"
                    )


@dataclass(frozen=True)
class Medium:
    min_radius: float
    max_radius: float
    geometry_bounds_type: str
    bounding_box: BoundingBox

    def __post_init__(self):
        if not 0 < self.min_radius <= self.max_radius:
            raise ConfigError("medium: require 0 < min_radius <= max_radius")
        if self.geometry_bounds_type not in GeometryPeriodicityType:
            raise ConfigError(
                f"medium.geometry_bounds_type: '{self.geometry_bounds_type}' "
                f"not in {sorted(GeometryPeriodicityType)}"
            )


@dataclass(frozen=True)
class Run:
    working_directory: pathlib.Path
    porosities: tuple[float, ...]
    velocities: tuple[float, ...]
    number_of_geometries: int

    def __post_init__(self):
        if not self.porosities:
            raise ConfigError("run.sweepParams.porosities must be non-empty")
        for p in self.porosities:
            if not 0 < p < 1:
                raise ConfigError(
                    f"run.sweepParams.porosities: {p} not in open interval (0, 1)"
                )
        if not self.velocities:
            raise ConfigError("run.sweepParams.velocities must be non-empty")
        for v in self.velocities:
            if v <= 0:
                raise ConfigError(f"run.sweepParams.velocities: {v} must be > 0")
        if self.number_of_geometries < 1:
            raise ConfigError("run.sweepParams.number_of_geometries must be >= 1")


@dataclass(frozen=True)
class CaseConfig:
    run: Run
    control: ControlDict
    parallelism: Parallelism
    block_mesh: BlockMesh
    snappy: SnappyHexMesh
    fluid: Fluid
    boundary: BoundaryConditions
    medium: Medium

    @classmethod
    def from_toml(cls, path: pathlib.Path) -> "CaseConfig":
        fn = path.name
        toml_dict = tomllib.loads(path.read_text())

        def req(dotted, expected):
            return _require(toml_dict, dotted, expected, filename=fn)

        def opt(dotted, expected, default=None):
            return _optional(toml_dict, dotted, expected, filename=fn, default=default)

        run = Run(
            working_directory=pathlib.Path(
                req("run.sweepParams.working_directory", str)
            ),
            porosities=tuple(req("run.sweepParams.porosities", list)),
            velocities=tuple(req("run.sweepParams.velocities", list)),
            number_of_geometries=req("run.sweepParams.number_of_geometries", int),
        )
        parallelism = Parallelism(
            number_of_procs=req("run.parallelism.number_of_procs", int),
            decompose_method=_normalize_none(
                opt("run.parallelism.decompose_method", str)
            ),
        )

        control = ControlDict(
            **_exact_table(toml_dict, "case.controlDict", ControlDict, filename=fn)
        )
        medium = Medium(
            min_radius=req("case.physicalProperties.medium.min_radius", float),
            max_radius=req("case.physicalProperties.medium.max_radius", float),
            geometry_bounds_type=GeometryPeriodicityType(
                req(
                    "case.physicalProperties.medium.geometry_bounds_type", str
                )
            ),
            bounding_box=BoundingBox(
                **_exact_table(
                    toml_dict,
                    "case.physicalProperties.medium.boundingBox",
                    BoundingBox,
                    filename=fn
                ),
            ),
        )
        fluid = Fluid(
            fluid_kinematic_viscosity=req(
                "case.physicalProperties.fluid.fluid_kinematic_viscosity", (int, float)
            ),
            turbulence_model=_normalize_none(
                opt("case.physicalProperties.fluid.turbulence_model", str)
            ),
            transport_model=_normalize_none(
                opt("case.physicalProperties.fluid.transport_model", str)
            ),
        )

        block_mesh = BlockMesh(
            bounding_box=BoundingBox(
                **_exact_table(
                    toml_dict,
                    "mesh.blockMesh.boundingBox",
                    BoundingBox,
                    filename=fn
                )
            ),
            discretization=Discretization(
                **_exact_table(
                    toml_dict,
                    "mesh.blockMesh.discretization",
                    Discretization,
                    filename=fn
                )
            ),
            boundary_types=req("mesh.blockMesh.boundaryTypes", dict),
        )
        snappy = SnappyHexMesh(
            seed_location_in_mesh=tuple(
                req("mesh.snappyHexMesh.seed_location_in_mesh", list)
            ),
            max_local_cells=req("mesh.snappyHexMesh.max_local_cells", int),
            max_global_cells=req("mesh.snappyHexMesh.max_global_cells", int),
            min_surface_refinement_lvl=req(
                "mesh.snappyHexMesh.min_surface_refinement_lvl",
                int
            ),
            max_surface_refinement_lvl=req(
                "mesh.snappyHexMesh.max_surface_refinement_lvl",
                int
            ),
        )

        boundary = BoundaryConditions(
            u=req("case.boundaryConditions.u", dict),
            p=req("case.boundaryConditions.p", dict),
        )

        return cls(
            run=run,
            control=control,
            parallelism=parallelism,
            block_mesh=block_mesh,
            snappy=snappy,
            fluid=fluid,
            boundary=boundary,
            medium=medium,
        )
