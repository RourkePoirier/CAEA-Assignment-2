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
        case MeshScheme.RADIAL:          return _radial(nodes)
        case MeshScheme.ADVANCING_FRONT: return _advancing_front(nodes)
        case MeshScheme.NOTHING:         return nodes, []
        case _:
            print(f"Unknown mesh scheme: {scheme}, falling back to Delaunay")
            return _delaunay(nodes)


# -- Algorithms --

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