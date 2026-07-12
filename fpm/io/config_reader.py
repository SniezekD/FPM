import pathlib

from fpm.io.config import CaseConfig
from fpm.io.config import VALID_BC_TYPES, FACES


class ConfigReader:
    """Reads a case configuration from a TOML file."""
    def __init__(self, toml_path: pathlib.Path):
        self.toml_path = toml_path
        self.case_cfg = self.read_case_config(toml_path)

    @staticmethod
    def read_case_config(toml_path: pathlib.Path) -> CaseConfig:
        """Read a case configuration from a TOML file."""
        return CaseConfig.from_toml(toml_path)

    def _unpack_u_boundary_types(self) -> dict:
        """Unpacks and expands boundary conditions for velocity.
        In order to characterize a boundary condition on a face,
        we need three parameters. One of them determines the
        values of remaining two, so there is no need to keep all
        of them in the config. Value of velocity is itself only
        a placeholder for now. I will be changed later when running
        the experiment.

        Raises:
            ValueError: If there is an illegal type of bc type.

        Returns:
            dict: a full dict compatible with OpenFoamCase class.
        """
        boundaty_types = self.case_cfg.boundary.u

        out_dict = {}
        for face in FACES:
            out_dict[f"{face}_bc_type"] = boundaty_types[f"{face}_bc_type"]
            if boundaty_types[f"{face}_bc_type"] not in VALID_BC_TYPES:
                raise ValueError(f"Illegal value of boundary type for {face}_bc_type."
                                 f"Legal values are {VALID_BC_TYPES}")

            elif boundaty_types[f"{face}_bc_type"] == "fixedValue":
                out_dict[f"{face}_field_type"] = "value"
                out_dict[f"{face}_field_value"] = "uniform (0 0 0)"

            elif boundaty_types[f"{face}_bc_type"] == "zeroGradient":
                out_dict[f"{face}_field_type"] = None
                out_dict[f"{face}_field_value"] = None

            elif boundaty_types[f"{face}_bc_type"] == "noSlip":
                out_dict[f"{face}_field_type"] = None
                out_dict[f"{face}_field_value"] = None

        return out_dict

    def _unpack_p_boundary_types(self):
        """Unpacks and expands boundary conditions for pressure.
        In order to characterize a boundary condition on a face,
        we need three parameters. One of them determines the
        values of remaining two, so there is no need to keep all
        of them in the config. Reference value of pressure is set
        to zero at the outlet.

        Raises:
            ValueError: If there is an illegal type of bc type.

        Returns:
            dict: a full dict compatible with OpenFoamCase class.
        """
        boundaty_types = self.case_cfg.boundary.p

        out_dict = {}
        for face in FACES:
            out_dict[f"{face}_bc_type"] = boundaty_types[f"{face}_bc_type"]
            if boundaty_types[f"{face}_bc_type"] not in VALID_BC_TYPES:
                raise ValueError(f"Illegal value of boundary type for {face}_bc_type."
                                 f"Legal values are {VALID_BC_TYPES}")

            elif boundaty_types[f"{face}_bc_type"] == "fixedValue":
                out_dict[f"{face}_field_type"] = "value"
                out_dict[f"{face}_field_value"] = "uniform 0"

            elif boundaty_types[f"{face}_bc_type"] == "zeroGradient":
                out_dict[f"{face}_field_type"] = None
                out_dict[f"{face}_field_value"] = None

            elif boundaty_types[f"{face}_bc_type"] == "noSlip":
                out_dict[f"{face}_field_type"] = None
                out_dict[f"{face}_field_value"] = None

        return out_dict

    def unpack_foam_case_config(self):
        """Unpack the case configuration into its components
        so that it is compatible with OpenFoamCase.
        """
        return {
            "working_direcory": self.case_cfg.run.working_directory,
            "end_time": self.case_cfg.control.end_time,
            "time_step": self.case_cfg.control.time_step,
            "solver_name": self.case_cfg.control.solver_name,
            "write_interval": self.case_cfg.control.write_interval,
            "number_of_procs": self.case_cfg.parallelism.number_of_procs,
            "max_local_cells": self.case_cfg.snappy.max_local_cells,
            "max_global_cells": self.case_cfg.snappy.max_global_cells,
            "min_surface_refinement_lvl":
                self.case_cfg.snappy.min_surface_refinement_lvl,
            "max_surface_refinement_lvl":
                self.case_cfg.snappy.max_surface_refinement_lvl,
            "seed_location_in_mesh": self.case_cfg.snappy.seed_location_in_mesh,
            "fluid_kinematic_viscosity": self.case_cfg.fluid.fluid_kinematic_viscosity,
            "blockmesh_boundary_types": self.case_cfg.block_mesh.boundary_types,
            "u_boundary_types": self._unpack_u_boundary_types(),
            "p_boundary_types": self._unpack_p_boundary_types(),
            "bounding_box_coords": self.case_cfg.block_mesh.bounding_box.as_dict(),
            "bounding_box_discretization": {
                "dx": self.case_cfg.block_mesh.discretization.dx,
                "dy": self.case_cfg.block_mesh.discretization.dy,
                "dz": self.case_cfg.block_mesh.discretization.dz,
            },
            "turbulence_model": self.case_cfg.fluid.turbulence_model,
            "decompose_method": self.case_cfg.parallelism.decompose_method,
            "transport_model": self.case_cfg.fluid.transport_model,
        }
