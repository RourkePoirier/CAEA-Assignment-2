
#
# Title: subdivision.py
# Author: Matthew Smith
# Date: 4/05/26
# Purpose:

"""
Subdivides each triangle into 4 smaller triangles, repeated subd_level times.

Each triangle:

    i0                   i0
    /\          ->       /\ 
   /  \                m20--m01
  /    \               /\  /\ 
 i2----i1            i2--m12--i1

"""

from typing import List
from geometry.components.types import *

def subdivide_triangular_mesh(nodes: List[Node], elements: List[Element], subd_level: int) -> tuple[List[Node], List[Element]]:

    working_nodes = list(nodes)

    for _ in range(subd_level):

        # Cache midpoints so shared edges don't create duplicate nodes
        midpoint_cache: dict[tuple[int, int], int] = {}

        def get_or_create_midpoint(i: int, j: int) -> int:
            # Sort indices so (i,j) and (j,i) map to the same cache entry
            key = (min(i, j), max(i, j))

            if key in midpoint_cache: return midpoint_cache[key]

            # Create midpoint node between node i and node j
            a, b = working_nodes[i], working_nodes[j]
            midpoint = Node(
                x    = (a.x + b.x) / 2,
                y    = (a.y + b.y) / 2,
                type = a.type if a.type == b.type else NodeType.NODE
            )

            # Register midpoint and cache its index
            mid_idx = len(working_nodes)
            working_nodes.append(midpoint)
            midpoint_cache[key] = mid_idx
            return mid_idx

        # Split each triangle into 4 smaller triangles
        new_elements = []
        for e in elements:
            i0, i1, i2 = e.node_indices

            # Create a midpoint on each edge
            m01 = get_or_create_midpoint(i0, i1)
            m12 = get_or_create_midpoint(i1, i2)
            m20 = get_or_create_midpoint(i2, i0)

            # Build the 4 sub-triangles
            new_elements.extend([
                Element((i0,  m01, m20)),   # top corner
                Element((m01, i1,  m12)),   # bottom-right corner
                Element((m20, m12, i2 )),   # bottom-left corner
                Element((m01, m12, m20)),   # centre
            ])

        elements = new_elements

    return working_nodes, elements