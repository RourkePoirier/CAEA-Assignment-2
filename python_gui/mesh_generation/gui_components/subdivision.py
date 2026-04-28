
from typing import List
from data_types import Node, NodeType, Triangle


def subdivide_triangular_mesh(nodes: List[Node], triangles: List[Triangle], subd_level: int) -> tuple[List[Node], List[Triangle]]:
    
    working_nodes = list(nodes)  # local copy, never touches caller's list

    for _ in range(subd_level):
        new_triangles = []
        edge_midpoint_cache: dict[tuple[int, int], int] = {}

        def get_or_create_midpoint(i: int, j: int) -> int:
            key = (min(i, j), max(i, j))
            if key in edge_midpoint_cache:
                return edge_midpoint_cache[key]

            n1, n2 = working_nodes[i], working_nodes[j]
            mid_node = Node((n1.x + n2.x) / 2, (n1.y + n2.y) / 2, n1.type if n1.type == n2.type else NodeType.NORMAL)
            mid_idx = len(working_nodes)
            working_nodes.append(mid_node)
            edge_midpoint_cache[key] = mid_idx
            return mid_idx

        for tri in triangles:
            i0, i1, i2 = tri.node_ids
            m01 = get_or_create_midpoint(i0, i1)
            m12 = get_or_create_midpoint(i1, i2)
            m20 = get_or_create_midpoint(i2, i0)
            new_triangles.extend([
                Triangle((i0,  m01, m20)),
                Triangle((m01, i1,  m12)),
                Triangle((m20, m12, i2 )),
                Triangle((m01, m12, m20)),
            ])

        triangles = new_triangles

    return working_nodes, triangles
    
