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

from data.exporter import save_geometry_to_excel

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
        exp_button    = tk.Button(self.root, text="Export to data_structure.xlsx", command=lambda: save_geometry_to_excel(self.geometry))
        subd_up_btn   = tk.Button(self.root, text="Subdivide +",                  command=lambda: [self.geometry.subdivide_up(),   viewport._redraw()])
        subd_down_btn = tk.Button(self.root, text="Subdivide -",                  command=lambda: [self.geometry.subdivide_down(), viewport._redraw()])

        viewport.place      (x=50,   y=50)
        properties.place    (x=900,  y=50)
        mesh_select.place   (x=900,  y=175)
        subd_up_btn.place   (x=1000, y=360)
        subd_down_btn.place (x=900,  y=360)
        clear_button.place  (x=900,  y=400)
        exp_button.place    (x=900,  y=440)

    # ---------- RUN ----------
    def run(self):
        self.root.mainloop()