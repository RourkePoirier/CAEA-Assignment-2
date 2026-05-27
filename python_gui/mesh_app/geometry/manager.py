#
# Title: geometry_manager.py
# Author: Matthew Smith 22173112
# Date: 4/05/26
# Purpose: Store and access all geometry through this class
#

import math

from geometry.components import *
from collections import Counter

MAX_SUBDIVISION_LEVEL = 3

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

        # Edges between adjacent placed nodes (convex hull order) — used for tool selection
        self.placed_edges: list[Edge] = []

        # Outer mesh edges (convecting unless endpoint nodes have temperature set)
        self.boundary_edges: list[Edge] = []

        # Fixed temperature BC per boundary edge, keyed by sorted endpoint positions
        self.edge_fixed_temps: dict[tuple, float] = {}
        
        # Thermal BC type per boundary edge (default convection if not set)
        self.edge_thermal_types: dict[tuple, ThermalType] = {}
        self.rake_edge:  Edge | None = None
        self.flank_edge: Edge | None = None

        self.subd_level: int = 0

    ## Accessors
    def get_placed_edges(self) -> list[Edge]:    return self.placed_edges
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

    def get_boundary_edges(self) -> list[Edge]:
        return self.boundary_edges

    def get_edge_fixed_temperature(self, edge: Edge) -> float | None:
        if not self.base_nodes: return None
        return self.edge_fixed_temps.get(self._edge_pos_key(edge, self.base_nodes))

    def get_edge_thermal_type(self, edge: Edge) -> ThermalType:
        if not self.base_nodes: return ThermalType.CONVECTION
        return self.edge_thermal_types.get(self._edge_pos_key(edge, self.base_nodes), ThermalType.CONVECTION)

    def set_edge_thermal_type(self, edge: Edge, thermal_type: ThermalType) -> None:
        if not self.base_nodes:
            return
        key = self._edge_pos_key(edge, self.base_nodes)
        if thermal_type == ThermalType.CONVECTION:
            self.edge_thermal_types.pop(key, None)
        else:
            self.edge_thermal_types[key] = thermal_type

    def set_edge_fixed_temperature(self, edge: Edge, temperature: float) -> None:
        if not self.base_nodes:
            return
        key = self._edge_pos_key(edge, self.base_nodes)
        self.edge_fixed_temps[key] = temperature
        self.edge_thermal_types[key] = ThermalType.FIXED_TEMP
        self._recompute_node_temperatures()

    def clear_edge_fixed_temperature(self, edge: Edge) -> None:
        if not self.base_nodes:
            return
        key = self._edge_pos_key(edge, self.base_nodes)
        self.edge_fixed_temps.pop(key, None)
        if self.edge_thermal_types.get(key) == ThermalType.FIXED_TEMP:
            self.edge_thermal_types.pop(key, None)
        self._recompute_node_temperatures()

    def set_edge_insulated(self, edge: Edge) -> None:
        if not self.base_nodes:
            return
        key = self._edge_pos_key(edge, self.base_nodes)
        self.edge_fixed_temps.pop(key, None)
        self.edge_thermal_types[key] = ThermalType.INSULATED
        self._recompute_node_temperatures()

    def clear_edge_thermal_bc(self, edge: Edge) -> None:
        if not self.base_nodes:
            return
        key = self._edge_pos_key(edge, self.base_nodes)
        self.edge_fixed_temps.pop(key, None)
        self.edge_thermal_types.pop(key, None)
        self._recompute_node_temperatures()

    def _edge_length(self, edge: Edge) -> float:
        na, nb = edge.get_nodes(self.base_nodes)
        return math.hypot(nb.x - na.x, nb.y - na.y)

    def _recompute_node_temperatures(self) -> None:
        self._clear_all_temperatures()
        if not self.base_nodes: return

        contributions: dict[tuple[float, float], list[tuple[float, float]]] = {}
        for edge in self.boundary_edges:
            temp = self.edge_fixed_temps.get(self._edge_pos_key(edge, self.base_nodes))
            if temp is None: continue
            length = self._edge_length(edge)
            na, nb = edge.get_nodes(self.base_nodes)
            for pos in ((na.x, na.y), (nb.x, nb.y)):
                contributions.setdefault(pos, []).append((temp, length))

        for node in self.base_nodes:
            pairs = contributions.get((node.x, node.y))
            if not pairs: continue
            total_len = sum(length for _, length in pairs)
            if total_len <= 0: continue
            blended = sum(temp * length for temp, length in pairs) / total_len
            self._set_node_temperature(node, blended)

    def _set_node_temperature(self, node: Node, temperature: float | None) -> None:
        node.temp = temperature
        for placed in self.placed_nodes:
            if placed.x == node.x and placed.y == node.y:
                placed.temp = temperature

    def _clear_all_temperatures(self) -> None:
        for node in (*self.base_nodes, *self.placed_nodes):
            node.temp = None

    def _edge_pos_key(self, edge: Edge, nodes: list[Node]) -> tuple[tuple[float, float], tuple[float, float]]:
        na, nb = edge.get_nodes(nodes)
        return tuple(sorted(((na.x, na.y), (nb.x, nb.y))))

    def _collect_edge_temperature_bcs(self) -> dict[tuple, float]:
        return dict(self.edge_fixed_temps)

    def _restore_edge_temperature_bcs(self, preserved: dict[tuple, float]) -> None:
        surviving = {self._edge_pos_key(edge, self.base_nodes) for edge in self.boundary_edges}
        self.edge_fixed_temps = {k: v for k, v in preserved.items() if k in surviving}
        self._recompute_node_temperatures()

    def _collect_edge_thermal_types(self) -> dict[tuple, ThermalType]:
        return dict(self.edge_thermal_types)

    def _restore_edge_thermal_types(self, preserved: dict[tuple, ThermalType]) -> None:
        surviving = {self._edge_pos_key(edge, self.base_nodes) for edge in self.boundary_edges}
        self.edge_thermal_types = {k: v for k, v in preserved.items() if k in surviving}

    def _compute_placed_edges(self) -> None:
        from scipy.spatial import ConvexHull
        import numpy as np

        self.placed_edges = []
        if len(self.placed_nodes) < 2:
            return

        if len(self.placed_nodes) == 2:
            # Only two placed nodes — one edge between them
            pos = {(n.x, n.y): i for i, n in enumerate(self.base_nodes)}
            ia = pos.get((self.placed_nodes[0].x, self.placed_nodes[0].y))
            ib = pos.get((self.placed_nodes[1].x, self.placed_nodes[1].y))
            if ia is not None and ib is not None:
                self.placed_edges.append(Edge(node_indices=(ia, ib)))
            return

        pts = np.array([[n.x, n.y] for n in self.placed_nodes])
        try:
            hull = ConvexHull(pts)
        except Exception:
            return

        # Map placed node coords → base_nodes index (nodes were copied, so match by position)
        pos_to_base = {(n.x, n.y): i for i, n in enumerate(self.base_nodes)}

        hull_verts = list(hull.vertices)
        for k in range(len(hull_verts)):
            pa = self.placed_nodes[hull_verts[k]]
            pb = self.placed_nodes[hull_verts[(k + 1) % len(hull_verts)]]
            ia = pos_to_base.get((pa.x, pa.y))
            ib = pos_to_base.get((pb.x, pb.y))
            if ia is not None and ib is not None:
                self.placed_edges.append(Edge(node_indices=(ia, ib)))

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
        self.boundary_edges.clear()
        self.placed_edges.clear()
        self.edge_fixed_temps.clear()
        self.edge_thermal_types.clear()
        self.rake_edge  = None
        self.flank_edge = None
        self.subd_level = 0

    ## Update — single method that recomputes everything from the manually placed_nodes
    def update(self) -> None:
        preserved_bcs = self._collect_edge_temperature_bcs()
        preserved_types = self._collect_edge_thermal_types()

        self.base_nodes, self.base_elements = generate_mesh(self.placed_nodes, self.scheme)
        self.nodes, self.elements = subdivide_triangular_mesh(self.base_nodes, self.base_elements, self.subd_level)
        self._compute_boundary_edges()
        self._compute_placed_edges()
        self._restore_edge_temperature_bcs(preserved_bcs)
        self._restore_edge_thermal_types(preserved_types)
        self._validate_edge_tags()

    def _validate_edge_tags(self) -> None:
        valid = set(self.boundary_edges)
        if self.rake_edge  not in valid: self.rake_edge  = None
        if self.flank_edge not in valid: self.flank_edge = None

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