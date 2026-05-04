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
    DELAUNAY        = "Delaunay"        # Fixed typo: "Delauny" -> "Delaunay"
    RADIAL          = "Radial"
    ADVANCING_FRONT = "Advancing Front"
    NOTHING         = "Nothing"

class NodeType(Enum):
    NORMAL = 1  # Removed trailing commas — they create single-element tuples
    FIXED  = 2
    FORCE  = 3

##########################################################################

@dataclass
class Node:
    x:    float
    y:    float
    type: NodeType
    id:   int = field(default_factory=lambda: id(object()))

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id

@dataclass
class Element:
    node_indices: tuple[int, int, int]  # Fixed typo: indicies -> indices

    def get_nodes(self, nodes: list[Node]) -> tuple[Node, Node, Node]:
        a, b, c = self.node_indices
        return nodes[a], nodes[b], nodes[c]

@dataclass
class Edge:
    node_indices: tuple[int, int]       # Fixed typo: indicies -> indices

    def get_nodes(self, nodes: list[Node]) -> tuple[Node, Node]:
        a, b = self.node_indices
        return nodes[a], nodes[b]

@dataclass
class Force:
    node:      Node
    angle:     float
    magnitude: float

##########################################################################