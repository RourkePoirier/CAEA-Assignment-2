#
# Title: mesh_generator.py
# Author: Matthew Smith 22173112
# Date: 4/05/26
# Purpose: Generate triangular meshes from a set of placed nodes
#

from typing import List
from scipy.spatial import Delaunay, ConvexHull, cKDTree
import numpy as np

from geometry.components.types import *

def generate_mesh(nodes: List[Node], scheme: MeshScheme) -> tuple[List[Node], List[Element]]:
    """Entry point — returns (nodes, elements) for the given scheme."""

    if len(nodes) < 3: return nodes, []

    match scheme:
        case MeshScheme.DELAUNAY:        return _delaunay(nodes)
        case MeshScheme.AMR:             return _amr(nodes)
        case MeshScheme.RADIAL:          return _radial(nodes)
        case MeshScheme.ADVANCING_FRONT: return _advancing_front(nodes)
        case MeshScheme.NOTHING:         return nodes, []

# -- Algorithms --

# Mostly done
# Just need to tune a bit
def _amr(nodes: list[Node]) -> tuple[list[Node], list[Element]]:
    points = np.array([[n.x, n.y] for n in nodes])

    important_points = []

    for n in nodes:
        if n.type == NodeType.FORCE_NODE or n.temp != None:
            important_points.append([n.x, n.y])
        
    if len(important_points) == 0:
        return _delaunay(nodes)

    important_tree = cKDTree(important_points)
    tree = cKDTree(points)
    dists, _ = tree.query(points, k=2)
    base_len = float(np.median(dists[:, 1]))
    if base_len == 0:
        return _delaunay(nodes)

    hull = ConvexHull(points)
    bbox_diag = np.linalg.norm(points.max(axis=0) - points.min(axis=0))
    hull_area = hull.volume 
    influence_radius = np.sqrt(hull_area) * 0.67
    fine_len = min(base_len * 0.15, bbox_diag * 0.04)

    def _inside_hull(p: np.ndarray) -> bool:
        return bool(np.all(hull.equations @ np.append(p, 1) <= 1e-10))

    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    rng = np.random.default_rng(seed=42)
    refined_pts: list[np.ndarray] = []

    # Coarse background grid with distance-dependent spacing
    base_coarse = min(base_len * 1.8, bbox_diag * 0.15)
    max_coarse  = min(base_len * 4.0, bbox_diag * 0.3) 

    nx_c = int((x_max - x_min) / base_coarse) + 1
    ny_c = int((y_max - y_min) / base_coarse) + 1
    for ix in range(nx_c):
        for iy in range(ny_c):
            px = x_min + ix * base_coarse + rng.uniform(-base_coarse * 0.3, base_coarse * 0.3)
            py = y_min + iy * base_coarse + rng.uniform(-base_coarse * 0.3, base_coarse * 0.3)
            p  = np.array([px, py])

            if not _inside_hull(p):
                continue

            dist_to_force, _ = important_tree.query(p)
            t = min(dist_to_force / influence_radius, 1.0)

            # Local spacing grows from base_coarse → max_coarse with distance
            local_spacing = base_coarse + (max_coarse - base_coarse) * t

            # Randomly drop points whose local spacing is coarser than grid spacing
            keep_prob = (base_coarse / local_spacing) ** 2
            if rng.random() < keep_prob:
                refined_pts.append(p)

    coarse_len = min(base_len * 0.6, bbox_diag * 0.15)
    for vi in hull.vertices:
        corner = points[vi]
        dist_to_force, _ = important_tree.query(corner)
        t = min(dist_to_force / influence_radius, 1.0)
        local_len = coarse_len * (0.6 + 0.4 * t)

        n_rings = 3
        for ring in range(1, n_rings + 1):
            radius = local_len * ring
            n_pts = max(6, int(round(2 * np.pi * radius / local_len)))
            for k in range(n_pts):
                angle = 2 * np.pi * k / n_pts
                p = corner + radius * np.array([np.cos(angle), np.sin(angle)])
                if _inside_hull(p):
                    refined_pts.append(p)

    # Interior points
    nx = int((x_max - x_min) / fine_len) + 1
    ny = int((y_max - y_min) / fine_len) + 1

    for ix in range(nx):
        for iy in range(ny):
            px = x_min + ix * fine_len + rng.uniform(-fine_len * 0.3, fine_len * 0.3)
            py = y_min + iy * fine_len + rng.uniform(-fine_len * 0.3, fine_len * 0.3)
            p  = np.array([px, py])

            if not _inside_hull(p):
                continue

            dist_to_force, _ = important_tree.query(p)
            if dist_to_force >= influence_radius:
                continue

            t = dist_to_force / influence_radius
            keep_prob = (1.0 - t) ** 2
            if rng.random() < keep_prob:
                refined_pts.append(p)

    # Seed ALL hull edges, density increases near force nodes
    hull_verts = list(hull.vertices) + [hull.vertices[0]]
    for k in range(len(hull_verts) - 1):
        p0 = points[hull_verts[k]]
        p1 = points[hull_verts[k + 1]]

        edge_len = np.linalg.norm(p1 - p0)
        dist_to_force, _ = important_tree.query((p0 + p1) / 2)
        t = min(dist_to_force / influence_radius, 1.0)
        
        # Vary subdivision density along edge based on proximity to force
        local_edge_len = coarse_len * (0.4 + 0.6 * t)
        n_div = max(2, int(round(edge_len / local_edge_len)))
        
        for j in range(1, n_div):
            p = p0 + (j / n_div) * (p1 - p0)
            refined_pts.append(p)
    
    if not refined_pts:
        return _delaunay(nodes)

    all_pts = np.vstack([points] + [r[None] for r in refined_pts])
    rounded = np.round(all_pts / (fine_len * 0.5)).astype(int)
    _, unique_idx = np.unique(rounded, axis=0, return_index=True)
    all_pts = all_pts[np.sort(unique_idx)]

    working_nodes = [Node(p[0], p[1], NodeType.NODE) for p in all_pts]
    for i, n in enumerate(nodes):
        working_nodes[i].type = n.type

    tri = Delaunay(all_pts)
    elements: list[Element] = []
    for simplex in tri.simplices:
        i0, i1, i2 = simplex
        if not _is_ccw(working_nodes[i0], working_nodes[i1], working_nodes[i2]):
            i1, i2 = i2, i1
        elements.append(Element(node_indices=(i0, i1, i2)))

    return _remap_to_used_nodes(working_nodes, elements)

