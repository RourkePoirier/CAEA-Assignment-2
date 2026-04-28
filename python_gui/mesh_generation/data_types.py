from dataclasses import dataclass
from typing import Tuple, List
from enum import Enum, StrEnum

# -- Enums --

# Tool is the viewport tool type
class Tool(Enum):
    NODE = 1
    FIXED_NODE = 2
    FORCE = 3

# Node type roughly matches tool but for future development they are split types
class NodeType(Enum):
    NORMAL = 1
    FIXED = 2
    FORCE = 3
     
# Different types of mesh generation schemes
@dataclass
class MeshScheme(StrEnum):
    DELAUNAY        = "Delauny"         # Delaunay triangulation (scipy)
    RADIAL          = "Radial"          # Fan from centroid to convex hull
    ADVANCING_FRONT = "Advancing Front" # Advancing front from boundary inward
    NOTHING         = "Nothing"

# -- Classes --

@dataclass
class Node:
    def __init__(self, x: float, y: float, type: NodeType, node_id=None):
        self.x = x
        self.y = y
        self.type = type
        self.id = node_id if node_id is not None else id(self)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id

@dataclass
class Triangle:

    # Instead of copying into array, store pointers to nodes - more efficient
    node_ids: Tuple[int, int, int]  

    def get_nodes(self, nodes: list[Node]):
        return [nodes[i] for i in self.node_ids]

@dataclass
class Force:
    node: Node
    angle: float
    magnitude: float

# data_structure.xlsx structure made by Sarat
@dataclass
class ExcelOutputFormat:
    n_element:  int             # Number of Triangular Elements
    n_nodes:    int             # Number of Nodes
    ncon1:      List[int]       # Nodal Connectivity Matrix 
    ncon2:      List[int]       # Nodal Connectivity Matrix 
    ncon3:      List[int]       # Nodal Connectivity Matrix 
    X:          List[float]     # Node X Coords
    Y:          List[float]     # Node Y Coords
    E:          float           # Young's Modulus
    A:          int             # Area -> purposeless (calculated in MATLAB)
    F:          List[float]     # Force Array, Tuples of force, [1000, 0] represents a 1000N Force in the x direction
    NDU:        int             # Nodal Degrees of Freedom Unconstrained (Number of non-fixed Nodes)
    dzero:      List[int]       # Increment for number of Nodes (if n=4 -> 1,2,3,4) Again purposeless, but I don't make the rules :/
    v:          float           # Poission's Ratio
    t:          float           # Uniform thickness of 2D element
