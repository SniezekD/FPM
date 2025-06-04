import pathlib
import fpm.openfoam_case as oc
from fpm.media_models.swiss_cheese import SwissCheese


WD = pathlib.Path('/home/user/tests')

c = oc.openFoamCase(
    working_direcory=WD,
    end_time=501,
    time_step=1,
    solver_name='simpleFoam',
    write_interval=50,
    number_of_procs=6,
    max_local_cells=2000000,
    max_global_cells=400000,
    min_surface_refinement_lvl=2,
    max_surface_refinement_lvl=3,
    seed_location_in_mesh=(-0.5, 0.5, 0.5),
    fluid_kinematic_viscosity=1e-6,
    blockmesh_boundary_types={
        'obstacles': 'wall',
        'front': 'wall',
        'back': 'wall',
        'up': 'wall',
        'down': 'wall',
        'left': 'patch',
        'right': 'patch'
    },
    u_boundary_types={
        'left_bc_type': 'fixedValue',
        'left_field_type': 'value',
        'left_field_value': 'uniform (1e-6 0 0)',
        'right_bc_type': 'zeroGradient',
        'right_field_type': None,
        'right_field_value': None,
        'up_bc_type': 'noSlip',
        'up_field_type': None,
        'up_field_value': None,
        'down_bc_type': 'noSlip',
        'down_field_type': None,
        'down_field_value': None,
        'front_bc_type': 'noSlip',
        'front_field_type': None,
        'front_field_value': None,
        'back_bc_type': 'noSlip',
        'back_field_type': None,
        'back_field_value': None,
        'obstacles_bc_type': 'noSlip',
        'obstacles_field_type': None,
        'obstacles_field_value': None
    },
    p_boundary_types={
        'left_bc_type': 'zeroGradient',
        'left_field_type': None,
        'left_field_value': None,
        'right_bc_type': 'fixedValue',
        'right_field_type': 'value',
        'right_field_value': 'uniform 0',
        'up_bc_type': 'zeroGradient',
        'up_field_type': None,
        'up_field_value': None,
        'down_bc_type': 'zeroGradient',
        'down_field_type': None,
        'down_field_value': None,
        'front_bc_type': 'zeroGradient',
        'front_field_type': None,
        'front_field_value': None,
        'back_bc_type': 'zeroGradient',
        'back_field_type': None,
        'back_field_value': None,
        'obstacles_bc_type': 'zeroGradient',
        'obstacles_field_type': None,
        'obstacles_field_value': None
    },
    bounding_box_coords={
        'x_min': -20,
        'x_max': 16+30,
        'y_min': 0,
        'y_max': 16,
        'z_min': 0,
        'z_max': 16,
    },
    bounding_box_discretization={
        'dx': 66 * 4,
        'dy': 64,
        'dz': 64,
    },
    turbulence_model=None,
    decompose_method=None,
    transport_model=None
)

c.create_of_dir()

c.save_walls_stls(WD / 'OF_case' / 'constant' / 'triSurface')

pm = SwissCheese(
    porosity=0.9,
    bounds=[0, 16, 0, 16, 0, 16],
    min_radius=0.1,
    max_radius=1
)
pm.walls = pm.create_boundary_walls()
pm.obstacles = pm.create_obstacles(geometry_bounds_type='non_periodic')
pm.save_stls(savepath=WD / 'OF_case' / 'constant' / 'triSurface')
