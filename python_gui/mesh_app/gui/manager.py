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

m_properties = [
    ("Young's Modulus", "Pa"),
    ("Thickness", "m"),
    ("Poisson's Ratio", ""),
]

p_properties = [
    ("Cutting speed", "m/min"),
    ("Depth of cut", "mm"),
    ("Feed", "mm/rev"),
    ("Cutting force (Pz)", "N"),
    ("Feed Force (Pxy)", "N"),
]

t_properties = [
    ("Convection Coefficient (h)", "W/m^2 * K"),
    ("Thermal Conductivity X (Kx)", "W/m*K"),
    ("Thermal Conductivity Y (Ky)", "W/m*K"),
    ("Fixed Temperature (T)", "deg C"),
    ("Ambient Temperature (T inf)", "deg C"),
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

        mechanical_properties = PropertiesWindow(self.root, label='Mechanical Properties', entries=m_properties, width=250, height=600)
        process_properties = PropertiesWindow(self.root, label='Process Properties', entries=p_properties, width=250, height=600)
        thermal_properties = PropertiesWindow(self.root, label='Thermal Properties', entries=t_properties, width=250, height=600)
        self.components["mechanical_properties"] = mechanical_properties
        self.components["process_properties"] = process_properties
        self.components["thermal_properties"] = thermal_properties

        mesh_select = MeshSelectDropdown(
            self.root,
            on_change=lambda scheme: [self.geometry.set_scheme(scheme), viewport._redraw()]
        )

        self.components["mesh_select"] = mesh_select

        clear_button  = tk.Button(self.root, text="Clear viewport", command=viewport.clear)
        exp_button    = tk.Button(
            self.root,
            text="Export to data_structure.xlsx",
            command=lambda: export_excel_file(self.geometry, self._collect_properties()),
        )
        subd_up_btn   = tk.Button(self.root, text="Subdivide +", command=lambda: [self.geometry.subdivide_up(),   viewport._redraw()])
        subd_down_btn = tk.Button(self.root, text="Subdivide -", command=lambda: [self.geometry.subdivide_down(), viewport._redraw()])

        viewport.place                  (x=50,   y=50)
        mechanical_properties.place     (x=900,  y=50)
        process_properties.place        (x=900,  y=150)
        thermal_properties.place        (x=900,  y=300)
        mesh_select.place               (x=900,  y=450)
        subd_up_btn.place               (x=1000, y=550)
        subd_down_btn.place             (x=900,  y=550)
        clear_button.place              (x=938,  y=580)
        exp_button.place                (x=900,  y=630)

    # ---------- RUN ----------
    def _collect_properties(self) -> dict:
        props = {}
        for key in ("mechanical_properties", "process_properties", "thermal_properties"):
            widget = self.components.get(key)
            if widget is not None:
                props.update(widget.get_dict())
        return props

    def run(self):
        self.root.mainloop()
