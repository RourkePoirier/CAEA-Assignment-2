# CAEA Assignment 1

## Authorship

Modified from code provided by Sarat in lectures

Python and MATLAB Development by
- Matthew Smith 22173112
- Steve Millar 21131046
- Rourke Poirer 22171432
- Jackson Long 19084617

## Overview

A 2D finite element analysis application that reads mesh and load data from Excel, solves for nodal displacements, and computes element stresses using triangular elements. The application provides mesh generation and visualization tools.

## How to Run

Launch the MATLAB app GUI:

```matlab
start_program.mlapp
```

Run in MATLAB and click buttons to execute each program stage. Alternatively, run `Main.m` directly in MATLAB to perform the FEA solve.

## Components

- **MATLAB FEA Solver** (`Main.m`): Reads `data_structure.xlsx`, assembles stiffness matrix, applies boundary conditions, and outputs displacement and stress results to Excel.
- **Mesh Generation GUI** (`python_gui/mesh_generation`): Create and edit triangular meshes with node properties.
- **Visualization GUI** (`python_gui/visualisation`): Display mesh data and analysis results.

