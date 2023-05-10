import os
import stl
import sys
import utils
import shutil
import numpy as np
import pyvista as pv
from mystl import ribbon, cube, plane, sphere, rounded_cube, colective_grains
from pathlib import Path
from stl import mesh

class IFPM:
    def __init__(self, porosity: float,
                 size: dict,
                 margin: int,
                 working_dir: Path,
                 r_r: float,
                 s_o: bool = False
        ) -> None:
        """Inertial Flow in Porous Media class creator"""
        self.porosity   = porosity
        self.size       = size
        self.margin     = margin
        self.wd         = working_dir
        self.rounding_r = r_r
        self.save_obs   = s_o
        self.lattice    = self.porosity_lattice()
        self.stls, self.obstacles_names = self.translate_into_stl()

        if self.rounding_r <= 866 or self.rounding_r > 0.5:
            print("Creating simulation geometry with "
                  + "cubes rounded at the vertices with "
                  + f"radius {self.rounding_r} as obstacles.")
        elif self.rounding_r <= 0.5:
            print(f"Creating simulation geometry with "
                  + "spheres as obstacles.")
        elif self.rounding_r > 0.866:
            print(f"Creating simulation geometry with "
                  + "sharp cubes as obstacles.")


    def porosity_lattice(self) -> np.ndarray:
        """
        Creates a random lattice with given porosity
        """
        lattice             = np.zeros(list(self.size.values()), dtype=int)
        number_of_cells     = np.prod(list(self.size.values()))
        number_of_obstacles = int((1-self.porosity)*number_of_cells)
        for i in range(number_of_obstacles): 
            rnd_x = np.random.randint(self.size['x'])
            rnd_y = np.random.randint(self.size['y'])
            rnd_z = np.random.randint(self.size['z'])
            lattice[rnd_x, rnd_y, rnd_z] = 1 
        
        # ADD MARGINS:
        lattice  = np.insert(
            lattice, 
            0, 
            np.zeros((self.margin, self.size['y'], self.size['z'])),
            axis=0
        )
        lattice  = np.append(
            lattice,
            np.zeros((self.margin, self.size['y'], self.size['z'])),
            axis=0
        )
        lattice  = lattice.transpose()

        # RETRUN LATTICE WITH MARGINS:
        return lattice
    

    def translate_into_fms(self):
        """
        Translates 2D geometry into .fms format. If geometry is 3D returns False
        """
        if(self.lattice.shape[0] == 1):
            for boundary in self.stls.keys():
                if boundary not in ['wall_front','wall_back']:
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

        inlet      = plane(0, 0, 0,
                            0, self.size['y'], self.size['z'])
        outlet     = plane(self.size['x'] + 2*self.margin, 0, 0,
                            0, self.size['y'], self.size['z'])
        wall_up    = plane(0, self.size['y'], 0,
                            self.size['x'] + 2*self.margin, 0, self.size['z'])
        wall_down  = plane(0, 0, 0,
                            self.size['x'] + 2*self.margin, 0, self.size['z'])
        wall_front = plane(0, 0, 0,
                            self.size['x'] + 2*self.margin, self.size['y'], 0)
        wall_back  = plane(0, 0, self.size['z'],
                            self.size['x'] + 2*self.margin, self.size['y'], 0)
        
        obstacles       = []
        obstacles_names = []

        grain_positions = np.argwhere(self.lattice == 1)

        for z,y,x in grain_positions:
            if self.lattice[z,y,x] == 1:
                if self.rounding_r > 0.866:
                    # if the case is 2D 
                    if self.lattice.shape[0] == 1:         
                        tmp_obstacle = ribbon(x,y,z)
                    else:
                        tmp_obstacle = cube(x,y,z)

                elif self.rounding_r <= 0.5:
                    tmp_obstacle = sphere(x,y,z)

                else:
                    tmp_obstacle = rounded_cube(x,y,z,self.rounding_r)

                obstacles_names.append(tmp_obstacle.get_name())
                obstacles.append(tmp_obstacle.stl)

        obstacles_stl = obstacles[0]
        if self.save_obs:
            print("      Saving separate obstacles")
            for obs,obs_name in zip(obstacles, obstacles_names):
                obs.save(f"{obs_name}")

        for obs in obstacles[1:]:
            obstacles_stl = obstacles_stl.merge(obs)
        obstacles_stl = colective_grains(obstacles_stl)
        obstacles_stl.save("/home/user/sharedVol/test_grains.stl")
        
        stls = {'inlet'     : inlet,
                'outlet'    : outlet,
                'wall_up'   : wall_up,
                'wall_down' : wall_down,
                'wall_front': wall_front,
                'wall_back' : wall_back,
                'grains'    : obstacles_stl}
        
        print("Lattice translated into stl")

        return stls, obstacles_names
    
    
    def prepare_model(self, ) -> None:
        print("    Preparing model")
        for stl_name in self.stls.keys():
            save_path = f"/home/user/MGR/IFPM/{stl_name}.stl"
            self.stls[stl_name].save(save_path)
        if(self.lattice.shape[0] == 1):
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
                self.margin
            )
            utils.createSnappyHexMeshDict(
                self.wd.joinpath(
                    'OF_Model',
                    'system',
                    'snappyHexMeshDict'
                )
            )
        utils.run_cmd([r'./prep_model.sh'])

        # shutil.rmtree(self.wd.joinpath('OF_Model', '0'))
        # shutil.rmtree(self.wd.joinpath('OF_Model', 'constant', 'triSurface'))
        # os.makedirs(self.wd.joinpath('OF_Model', 'constant', 'triSurface', 'grains'), exist_ok=True)
        # os.makedirs(self.wd.joinpath('OF_Model', '0'), exist_ok=True)
        # self.wd.joinpath('OF_Model', '0', 'p').touch(exist_ok=True)
        # self.wd.joinpath('OF_Model', '0', 'U').touch(exist_ok=True)


    def run_meshing(self) -> None:
        """
        Runs OpenFOAM meshing commands. 
        Mesh is done with snappyHexMesh tool.
        """
        if(self.lattice.shape[0] == 1):
            print("    Creating the mesh with cfMesh")
            utils.run_cmd([r'./run_meshing2D.sh'])
        else:
            print("    Creating the mesh with snappyHexMesh")
            utils.run_cmd([r'./run_meshing.sh'])
        # os.system(f"cd {self.wd.joinpath('OF_Model')} && \
        #             echo '    Creating boundary mesh with blockMesh' &&\
        #             blockMesh &> {self.wd.joinpath('OF_Model')}/blockMesh.log"                       
        #                )
        # os.system(f"cd {self.wd.joinpath('OF_Model')} &&\
        #             echo '    Decomposing the mesh into 6 domains' &&\
        #             decomposePar -force &> {self.wd.joinpath('OF_Model')}/decomposeParMesh.log"
        #                 )
        # os.system(f"cd {self.wd.joinpath('OF_Model')} &&\
        #             echo '    Creating the mesh with snappyHexMesh'  &&\
        #             mpirun -np 6 snappyHexMesh -parallel -overwrite &> {self.wd.joinpath('OF_Model')}/snappyHexMesh.log"                 
        #                )
        # os.system(f"cd {self.wd.joinpath('OF_Model')}  &&\
        #             echo '    Reconstructing the mesh into 1 domain'  &&\
        #             reconstructParMesh -mergeTol 1e-06 -constant &> {self.wd.joinpath('OF_Model')}/reconstructParMesh.log"                 
        #                )
        # os.system(f"cd {self.wd.joinpath('OF_Model')} && \
        #             echo '    Checking the mesh' && \
        #             checkMesh &> checkMesh.log"                 
        #             )


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
        # os.system(f"cd {self.wd.joinpath('OF_Model')} &&\
        #             echo '    Decomposing' &&\
        #             starta=$SECONDS &&\
        #             decomposePar -force &> {self.wd.joinpath('OF_Model')}/decomposePar.log &&\
        #             echo '     - done in $SECONDS - $starta s'"
        #             )
        # os.system(f"cd {self.wd.joinpath('OF_Model')} &&\
        #             echo '    Running simpleFoam' &&\
        #             startb=$SECONDS &&\
        #             mpirun -np {n_par} simpleFoam -parallel &> {self.wd.joinpath('OF_Model')}/logs/simpleFoam{Re:0.4f}.log  &&\
        #             echo '     - done in $SECONDS - $startb s'"
        #             )
        # os.system(f"cd {self.wd.joinpath('OF_Model')} &&\
        #             echo '    Reconstructing'  &&\
        #             startc=$SECONDS  &&\
        #             reconstructPar &> {self.wd.joinpath('OF_Model')}/reconstructPar.log  &&\
        #             echo '     - done in $SECONDS - $startc s'"
        #             )
        

    def save_as_VTK(self) -> None:
        print("    Saving results in VTK format")
        # os.system(f"cd {self.wd.joinpath('OF_Model')} &&\
        #             echo '    Converting foam to VTK' &&\
        #             foamToVTK -latestTime -ascii  &> {self.wd.joinpath('OF_Model')}/foamToVTK.log"
        #             )


    def prep_convergence(self, Re: float) -> None:
        print("    Running foamLog")
        utils.run_cmd([r'./calc_convergence.sh', f'{Re:0.4f}'])
