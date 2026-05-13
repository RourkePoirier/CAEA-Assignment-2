#
# Title: geometry_manager.py
# Author: Matthew Smith 22173112
# Date: 4/05/26
# Purpose: Store and access all geometry through this class
#

from geometry.components import *
from collections import Counter

MAX_SUBDIVISION_LEVEL = 5

class GeometryManager:

    def __init__(self):
        # Placed nodes and forces — user defined
        self.placed_nodes: list[Node]  = []
        self.forces:       list[Force] = []

        # Mesh scheme
        self.scheme: MeshScheme = MeshScheme.DELAUNAY

        # Base mesh — generated from placed_nodes, never subdivided
        self.base_nodes:    list[Node]    = []
        self.base_elements: list[Element] = []

        # Working mesh — base mesh after subdivision
        self.nodes:    list[Node]    = []
        self.elements: list[Element] = []

        # Thermal Boundary Conditions
        self.boundary_edges: list[Edge] = []
        self.thermal_bcs:    dict[Edge, ThermalBC] = {}

        self.subd_level: int = 0

    ## Accessors
    def get_placed_nodes(self) -> list[Node]:    return self.placed_nodes
    def get_nodes(self)        -> list[Node]:    return self.nodes
    def get_elements(self)     -> list[Element]: return self.elements
    def get_forces(self)       -> list[Force]:   return self.forces

    ## Placed node/force modifiers
    def add_node(self, node: Node)       -> None: self.placed_nodes.append(node)
    def remove_node(self, node: Node)    -> None: self.placed_nodes.remove(node)
    def add_force(self, force: Force)    -> None: self.forces.append(force)
    def remove_force(self, force: Force) -> None: self.forces.remove(force)
    
    def node_exists_at(self, x: float, y: float) -> bool:
        return any(n.x == x and n.y == y for n in self.placed_nodes)

    def remove_node_at(self, x: float, y: float) -> None:
        self.placed_nodes = [n for n in self.placed_nodes if not (n.x == x and n.y == y)]
        self.forces       = [f for f in self.forces       if not (f.node.x == x and f.node.y == y)]

    # Thermal BC's
    def get_boundary_edges(self) -> list[Edge]: return self.boundary_edges
    def set_thermal_bc(self, edge: Edge, bc: ThermalBC) -> None: self.thermal_bcs[edge] = bc
    def get_thermal_bc(self, edge: Edge) -> ThermalBC | None: return self.thermal_bcs.get(edge)

    # Compute boundary edges from the base triangular elements
    # Used in to define Thermal Boundary Conditions
    def _compute_boundary_edges(self) -> None:
        edge_count = Counter()
        for el in self.base_elements:
            a, b, c = el.node_indices
            for pair in [(a,b), (b,c), (a,c)]:
                key = tuple(sorted(pair))
                edge_count[key] += 1

        self.boundary_edges = [
            Edge(node_indices=key)
            for key, count in edge_count.items()
            if count == 1
        ]
    
    def clear(self) -> None:
        self.placed_nodes.clear()
        self.forces.clear()
        self.base_nodes.clear()
        self.base_elements.clear()
        self.nodes.clear()
        self.elements.clear()
        self.subd_level = 0

    ## Update — single method that recomputes everything from the manually placed_nodes
    def update(self) -> None:
        self.base_nodes, self.base_elements = generate_mesh(self.placed_nodes, self.scheme)
        self.nodes, self.elements = subdivide_triangular_mesh(self.base_nodes, self.base_elements, self.subd_level)
        self._compute_boundary_edges()

    ## Subdivision
    def subdivide_up(self) -> bool:
        if self.subd_level < MAX_SUBDIVISION_LEVEL:
            self.subd_level += 1
            self.update()
            return True
        return False

    def subdivide_down(self) -> bool:
        if self.subd_level > 0:
            self.subd_level -= 1
            self.update()
            return True
        return False
    
    ## Mesh Generation
    def set_scheme(self, scheme: MeshScheme) -> None:
        self.scheme = scheme
        self.update()