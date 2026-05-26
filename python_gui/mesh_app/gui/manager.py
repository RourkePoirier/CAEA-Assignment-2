#
# Title: gui_manager.py
# Author: Matthew Smith 22173112
# Date: 19/03/26, 4/05/26
# Purpose:
#    Manages the layout of all Tkinter elements on the window
#    Plumbs GUI elements to function calls
#

import tkinter as tk

from gui.components import *

from geometry.components.types import *
from geometry.manager import GeometryManager

from data.exporter import export_excel_file

e_properties = [
    ("Young's Modulus", "Pa"),
    ("Thickness", "m"),
    ("Poisson's Ratio", ""),
]

c_properties = [
    ("Cutting speed", "m/min"),
    ("Depth of cut", "mm"),
    ("Feed", "mm/rev"),
    ("Rake angle", "deg"),
    ("Chip Thickness (a2)", "mm"),
    ("Chip tool contact length (L)", "mm"),
]

t_properties = [
    ("")
]


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

        elastostatics_properties = PropertiesWindow(self.root, label='Elastostatic Properties', entries=e_properties, width=250, height=600)
        cutting_tool_properties = PropertiesWindow(self.root, label='Cutting Tool Properties', entries=c_properties, width=250, height=600)

        mesh_select = MeshSelectDropdown(
            self.root,
            on_change=lambda scheme: [self.geometry.set_scheme(scheme), viewport._redraw()]
        )

        self.components["mesh_select"] = mesh_select

        clear_button  = tk.Button(self.root, text="Clear viewport", command=viewport.clear)
        exp_button    = tk.Button(
            self.root,
            text="Export to data_structure.xlsx",
            command=lambda: export_excel_file(self.geometry, elastostatics_properties.get_dict()),
        )
        subd_up_btn   = tk.Button(self.root, text="Subdivide +", command=lambda: [self.geometry.subdivide_up(),   viewport._redraw()])
        subd_down_btn = tk.Button(self.root, text="Subdivide -", command=lambda: [self.geometry.subdivide_down(), viewport._redraw()])

        viewport.place                  (x=50,   y=50)
        elastostatics_properties.place  (x=900,  y=50)
        cutting_tool_properties.place   (x=900,  y=175)
        mesh_select.place               (x=900,  y=350)
        subd_up_btn.place               (x=1000, y=500)
        subd_down_btn.place             (x=900,  y=500)
        clear_button.place              (x=938,  y=530)
        exp_button.place                (x=900,  y=580)

    # ---------- RUN ----------
    def run(self):
        self.root.mainloop()