def _delaunay(nodes: List[Node]) -> tuple[List[Node], List[Element]]:
    points = np.array([[n.x, n.y] for n in nodes])
    tri    = Delaunay(points)

    elements: List[Element] = []
    for simplex in tri.simplices:
        i0, i1, i2 = simplex
        if not _is_ccw(nodes[i0], nodes[i1], nodes[i2]):
            i1, i2 = i2, i1
        elements.append(Element(node_indices=(i0, i1, i2)))

    return nodes, elements


def _radial(nodes: List[Node]) -> tuple[List[Node], List[Element]]:
    """
    Places a centroid node and fans triangles from it to each convex hull edge.
    Works best for convex point clouds.
    """
    points      = np.array([[n.x, n.y] for n in nodes])
    hull        = ConvexHull(points)
    hull_indices = list(hull.vertices) + [hull.vertices[0]]  # close loop

    centroid     = Node(points[:, 0].mean(), points[:, 1].mean(), NodeType.NODE)
    working_nodes = list(nodes) + [centroid]
    centroid_idx  = len(working_nodes) - 1

    elements: List[Element] = []
    for k in range(len(hull_indices) - 1):
        i0, i1 = hull_indices[k], hull_indices[k + 1]
        if not _is_ccw(working_nodes[i0], working_nodes[i1], centroid):
            i0, i1 = i1, i0
        elements.append(Element(node_indices=(i0, i1, centroid_idx)))

    return _remap_to_used_nodes(working_nodes, elements)


def _advancing_front(nodes: List[Node]) -> tuple[List[Node], List[Element]]:
    """
    Seeds interior points along convex hull edges pushed inward toward
    the centroid, then runs Delaunay on the enriched point cloud.
    """
    points = np.array([[n.x, n.y] for n in nodes])

    # Target edge length: median nearest-neighbour distance
    tree      = cKDTree(points)
    dists, _  = tree.query(points, k=2)
    target_len = float(np.median(dists[:, 1]))

    if target_len == 0:
        return _delaunay(nodes)

    hull     = ConvexHull(points)
    front    = list(hull.vertices) + [hull.vertices[0]]
    centroid = points.mean(axis=0)

    # Seed midpoints along each hull edge, pushed slightly inward
    interior_pts = list(points)
    for k in range(len(front) - 1):
        p0, p1 = points[front[k]], points[front[k + 1]]
        n_div  = max(1, int(round(np.linalg.norm(p1 - p0) / target_len)))
        for j in range(1, n_div):
            mid    = p0 + (j / n_div) * (p1 - p0)
            inward = centroid - mid
            norm   = np.linalg.norm(inward)
            if norm > 0:
                mid = mid + (inward / norm) * target_len * 0.4
            interior_pts.append(mid)

    all_pts       = np.array(interior_pts)
    working_nodes = [Node(p[0], p[1], NodeType.NODE) for p in all_pts]

    tri      = Delaunay(all_pts)
    elements: List[Element] = []
    for simplex in tri.simplices:
        i0, i1, i2 = simplex
        if not _is_ccw(working_nodes[i0], working_nodes[i1], working_nodes[i2]):
            i1, i2 = i2, i1
        elements.append(Element(node_indices=(i0, i1, i2)))

    return _remap_to_used_nodes(working_nodes, elements)


# -- Helpers --

def _is_ccw(n1: Node, n2: Node, n3: Node) -> bool:
    return (n2.x - n1.x) * (n3.y - n1.y) - (n2.y - n1.y) * (n3.x - n1.x) > 0

def _remap_to_used_nodes(nodes: List[Node], elements: List[Element]) -> tuple[List[Node], List[Element]]:
    """Strips unused nodes and remaps element indices to match the compacted node list."""
    used       = sorted({i for e in elements for i in e.node_indices})
    old_to_new = {old: new for new, old in enumerate(used)}
    new_nodes  = [nodes[i] for i in used]
    new_elements = [
        Element(node_indices=(old_to_new[i0], old_to_new[i1], old_to_new[i2]))
        for i0, i1, i2 in (e.node_indices for e in elements)
    ]
    return new_nodes, new_elements
