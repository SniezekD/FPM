# FPM - Flow through Porous Media

A toolchain for automating OpenFOAM simulations of fluid flow through
randomly generated porous media

All actions from geometry generation through OpenFOAM case setup and solving to post-processed transport metrics are inside a single pipeline. An experiment is
defined by a single, validated TOML configuration file.

## Overview

Studying flow through porous media normally means hand-building an OpenFOAM case for every geometry and flow condition: generating the pore structure, meshing it, writing the boundary conditions and solver dictionaries, running the solver, and reducing the output to physical quantities. FPM automates that whole loop. A single configuration file describes an experiment: the porous geometry, the mesh, the boundary conditions, and a sweep over porosities and flow velocities. Then the toolchain produces the corresponding OpenFOAM cases, runs them, and extracts the results.

## Pipeline

1. **Geometry** — generate a porous medium at a target porosity,with configurable size distribution and various boundary periodicities (`fpm/media_models`).
2. **Case generation** — render the OpenFOAM case (blockMesh, snappyHexMesh, boundary conditions, solver dictionaries) from Jinja templates (`fpm/openfoam_case.py`, `fpm/templates/`).
3. **Simulation** — simulate the model according to given specification.
4. **Post-processing** — compute related metrics from the resulting field (`fpm/utilities`).

## Requirements

- Python 3.12+
- [Poetry](https://python-poetry.org/) for dependency management
- OpenFOAM v12 for running simulations — provided by the included `Dockerfile`

## Defining an experiment

Everything about a run is specified in a single TOML file — the geometry, mesh, boundary conditions, solver options, and the porosity/velocity sweep. The schema mirrors OpenFOAM's own dictionary structure, and the configuration is validated when it loads: a missing key, a wrong type, or an out-of-range value fails immediately with a specific message rather than deep inside a run. 

A fully commented reference is provided at
[`examples/experiment_config.toml`](examples/experiment_config.toml).

> **Installation and usage** guides are being finalized alongside the run
> workflow and will be added shortly.

## Running an experiment 

In order to run the experiment, first build docker image. Run from the repo root:

`docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t fpm .`

Next, run the container. Remember to specify paths to results directory.  
```
mkdir -p <results_dir>
docker run -it \
    -v "<results_dir>":/results \
    -v "<path_to_experiment_config.toml>":/work/config.toml:ro \
    fpm \
    bash -c \
    "source /usr/lib/openfoam/openfoam2306/etc/bashrc && \
    cd /home/repos/FPM && \
    poetry run python scripts/automatic_runner.py --config-path /work/config.toml"
```

This is only temporary. In the future a single runner script will be provided.
