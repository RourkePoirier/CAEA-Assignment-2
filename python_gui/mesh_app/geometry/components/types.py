#
# Title: geometry/types.py
# Author: Matthew Smith
# Date: 4/05/26
# Purpose: Primitives for geometric representation
#

from dataclasses import dataclass, field
from enum import Enum, StrEnum

##########################################################################

class MeshScheme(StrEnum):
    DELAUNAY        = "Delaunay"
    RADIAL          = "Radial"
    ADVANCING_FRONT = "Advancing Front"
    NOTHING         = "Nothing"

class NodeType(Enum):
    NODE        = 1 
    FIXED_NODE  = 2
    FORCE_NODE  = 3

class ThermalType(Enum):
    CONVECTION = 1
    FIXED_TEMP = 2
    INSULATED  = 3

##########################################################################

@dataclass
class Node:
    x:              float
    y:              float
    type:           NodeType
    temp:     float | None = None
    id:             int = field(default_factory=lambda: id(object()))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id

@dataclass
class Element:
    node_indices: tuple[int, int, int]

    def get_nodes(self, nodes: list[Node]) -> tuple[Node, Node, Node]:
        a, b, c = self.node_indices
        return nodes[a], nodes[b], nodes[c]

@dataclass(frozen=True)
class Edge:
    node_indices: tuple[int, int]
    thermal_type: ThermalType | None = None

    def get_nodes(self, nodes: list[Node]) -> tuple[Node, Node]:
        a, b = self.node_indices
        return nodes[a], nodes[b]

@dataclass
class Force:
    node:      Node
    angle:     float
    magnitude: float

THERMAL_FIXED_TEMP_COLOUR = "#FF5E00"
RAKE_COLOUR  = "#AA00FF"
FLANK_COLOUR = "#FF6600"

##########################################################################