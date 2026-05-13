from dataclasses import dataclass
     
# data_structure.xlsx structure made by Sarat
@dataclass
class ExcelOutputFormat:
    n_element:  int             # Number of Triangular Elements
    n_nodes:    int             # Number of Nodes
    ncon1:      list[int]       # Nodal Connectivity Matrix 
    ncon2:      list[int]       # Nodal Connectivity Matrix 
    ncon3:      list[int]       # Nodal Connectivity Matrix 
    X:          list[float]     # Node X Coords
    Y:          list[float]     # Node Y Coords
    E:          float           # Young's Modulus
    A:          int             # Area -> purposeless (calculated in MATLAB)
    F:          list[float]     # Force Array, Tuples of force, [1000, 0] represents a 1000N Force in the x direction
    NDU:        int             # Nodal Degrees of Freedom Unconstrained (Number of non-fixed Nodes)
    dzero:      list[int]       # Increment for number of Nodes (if n=4 -> 1,2,3,4) Again purposeless, but I don't make the rules :/
    v:          float           # Poission's Ratio
    t:          float           # Uniform thickness of 2D element
