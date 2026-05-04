#
# Title: gui_manager.py
# Author: Matthew Smith 22173112
# Date: 19/03/26, 4/05/26
# Purpose:
#    Manages the layout of all Tkinter elements on the window
#    Plumbs GUI elements to function calls
#

import tkinter as tk
import math

from gui.components import *

from geometry.components.types import *
from geometry.manager import GeometryManager

from data_handling.types import ExcelOutputFormat

class GUIManager:

    def __init__(self, geometry: GeometryManager):
        self.geometry = geometry

        self.root = tk.Tk()
        self.root.title("Mesh App")
        self.root.geometry("1200x800")
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        self.components = {}
        self.build_layout()

    # ---------- LAYOUT ----------
    def build_layout(self):

        viewport = Viewport(self.root, self.geometry, width=800, height=600)
        self.components["viewport"] = viewport

        properties = PropertiesWindow(self.root, width=250, height=600)
        self.components["properties"] = properties

        mesh_select = MeshSelectDropdown(
            self.root,
            on_change=lambda scheme: [self.geometry.set_scheme(scheme), viewport._redraw()]
        )
        self.components["mesh_select"] = mesh_select

        # Fixed: removed () from command= so functions are passed, not called
        clear_button  = tk.Button(self.root, text="Clear viewport",               command=viewport.clear)
        exp_button    = tk.Button(self.root, text="Export to data_structure.xlsx", command=self.export_excel)
        subd_up_btn   = tk.Button(self.root, text="Subdivide +",                  command=lambda: [self.geometry.subdivide_up(),   viewport._redraw()])
        subd_down_btn = tk.Button(self.root, text="Subdivide -",                  command=lambda: [self.geometry.subdivide_down(), viewport._redraw()])

        viewport.place      (x=50,   y=50)
        properties.place    (x=900,  y=50)
        mesh_select.place   (x=900,  y=175)
        subd_up_btn.place   (x=1000, y=360)
        subd_down_btn.place (x=900,  y=360)
        clear_button.place  (x=900,  y=400)
        exp_button.place    (x=900,  y=440)

    # ---------- EXPORT ----------
    def export_excel(self):
        output = self.construct_output()
        self.write_data_structure_to_excel(output, filename='data_structure.xlsx')

    def construct_output(self):
        try:
            # Read all data from geometry manager
            nodes    = self.geometry.get_nodes()
            elements = self.geometry.get_elements()
            forces   = self.geometry.get_forces()
            material = self.components["properties"].get_material_properties()

            n_element = len(elements)
            n_nodes   = len(nodes)
            ncon1, ncon2, ncon3 = [], [], []
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

            E = material.get("Young's Modulus", 0)
            v = material.get("Poisson's Ratio", 0)
            t = material.get("Thickness",       0)

            return ExcelOutputFormat(
                n_element=n_element,
                n_nodes=n_nodes,
                ncon1=ncon1, ncon2=ncon2, ncon3=ncon3,
                X=X, Y=Y,
                E=E, A=0, F=F,
                NDU=len(dzero),
                dzero=dzero,
                v=v, t=t
            )

        except Exception as e:
            raise e

    # ---------- RUN ----------
    def run(self):
        self.root.mainloop()