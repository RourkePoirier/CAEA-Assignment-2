import math
import pandas as pd

from geometry.components.types import *
from geometry.manager import GeometryManager


EXCEL_FILENAME = "data_structure.xlsx"


def _get_prop(properties: dict, key: str, default):
    if properties is None:
        return default
    return properties.get(key, default)


def _build_sheet1_dataframe(geometry: GeometryManager, properties: dict) -> pd.DataFrame:
    nodes = geometry.get_nodes()
    elements = geometry.get_elements()
    forces = geometry.get_forces()

    n_element = len(elements)
    n_nodes = len(nodes)
    ncon1, ncon2, ncon3 = [], [], []
    x_coords = [node.x for node in nodes]
    y_coords = [node.y for node in nodes]
    force_vector = [0.0] * (2 * n_nodes)

    # Map node coordinates to 1-based node IDs for MATLAB.
    node_index_map = {(node.x, node.y): i + 1 for i, node in enumerate(nodes)}

    for element in elements:
        n1, n2, n3 = element.get_nodes(nodes)
        ncon1.append(node_index_map[(n1.x, n1.y)])
        ncon2.append(node_index_map[(n2.x, n2.y)])
        ncon3.append(node_index_map[(n3.x, n3.y)])

    for force in forces:
        angle_rad = math.radians(force.angle)
        force_x = round(force.magnitude * math.cos(angle_rad), 4)
        force_y = round(force.magnitude * math.sin(angle_rad), 4)
        node_pos = (force.node.x, force.node.y)
        if node_pos not in node_index_map:
            continue
        idx = node_index_map[node_pos] - 1
        force_vector[2 * idx] += force_x
        force_vector[2 * idx + 1] += force_y

    dzero = []
    for i, node in enumerate(nodes):
        if node.type == NodeType.FIXED_NODE:
            dof_base = 2 * (i + 1)
            dzero.append(dof_base - 1)
            dzero.append(dof_base)

    e_modulus = _get_prop(properties, "Young's Modulus", 0)
    poisson = _get_prop(properties, "Poisson's Ratio", 0)
    thickness = _get_prop(properties, "Thickness", 0)
    area = 0
    ndu = len(dzero)

    max_len = max(
        1,
        len(force_vector),
        len(x_coords),
        len(y_coords),
        len(dzero),
        len(ncon1),
        len(ncon2),
        len(ncon3),
    )

    def pad(value):
        seq = value if isinstance(value, list) else [value]
        if len(seq) >= max_len:
            return seq[:max_len]
        return seq + [None] * (max_len - len(seq))

    return pd.DataFrame(
        {
            "n_element": pad(n_element),
            "n_nodes": pad(n_nodes),
            "ncon1": pad(ncon1),
            "ncon2": pad(ncon2),
            "ncon3": pad(ncon3),
            "X": pad(x_coords),
            "Y": pad(y_coords),
            "E": pad(e_modulus),
            "A": pad(area),
            "F": pad(force_vector),
            "NDU": pad(ndu),
            "dzero": pad(dzero),
            "v": pad(poisson),
            "t": pad(thickness),
        }
    )


def _build_cutting_data_dataframe(properties: dict) -> pd.DataFrame:
    rows = [
        ("Vc_m_min", _get_prop(properties, "Cutting speed", 0)),
        ("depth_cut_mm", _get_prop(properties, "Depth of cut", 0)),
        ("feed_mm_rev", _get_prop(properties, "Feed", 0)),
        ("rake_angle_deg", _get_prop(properties, "Rake angle", 0)),
        ("a2_mm", _get_prop(properties, "Chip thickness (a2)", 0)),
        ("L_contact_mm", _get_prop(properties, "Chip tool contact length (L)", 0)),
        ("Pz_N", _get_prop(properties, "Cutting force (Pz)", 0)),
        ("Pxy_N", _get_prop(properties, "Feed Force (Pxy)", 0)),
        ("heat_fraction_tool", _get_prop(properties, "Heat fraction tool", 0.3)),
        ("flank_heat_fraction", _get_prop(properties, "Flank heat fraction", 0.2)),
    ]
    return pd.DataFrame(rows, columns=["parameter", "value"])


def _build_thermal_properties_dataframe(properties: dict) -> pd.DataFrame:
    rows = [
        ("kx_W_mK", _get_prop(properties, "Thermal Conductivity X (Kx)", 85)),
        ("ky_W_mK", _get_prop(properties, "Thermal Conductivity Y (Ky)", 85)),
        ("thickness_m", _get_prop(properties, "Thickness", 0)),
        ("T_fixed_C", _get_prop(properties, "Fixed Temperature (T)", 20)),
        ("T_infinity_C", _get_prop(properties, "Ambient Temperature (T inf)", 20)),
        ("geometry_units", _get_prop(properties, "Geometry Units", "mm")),
    ]
    return pd.DataFrame(rows, columns=["parameter", "value"])


