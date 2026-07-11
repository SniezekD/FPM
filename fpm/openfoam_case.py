import pathlib

import jinja2
import numpy as np
import pandas as pd

import fpm.geometry.shapes as shapes


class OpenFoamCase():
    def __init__(
        self,
        working_direcory: pathlib.Path,
        end_time: float,
        time_step: float,
        solver_name: str,
        write_interval: float,
        number_of_procs: int,
        max_local_cells: int,
        max_global_cells: int,
        min_surface_refinement_lvl: int,
        max_surface_refinement_lvl: int,
        seed_location_in_mesh: np.ndarray,
        fluid_kinematic_viscosity: float,
        blockmesh_boundary_types: dict,
        u_boundary_types: dict,
        p_boundary_types: dict,
        bounding_box_coords: dict,
        bounding_box_discretization: dict,
        turbulence_model: str = None,
        decompose_method: str = None,
        transport_model: str = None,
    ) -> None:
        self.working_direcory = working_direcory
        self.end_time = end_time
        self.time_step = time_step
        self.solver_name = solver_name
        self.write_interval = write_interval
        self.number_of_procs = number_of_procs
        self.max_local_cells = max_local_cells
        self.max_global_cells = max_global_cells
        self.min_surface_refinement_lvl = min_surface_refinement_lvl
        self.max_surface_refinement_lvl = max_surface_refinement_lvl
        self.seed_location_in_mesh = seed_location_in_mesh
        self.fluid_kinematic_viscosity = fluid_kinematic_viscosity
        self.blockmesh_boundary_types = blockmesh_boundary_types
        self.u_boundary_types = u_boundary_types
        self.p_boundary_types = p_boundary_types
        self.bounding_box_coords = bounding_box_coords
        self.bounding_box_discretization = bounding_box_discretization
        self.turbulence_model = turbulence_model
        self.decompose_method = decompose_method
        self.transport_model = transport_model
        self.boundary_walls = self.create_boundary_walls()

    def create_of_dir(self):
        of_dir = self.working_direcory / 'OF_case'
        of_dir.mkdir(parents=True, exist_ok=True)

        zero_dir = of_dir / '0'
        system_dir = of_dir / 'system'
        constant_dir = of_dir / 'constant'

        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("fpm/templates/openfoam_files/")
        )
        all_templates = {}

        zero_u_path = zero_dir / 'U'
        zero_u_template = jinja_env.get_template("U_template.jinja")
        zero_u_content = zero_u_template.render(
            left_bc_type=self.u_boundary_types['left_bc_type'],
            left_field_type=self.u_boundary_types['left_field_type'],
            left_field_value=self.u_boundary_types['left_field_value'],
            right_bc_type=self.u_boundary_types['right_bc_type'],
            right_field_type=self.u_boundary_types['right_field_type'],
            right_field_value=self.u_boundary_types['right_field_value'],
            up_bc_type=self.u_boundary_types['up_bc_type'],
            up_field_type=self.u_boundary_types['up_field_type'],
            up_field_value=self.u_boundary_types['up_field_value'],
            down_bc_type=self.u_boundary_types['down_bc_type'],
            down_field_type=self.u_boundary_types['down_field_type'],
            down_field_value=self.u_boundary_types['down_field_value'],
            front_bc_type=self.u_boundary_types['front_bc_type'],
            front_field_type=self.u_boundary_types['front_field_type'],
            front_field_value=self.u_boundary_types['front_field_value'],
            back_bc_type=self.u_boundary_types['back_bc_type'],
            back_field_type=self.u_boundary_types['back_field_type'],
            back_field_value=self.u_boundary_types['back_field_value'],
            obstacles_bc_type=self.u_boundary_types['obstacles_bc_type'],
            obstacles_field_type=self.u_boundary_types['obstacles_field_type'],
            obstacles_field_value=self.u_boundary_types[
                'obstacles_field_value'
            ],
        )
        all_templates['zero_u'] = {
            'path': zero_u_path,
            'content': zero_u_content
        }

        zero_p_path = zero_dir / 'p'
        zero_p_template = jinja_env.get_template("p_template.jinja")
        zero_p_content = zero_p_template.render(
            left_bc_type=self.p_boundary_types['left_bc_type'],
            left_field_type=self.p_boundary_types['left_field_type'],
            left_field_value=self.p_boundary_types['left_field_value'],
            right_bc_type=self.p_boundary_types['right_bc_type'],
            right_field_type=self.p_boundary_types['right_field_type'],
            right_field_value=self.p_boundary_types['right_field_value'],
            up_bc_type=self.p_boundary_types['up_bc_type'],
            up_field_type=self.p_boundary_types['up_field_type'],
            up_field_value=self.p_boundary_types['up_field_value'],
            down_bc_type=self.p_boundary_types['down_bc_type'],
            down_field_type=self.p_boundary_types['down_field_type'],
            down_field_value=self.p_boundary_types['down_field_value'],
            front_bc_type=self.p_boundary_types['front_bc_type'],
            front_field_type=self.p_boundary_types['front_field_type'],
            front_field_value=self.p_boundary_types['front_field_value'],
            back_bc_type=self.p_boundary_types['back_bc_type'],
            back_field_type=self.p_boundary_types['back_field_type'],
            back_field_value=self.p_boundary_types['back_field_value'],
            obstacles_bc_type=self.p_boundary_types['obstacles_bc_type'],
            obstacles_field_type=self.p_boundary_types['obstacles_field_type'],
            obstacles_field_value=self.p_boundary_types[
                'obstacles_field_value'
            ],
        )
        all_templates['zero_p'] = {
            'path': zero_p_path,
            'content': zero_p_content
        }

        snappy_dict_path = system_dir / 'snappyHexMeshDict'
        snappy_dict_template = jinja_env.get_template(
            "snappyHexMesh_template.jinja"
        )
        snappy_dict_content = snappy_dict_template.render(
            max_local_cells=self.max_local_cells,
            max_global_cells=self.max_global_cells,
            min_surface_refinement_lvl=self.min_surface_refinement_lvl,
            max_surface_refinement_lvl=self.max_surface_refinement_lvl,
            obstacles_patch_info=self.blockmesh_boundary_types['obstacles'],
            front_patch_info=self.blockmesh_boundary_types['front'],
            back_patch_info=self.blockmesh_boundary_types['back'],
            down_patch_info=self.blockmesh_boundary_types['down'],
            up_patch_info=self.blockmesh_boundary_types['up'],
            left_patch_info=self.blockmesh_boundary_types['left'],
            right_patch_info=self.blockmesh_boundary_types['right'],
            location_in_mesh_x=self.seed_location_in_mesh[0],
            location_in_mesh_y=self.seed_location_in_mesh[1],
            location_in_mesh_z=self.seed_location_in_mesh[2],
        )
        all_templates['snappyhexmeshdict'] = {
            'path': snappy_dict_path,
            'content': snappy_dict_content
        }

        mesh_quality_dict_path = system_dir / 'meshQualityDict'
        mesh_quality_dict_template = jinja_env.get_template(
            "meshQualityDict_template.jinja"
        )
        mesh_quality_dict_content = mesh_quality_dict_template.render(
        )
        all_templates['meshqualitdict'] = {
            'path': mesh_quality_dict_path,
            'content': mesh_quality_dict_content
        }

        blockmesh_dict_path = system_dir / 'blockMeshDict'
        blockmesh_dict_template = jinja_env.get_template(
            "blockMesh_template.jinja"
        )
        blockmesh_dict_content = blockmesh_dict_template.render(
           x_min=self.bounding_box_coords['x_min'],
           x_max=self.bounding_box_coords['x_max'],
           y_min=self.bounding_box_coords['y_min'],
           y_max=self.bounding_box_coords['y_max'],
           z_min=self.bounding_box_coords['z_min'],
           z_max=self.bounding_box_coords['z_max'],
           dx=self.bounding_box_discretization['dx'],
           dy=self.bounding_box_discretization['dy'],
           dz=self.bounding_box_discretization['dy'],
           left_bc_type=self.blockmesh_boundary_types['left'],
           right_bc_type=self.blockmesh_boundary_types['right'],
           up_bc_type=self.blockmesh_boundary_types['up'],
           down_bc_type=self.blockmesh_boundary_types['down'],
           front_bc_type=self.blockmesh_boundary_types['front'],
           back_bc_type=self.blockmesh_boundary_types['back'],
        )
        all_templates['blockmeshdict'] = {
            'path': blockmesh_dict_path,
            'content': blockmesh_dict_content
        }

        control_dict_path = system_dir / 'controlDict'
        control_dict_template = jinja_env.get_template(
            "controlDict_template.jinja"
        )
        control_dict_content = control_dict_template.render(
            solver_name=self.solver_name,
            end_time=self.end_time,
            time_step=self.time_step,
            write_interval=self.write_interval
        )
        all_templates['controldict'] = {
            'path': control_dict_path,
            'content': control_dict_content
        }

        transport_properties_path = constant_dir / 'transportProperties'
        transport_properties_template = jinja_env.get_template(
            "transportProperties_template.jinja"
        )
        transport_properties_content = transport_properties_template.render(
            transport_model=self.transport_model,
            kin_viscosity=self.fluid_kinematic_viscosity
        )
        all_templates['transportproperties'] = {
            'path': transport_properties_path,
            'content': transport_properties_content
        }

        turbulence_properties_path = constant_dir / 'turbulenceProperties'
        turbulence_properties_template = jinja_env.get_template(
            "turbulenceProperties_template.jinja"
        )
        turbulence_properties_content = turbulence_properties_template.render(
            turbulence_model=self.turbulence_model
        )
        all_templates['transportproperties'] = {
            'path': turbulence_properties_path,
            'content': turbulence_properties_content
        }

        physical_properties_path = constant_dir / 'physicalProperties'
        physical_properties_template = jinja_env.get_template(
            "physicalProperties_template.jinja"
        )
        physical_properties_content = physical_properties_template.render(
            kin_viscosity=self.fluid_kinematic_viscosity
        )
        all_templates['physicalproperties'] = {
            'path': physical_properties_path,
            'content': physical_properties_content
        }

        fv_schemes_path = system_dir / 'fvSchemes'
        fv_schemes_template = jinja_env.get_template(
            "fvSchemes_template.jinja"
        )
        fv_schemes_content = fv_schemes_template.render()
        all_templates['fvschemes'] = {
            'path': fv_schemes_path,
            'content': fv_schemes_content
        }

        fv_solution_path = system_dir / 'fvSolution'
        fv_solution_template = jinja_env.get_template(
            "fvSolution_template.jinja"
        )
        fv_solution_content = fv_solution_template.render()
        all_templates['fvsolution'] = {
            'path': fv_solution_path,
            'content': fv_solution_content
        }

        decomposepar_dict_path = system_dir / 'decomposeParDict'
        decomposepar_dict_template = jinja_env.get_template(
            "decomposeParDict_template.jinja"
        )
        decomposepar_dict_content = decomposepar_dict_template.render(
            number_of_procs=self.number_of_procs,
            decompose_method=self.decompose_method
        )
        all_templates['decomposepardict'] = {
            'path': decomposepar_dict_path,
            'content': decomposepar_dict_content
        }

        for name, template in all_templates.items():
            template['path'].parent.mkdir(exist_ok=True, parents=True)
            with open(template['path'], mode="w", encoding="utf-8") as file:
                file.write(template['content'])
            print(f"  ... created {template['path']}")

    def change_velocity_boundary_types(self, new_u_boundary_types):
        self.u_boundary_types = new_u_boundary_types
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("fpm/templates/openfoam_files/")
        )
        of_dir = self.working_direcory / 'OF_case'
        zero_dir = of_dir / '0'
        zero_u_path = zero_dir / 'U'
        zero_u_template = jinja_env.get_template("U_template.jinja")
        zero_u_content = zero_u_template.render(
            left_bc_type=self.u_boundary_types['left_bc_type'],
            left_field_type=self.u_boundary_types['left_field_type'],
            left_field_value=self.u_boundary_types['left_field_value'],
            right_bc_type=self.u_boundary_types['right_bc_type'],
            right_field_type=self.u_boundary_types['right_field_type'],
            right_field_value=self.u_boundary_types['right_field_value'],
            up_bc_type=self.u_boundary_types['up_bc_type'],
            up_field_type=self.u_boundary_types['up_field_type'],
            up_field_value=self.u_boundary_types['up_field_value'],
            down_bc_type=self.u_boundary_types['down_bc_type'],
            down_field_type=self.u_boundary_types['down_field_type'],
            down_field_value=self.u_boundary_types['down_field_value'],
            front_bc_type=self.u_boundary_types['front_bc_type'],
            front_field_type=self.u_boundary_types['front_field_type'],
            front_field_value=self.u_boundary_types['front_field_value'],
            back_bc_type=self.u_boundary_types['back_bc_type'],
            back_field_type=self.u_boundary_types['back_field_type'],
            back_field_value=self.u_boundary_types['back_field_value'],
            obstacles_bc_type=self.u_boundary_types['obstacles_bc_type'],
            obstacles_field_type=self.u_boundary_types['obstacles_field_type'],
            obstacles_field_value=self.u_boundary_types[
                'obstacles_field_value'
            ],
        )
        zero_u_path.parent.mkdir(exist_ok=True, parents=True)
        with open(zero_u_path, mode="w", encoding="utf-8") as file:
            file.write(zero_u_content)
        print(f"  ... changed {zero_u_path}")

    def create_boundary_walls(self):
        """Create walls that will be used as geometrical
        boundaries to the model.
        """
        upper_wall = shapes.Plane(
            position=[
                self.bounding_box_coords['x_min'],
                self.bounding_box_coords['y_max'],
                self.bounding_box_coords['z_min']
            ],
            size=[
                self.bounding_box_coords['x_max']
                - self.bounding_box_coords['x_min'],
                0,
                self.bounding_box_coords['z_max']
                - self.bounding_box_coords['z_min']
            ]
        )

        lower_wall = shapes.Plane(
            position=[
                self.bounding_box_coords['x_min'],
                self.bounding_box_coords['y_min'],
                self.bounding_box_coords['z_min']
            ],
            size=[
                self.bounding_box_coords['x_max']
                - self.bounding_box_coords['x_min'],
                0,
                self.bounding_box_coords['z_max']
                - self.bounding_box_coords['z_min']
            ]
        )

        right_wall = shapes.Plane(
            position=[
                self.bounding_box_coords['x_max'],
                self.bounding_box_coords['y_min'],
                self.bounding_box_coords['z_min']
            ],
            size=[
                0,
                self.bounding_box_coords['y_max']
                - self.bounding_box_coords['y_min'],
                self.bounding_box_coords['z_max']
                - self.bounding_box_coords['z_min']
            ]
        )

        left_wall = shapes.Plane(
            position=[
                self.bounding_box_coords['x_min'],
                self.bounding_box_coords['y_min'],
                self.bounding_box_coords['z_min']
            ],
            size=[
                0,
                self.bounding_box_coords['y_max']
                - self.bounding_box_coords['y_min'],
                self.bounding_box_coords['z_max']
                - self.bounding_box_coords['z_min']
            ]
        )

        front_wall = shapes.Plane(
            position=[
                self.bounding_box_coords['x_min'],
                self.bounding_box_coords['y_min'],
                self.bounding_box_coords['z_max']
            ],
            size=[
                self.bounding_box_coords['x_max']
                - self.bounding_box_coords['x_min'],
                self.bounding_box_coords['y_max']
                - self.bounding_box_coords['y_min'],
                0
            ]
        )

        back_wall = shapes.Plane(
            position=[
                self.bounding_box_coords['x_min'],
                self.bounding_box_coords['y_min'],
                self.bounding_box_coords['z_min']
            ],
            size=[
                self.bounding_box_coords['x_max']
                - self.bounding_box_coords['x_min'],
                self.bounding_box_coords['y_max']
                - self.bounding_box_coords['y_min'],
                0
            ]
        )

        walls = {
            "wall_up": upper_wall,
            "wall_down": lower_wall,
            "wall_right": right_wall,
            "wall_left": left_wall,
            "wall_front": front_wall,
            "wall_back": back_wall,
        }

        return walls

    def save_walls_stls(self, savepath: pathlib.Path):
        savepath.mkdir(parents=True, exist_ok=True)

        if self.boundary_walls is None:
            self.create_boundary_walls()

        for name, o in self.boundary_walls.items():
            dest = savepath / f"{name}.stl"
            o.save_stl(destination=dest, binary=False)

    def save_spec_to_file(
        self,
        savepath: pathlib.Path,
        inlet_wall: str = 'left'
    ):
        data_dict = {
            'inlet_wall': [inlet_wall],
            'inlet_u_type': [
                self.u_boundary_types[f'{inlet_wall}_field_type']
            ],
            'inlet_u_value': [
                self.u_boundary_types[f'{inlet_wall}_field_value']
            ],
            'inlet_area': [self.boundary_walls[f'wall_{inlet_wall}'].area],
            'x_min': [self.bounding_box_coords['x_min']],
            'x_max': [self.bounding_box_coords['x_max']],
            'y_min': [self.bounding_box_coords['y_min']],
            'y_max': [self.bounding_box_coords['y_max']],
            'z_min': [self.bounding_box_coords['z_min']],
            'z_max': [self.bounding_box_coords['z_max']],
            'number_of_procs': [self.number_of_procs],

        }

        df = pd.DataFrame.from_dict(data_dict)
        df.to_csv(savepath, index=False)
        print(f"  ... saved OF spec to {savepath}")
