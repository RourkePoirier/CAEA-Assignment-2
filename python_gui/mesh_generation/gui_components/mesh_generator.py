# mesh_generator.py
#
# Hi Rourke - extend this to implement whatever triangulation logic :)
# Currently there is a dalanuay implementation I am wrapping from scipy library
# So long as you follow the function signature (input: List of Nodes | Output List of Triangles)
# Then any algorithm can be implemented here and it should show up nicely :)

from typing import List
from scipy.spatial import Delaunay, ConvexHull
import numpy as np
import tkinter as tk

from data_types import Node, Triangle, MeshScheme, NodeType

def generate_triangular_mesh(nodes: List[Node], mesh_method: tk.StringVar) -> List[Triangle]:

    # No triangles if there are less than 3 nodes xD
    if len(nodes) < 3: return []

    value = mesh_method.get()
    
    match mesh_method.get():
        case MeshScheme.DELAUNAY.value:         return _delaunay(nodes)
        case MeshScheme.RADIAL.value:           return _radial(nodes)
        case MeshScheme.ADVANCING_FRONT.value:  return _advancing_front(nodes)
        case MeshScheme.NOTHING.value:          return []
        case _:
            print(f"Unknown mesh scheme: {mesh_method.get()}, falling back to Delaunay")
            return _delaunay(nodes)

# -- Algorithms --
def _delaunay(nodes: List[Node]) -> List[Triangle]:
    if len(nodes) < 3:
        return []

    # Convert nodes to numpy array
    points = np.array([[n.x, n.y] for n in nodes])
    tri = Delaunay(points)

    triangles: List[Triangle] = []

    for simplex in tri.simplices:
        i0, i1, i2 = simplex  # indices into nodes list
        n0, n1, n2 = nodes[i0], nodes[i1], nodes[i2]

        # Ensure CCW orientation
        if not _is_ccw(n0, n1, n2):
            i1, i2 = i2, i1  # swap indices, not Node objects
        
        triangles.append(Triangle(node_ids=(i0, i1, i2)))

    return triangles

def _advancing_front(nodes: List[Node]) -> List[Triangle]:
    """
    Advancing front method. Starts from convex hull edges and grows
    inward by placing new points at the average edge length of the
    input node distribution. Falls back to Delaunay on the full
    point cloud (including generated interior points) at the end,
    which gives clean results consistent with the front placement.
    """
    points = np.array([[n.x, n.y] for n in nodes])
 
    if len(points) < 3:
        return []
 
    # Target edge length: average nearest-neighbour distance
    from scipy.spatial import cKDTree
    tree = cKDTree(points)
    dists, _ = tree.query(points, k=2)
    target_len = float(np.median(dists[:, 1]))
 
    if target_len == 0:
        return _delaunay(nodes)
 
    hull = ConvexHull(points)
    front = [hull.vertices[i] for i in range(len(hull.vertices))]
    front.append(front[0])  # close loop
 
    # Seed interior points along each front edge
    interior_pts = list(points)
 
    for k in range(len(front) - 1):
        p0 = points[front[k]]
        p1 = points[front[k + 1]]
        edge_len = np.linalg.norm(p1 - p0)
        n_div = max(1, int(round(edge_len / target_len)))
 
        for j in range(1, n_div):
            t = j / n_div
            mid = p0 + t * (p1 - p0)
            # Push slightly inward (toward centroid)
            centroid = points.mean(axis=0)
            inward = centroid - mid
            norm = np.linalg.norm(inward)
            if norm > 0:
                mid = mid + (inward / norm) * target_len * 0.4
            interior_pts.append(mid)
 
    all_pts = np.array(interior_pts)
 
    # Build nodes from all points
    working_nodes = [Node(p[0], p[1], NodeType.NORMAL) for p in all_pts]
 
    # Delaunay on the enriched point set
    tri = Delaunay(all_pts)
    triangles: List[Triangle] = []
 
    for simplex in tri.simplices:
        i0, i1, i2 = simplex
        n0, n1, n2 = working_nodes[i0], working_nodes[i1], working_nodes[i2]
        if not _is_ccw(n0, n1, n2):
            i1, i2 = i2, i1
        triangles.append(Triangle(node_ids=(i0, i1, i2)))
 
    return _remap_to_used_nodes(working_nodes, triangles)


def _radial(nodes: List[Node]) -> List[Triangle]:
    """
    Computes the convex hull of the placed nodes, places a centroid node,
    and fans triangles from the centroid to each hull edge.
    Works best for convex or roughly convex point clouds.
    """
    points = np.array([[n.x, n.y] for n in nodes])
 
    if len(points) < 3:
        return []
 
    hull = ConvexHull(points)
    hull_indices = list(hull.vertices)
 
    # Close the hull loop
    hull_indices.append(hull_indices[0])
 
    # Centroid node
    cx = points[:, 0].mean()
    cy = points[:, 1].mean()
 
    # Build a working node list: original nodes + centroid
    working_nodes = list(nodes)
    centroid = Node(cx, cy, NodeType.NORMAL)
    centroid_idx = len(working_nodes)
    working_nodes.append(centroid)
 
    triangles: List[Triangle] = []
 
    for k in range(len(hull_indices) - 1):
        i0 = hull_indices[k]
        i1 = hull_indices[k + 1]
        n0, n1 = working_nodes[i0], working_nodes[i1]
 
        # Ensure CCW
        if not _is_ccw(n0, n1, centroid):
            i0, i1 = i1, i0
 
        triangles.append(Triangle(node_ids=(i0, i1, centroid_idx)))
 
    return _remap_to_used_nodes(working_nodes, triangles)



def _nothing(nodes: List[Node]) -> List[Triangle]:
    return []

# -- Helper Methods --
def _is_ccw(n1: Node, n2: Node, n3: Node) -> bool:
    return (n2.x - n1.x)*(n3.y - n1.y) - (n2.y - n1.y)*(n3.x - n1.x) > 0

def _remap_to_used_nodes(all_nodes: List[Node], triangles: List[Triangle]):
    """
    Strips unused nodes and remaps triangle indices so the returned
    node list contains only nodes that appear in at least one triangle.
    """
    used = set()
    for tri in triangles:
        used.update(tri.node_ids)
 
    old_to_new = {old: new for new, old in enumerate(sorted(used))}
    new_nodes = [all_nodes[i] for i in sorted(used)]
    new_triangles = [
        Triangle(node_ids=(old_to_new[i0], old_to_new[i1], old_to_new[i2]))
        for i0, i1, i2 in (tri.node_ids for tri in triangles)
    ]
    return new_nodes, new_triangles

