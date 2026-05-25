import pandas as pd
import math
from geometry.components.types import *
from geometry.manager import GeometryManager

ELASTOSTATICS_FILENAME = 'data_structure.xlsx'

## REFERENCE
class ExcelOutputFormat:
    n_element:  int             # Number of Triangular Elements
    n_nodes:    int             # Number of Nodes
    ncon1:      list[int]       # Nodal Connectivity Matrix 
    ncon2:      list[int]       # Nodal Connectivity Matrix 
    ncon3:      list[int]       # Nodal Connectivity Matrix 
    X:          list[float]     # Node X Coords
    Y:          list[float]     # Node Y Coords
    E:          float           # Young's Modulus
    A:          int             # Area -> purposeless (calculated in MATLAB)
    F:          list[float]     # Force Array, Tuples of force, [1000, 0] represents a 1000N Force in the x direction
    NDU:        int             # Nodal Degrees of Freedom Unconstrained (Number of non-fixed Nodes)
    dzero:      list[int]       # Increment for number of Nodes (if n=4 -> 1,2,3,4) Again purposeless, but I don't make the rules :/
    v:          float           # Poission's Ratio
    t:          float           # Uniform thickness of 2D element



def export_elastostatic_excel_file(geometry: GeometryManager, properties: dict):
    try:
        # Read all data from geometry manager
        nodes    = geometry.get_nodes()
        elements = geometry.get_elements()
        forces   = geometry.get_forces()

        n_element = len(elements)
        n_nodes   = len(nodes)
        ncon1, ncon2, ncon3 = [], [], []
        A = 0
        X = [node.x for node in nodes]
        Y = [node.y for node in nodes]
        F = [0.0] * (2 * n_nodes)

        # Map (x, y) → 1-based node index
        node_index_map = {(node.x, node.y): i + 1 for i, node in enumerate(nodes)}

        for e in elements:
            n1, n2, n3 = e.get_nodes(nodes)
            ncon1.append(node_index_map[(n1.x, n1.y)])
            ncon2.append(node_index_map[(n2.x, n2.y)])
            ncon3.append(node_index_map[(n3.x, n3.y)])

        for force in forces:
            angle_rad = math.radians(force.angle)
            force_x   = round(force.magnitude * math.cos(angle_rad), 4)
            force_y   = round(force.magnitude * math.sin(angle_rad), 4)
            node_pos  = (force.node.x, force.node.y)
            if node_pos in node_index_map:
                idx = node_index_map[node_pos] - 1  # 0-based
                F[2 * idx]     += force_x
                F[2 * idx + 1] += force_y

        dzero = []
        for i, node in enumerate(nodes):
            if node.type == NodeType.FIXED:
                dzero.append(2 * (i + 1) - 1)  # x DOF (1-based)
                dzero.append(2 * (i + 1))       # y DOF (1-based)

        E = properties.get("Young's Modulus", 0)
        v = properties.get("Poisson's Ratio", 0)
        t = properties.get("Thickness",       0)
        
        NDU = len(dzero)

        # At least one row (matches generate_cutting_tool_data.m / readmatrix layout)
        max_len = max(
            1,
            len(F),
            len(X),
            len(Y),
            len(dzero),
            len(ncon1),
            len(ncon2),
            len(ncon3),
        )

        def pad(lst):
            if not isinstance(lst, list): lst = [lst]
            if len(lst) > max_len: return lst[:max_len]
            return lst + [None] * (max_len - len(lst))

        # Build full dataframe including ncon
        df_full = pd.DataFrame({
            "n_element": pad(n_element),
            "n_nodes":   pad(n_nodes),
            "ncon1":     pad(ncon1),
            "ncon2":     pad(ncon2),
            "ncon3":     pad(ncon3),
            "X":         pad(X),
            "Y":         pad(Y),
            "E":         pad(E),
            "A":         pad(A),
            "F":         pad(F),
            "NDU":       pad(NDU),
            "dzero":     pad(dzero),
            "v":         pad(v),
            "t":         pad(t),
        })    

        print(df_full.to_string())
        df_full.to_excel(ELASTOSTATICS_FILENAME, index=False)

    except Exception as e:
        raise e
