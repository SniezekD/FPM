import os
import stl
import utils
import shutil
import numpy as np
import pyvista as pv
from mystl import grain, plane
from pathlib import Path
from stl import mesh

class IFPM:
    def __init__(self, porosity: float, size: dict, margin: int, working_dir: Path) -> None:
        self.porosity                = porosity
        self.size                    = size
        self.margin                  = margin
        self.wd                      = working_dir
        self.dimension               = len(self.size)
        self.lattice                 = self.porosity_lattice()
        self.stls, self.grains_names = self.translate_into_stl()


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
        lattice  = np.insert(lattice, 0, np.zeros((self.margin,self.size['y'],self.size['z'])), axis=0)
        lattice  = np.append(lattice,    np.zeros((self.margin,self.size['y'],self.size['z'])), axis=0)
        lattice  = lattice.transpose()

        # RETRUN LATTICE WITH MARGINS:
        return lattice

    def translate_into_stl(self):
        """
        Translates a lattice of zeros and ones into .stl format
        """
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
        
        grains       = []
        grains_names = []
        for z in range(self.lattice.shape[0]):
            for y in range(self.lattice.shape[1]):
                for x in range(self.lattice.shape[2]):
                    if self.lattice[z,y,x] == 1:
                        tmp_grain = grain(x,y,z)
                        grains_names.append(tmp_grain.name)
                        grains.append(tmp_grain.cube)


            grains_stl =  mesh.Mesh(np.concatenate([g.data for g in grains]))
            stls = {'inlet'     : inlet,
                    'outlet'    : outlet,
                    'wall_up'   : wall_up,
                    'wall_down' : wall_down,
                    'wall_front': wall_front,
                    'wall_back' : wall_back,
                    'grains'    : grains_stl}
            return stls, grains_names
    
    def prepare_model(self) -> None:
        print("    Preparing model")
        for stl_name in self.stls.keys():
            # save_path = self.wd.joinpath('OF_Model', 'constant', 'triSurface', f"{stl_name}.stl")
            save_path = f"/home/damian/MGR/IFPM/{stl_name}.stl"
            self.stls[stl_name].save(save_path, mode=stl.Mode.ASCII)
        utils.createBlockMeshDict(self.wd.joinpath('OF_Model', 'system', 'blockMeshDict'), self.size, self.margin)
        utils.createSnappyHexMeshDict(self.wd.joinpath('OF_Model', 'system', 'snappyHexMeshDict'))
        utils.run_cmd([r'./prep_model.sh'])

        # shutil.rmtree(self.wd.joinpath('OF_Model', '0'))
        # shutil.rmtree(self.wd.joinpath('OF_Model', 'constant', 'triSurface'))
        # os.makedirs(self.wd.joinpath('OF_Model', 'constant', 'triSurface', 'grains'), exist_ok=True)
        # os.makedirs(self.wd.joinpath('OF_Model', '0'), exist_ok=True)
        # self.wd.joinpath('OF_Model', '0', 'p').touch(exist_ok=True)
        # self.wd.joinpath('OF_Model', '0', 'U').touch(exist_ok=True)

    def run_meshing(self) -> None:
        """
        Runs OpenFOAM meshing commands (Mesh is done with snappyHexMesh tool)
        """
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

        U_file = open(self.wd.joinpath('OF_Model', '0', 'U'), "w")
        p_file = open(self.wd.joinpath('OF_Model', '0', 'p'), "w")
        utils.make_0_U(self.grains_names, U_file, Re)
        utils.make_0_p(self.grains_names, p_file)

    def run_single_simulation(self, Re: float, n_par: int = 6) -> None:
        """
        Runs SimpeFoam (an OpenFOAM solver) with parellisation into n_par processors.
        Setting the value of n_par into a value differnet than 6 (default) requires
        changes inside 'decomposeParDict' inside OF case directory. 
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