def _build_thermal_bc_dataframe(geometry: GeometryManager, properties: dict) -> pd.DataFrame:
    rows = []

    # base_nodes holds the pre-subdivision nodes whose indices boundary_edges reference.
    # nodes holds the full subdivided set — this is where sub-edge nodes live.
    base_nodes = geometry.base_nodes if geometry.base_nodes else geometry.get_nodes()
    all_nodes  = geometry.get_nodes()

    # 1-based MATLAB index map built from the full subdivided node list.
    node_index_map = {(node.x, node.y): i + 1 for i, node in enumerate(all_nodes)}

    h_default   = _get_prop(properties, "Convection Coefficient (h)", 0)
    T_inf       = _get_prop(properties, "Ambient Temperature (T inf)", 20)

    def nodes_along_edge(na: "Node", nb: "Node") -> list["Node"]:
        """
        Return every node in the subdivided mesh that lies on the segment na→nb,
        sorted from na to nb.  Works by projecting each candidate onto the segment
        and keeping those whose perpendicular distance is within a small tolerance.
        """
        dx = nb.x - na.x
        dy = nb.y - na.y
        len_sq = dx * dx + dy * dy
        if len_sq == 0:
            return [na]

        tol = 1e-6 * math.sqrt(len_sq)   # scale tolerance with edge length
        candidates: list[tuple[float, "Node"]] = []

        for node in all_nodes:
            cx = node.x - na.x
            cy = node.y - na.y
            # Perpendicular distance (cross product magnitude)
            if abs(cx * dy - cy * dx) > tol * math.sqrt(len_sq):
                continue
            # Parametric position along the edge
            t = (cx * dx + cy * dy) / len_sq
            if -1e-9 <= t <= 1 + 1e-9:
                candidates.append((t, node))

        candidates.sort(key=lambda p: p[0])
        return [node for _, node in candidates]

    for edge in geometry.get_boundary_edges():
        # Resolve endpoints through base_nodes (boundary_edges use base_nodes indices).
        na, nb = edge.get_nodes(base_nodes)

        # Collect all subdivided nodes along this edge, ordered na → nb.
        segment_nodes = nodes_along_edge(na, nb)
        if len(segment_nodes) < 2:
            segment_nodes = [na, nb]   # fallback: just the two endpoints

        # Resolve thermal properties once for the parent edge.
        is_rake  = (edge == geometry.rake_edge)
        is_flank = (edge == geometry.flank_edge)

        if not (is_rake or is_flank):
            thermal_type = geometry.get_edge_thermal_type(edge)
            fixed_temp   = (
                geometry.get_edge_fixed_temperature(edge)
                if thermal_type == ThermalType.FIXED_TEMP
                else None
            )

        # Emit one BC row per consecutive sub-segment pair.
        for i in range(len(segment_nodes) - 1):
            n_a = segment_nodes[i]
            n_b = segment_nodes[i + 1]
            idx1 = node_index_map.get((n_a.x, n_a.y))
            idx2 = node_index_map.get((n_b.x, n_b.y))
            if idx1 is None or idx2 is None:
                continue

            if is_rake:
                rows.append(("heat",      idx1, idx2, "AutoRake",  None))
            elif is_flank:
                rows.append(("heat",      idx1, idx2, "AutoFlank", None))
            elif thermal_type == ThermalType.INSULATED:
                rows.append(("insulated", idx1, idx2, None,        None))
            elif thermal_type == ThermalType.FIXED_TEMP:
                rows.append(("fixed",     idx1, idx2, fixed_temp,  None))
            else:
                rows.append(("conv",      idx1, idx2, h_default,   T_inf))

    return pd.DataFrame(rows, columns=["type", "node_1", "node_2", "value_or_keyword", "T_infinity_C"])


def export_excel_file(geometry: GeometryManager, properties: dict | None = None):
    properties = properties or {}

    sheet1_df = _build_sheet1_dataframe(geometry, properties)
    cutting_df = _build_cutting_data_dataframe(properties)
    thermal_props_df = _build_thermal_properties_dataframe(properties)
    thermal_bc_df = _build_thermal_bc_dataframe(geometry, properties)

    with pd.ExcelWriter(EXCEL_FILENAME) as writer:
        sheet1_df.to_excel(writer, sheet_name="Sheet1", index=False)
        cutting_df.to_excel(writer, sheet_name="cutting_data", index=False)
        thermal_props_df.to_excel(writer, sheet_name="thermal_properties", index=False)
        thermal_bc_df.to_excel(writer, sheet_name="thermal_bc", index=False)


def export_elastostatic_excel_file(geometry: GeometryManager, properties: dict | None = None):
    # Backward-compatible entrypoint name.
    export_excel_file(geometry, properties)