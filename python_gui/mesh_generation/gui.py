
#
#
# Title: gui.py
# Author: Matthew Smith 22173112
# Date: 19/03/26
# Purpose:
#    Manages drawing the main tkinter frame and placement of "widgets" on screen
#    
#
##########################################################################################

# Imports
import tkinter as tk
import pandas as pd
import math

from gui_components.viewport import Viewport
from gui_components.properties_window import PropertiesWindow
from gui_components.mesh_gen_window import MeshGenWindow
from data_types import ExcelOutputFormat, NodeType, MeshScheme

##########################################################################################

class GUIManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mesh App")
        self.root.geometry("1200x800")
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

        # Store components in array
        self.components = {}

        # Function to array all components nicely on screen
        self.build_layout()

    # ---------- LAYOUT ----------
    def build_layout(self):

        mesh_method = tk.StringVar()
        #mesh_method.trace_add("write", lambda *_: print(mesh_method.get()))

        # Viewport
        plot = Viewport(self.root, mesh_method=mesh_method, subdivision_level=2, width=800, height=600)
        plot.place(x=50, y=50)
        self.components["plot"] = plot

        # Side panel
        properties = PropertiesWindow(self.root, width=250, height=600)
        properties.place(x=900, y=50)
        self.components["properties"] = properties

        # Side panel
        mesh_panel = MeshGenWindow(self.root, mesh_method=mesh_method, on_change=plot.regenerate, width=250, height=600)
        mesh_panel.place(x=900, y=175)

        self.components["properties"] = properties
        
        # Buttons
        clear_viewport_button = tk.Button(self.root, text="Clear viewport", command=self.clear_viewport)
        exp_button = tk.Button(self.root, text="Export to data_structure.xlsx", command=self.export_excel)
        subdivide_up_button = tk.Button(text="Subdivide +", command=self.subd_up)
        subdivide_down_button = tk.Button(text="Subdivide -", command=self.subd_down)

        # Place buttons #HARDCODED
        subdivide_up_button.place   (x=1000, y=360)
        subdivide_down_button.place (x=900, y=360)
        clear_viewport_button.place (x=900, y=400)
        exp_button.place            (x=900, y=440)
        

    # ---------- BUSINESS LOGIC ----------
    def subd_up(self):
        self.components["plot"].subd_up()
        
    def subd_down(self):
        self.components["plot"].subd_down()

    def clear_viewport(self):
        self.components["plot"].clear()

    # TODO: Check if all the proper values are there, E, t and v
    def export_excel(self):
        output = self.construct_output()
        self.write_data_structure_to_excel(output, filename='data_structure.xlsx')  

    def construct_output(self):

        try:
            #############################################################
            ### Get Nodes and material Properties from gui components ###
            #############################################################
            nodes = self.components["plot"].get_nodes()
            triangles = self.components["plot"].get_triangles()
            forces = self.components["plot"].get_forces()
            material_properties = self.components["properties"].get_material_properties()

            ################################
            ### Construct data_structure ###
            ################################

            n_element = len(triangles)
            n_nodes = len(nodes)
            ncon1, ncon2, ncon3 = [], [], []    # Populated later
            X = [node.x for node in nodes]
            Y = [node.y for node in nodes] 
            F = [0.0] * (2 * n_nodes)                              # Populated later
            A = 0                               # Area is handled in MATLAB -> here for poserity


            # Map Node objects to 1-based indices by position (x, y)
            # This handles node identity issues when mesh is regenerated/subdivided
            node_index_map = {(node.x, node.y): i+1 for i, node in enumerate(nodes)}

            for tri in triangles:
                n1, n2, n3 = tri.get_nodes(nodes)
                ncon1.append(node_index_map[(n1.x, n1.y)])
                ncon2.append(node_index_map[(n2.x, n2.y)])
                ncon3.append(node_index_map[(n3.x, n3.y)])
                
            # For each force, calculate x and y component (to 4dp) and append to output array
            for force in forces:
                angle_rad = math.radians(force.angle)
                force_x = round(force.magnitude * math.cos(angle_rad), 4)
                force_y = round(force.magnitude * math.sin(angle_rad), 4)

                # Resolve force to node by position (x, y) instead of ID
                node_pos = (force.node.x, force.node.y)
                if node_pos in node_index_map:
                    node_idx = node_index_map[node_pos] - 1  # 0-based
                    F[2*node_idx]   += force_x
                    F[2*node_idx+1] += force_y

            dzero = []
            for i, node in enumerate(nodes):
                if node.type == NodeType.FIXED:
                    dof_x = 2 * (i + 1) - 1  # x DOF (1-based)
                    dof_y = 2 * (i + 1)       # y DOF (1-based)
                    dzero.append(dof_x)
                    dzero.append(dof_y)

            # Boundary Conditions
            NDU = len(dzero)    # NDU is the number of non-fixed nodes

            # Material Properties if not exist set to zero
            try: E = material_properties["Young's Modulus"] 
            except: E = 0

            try: v = material_properties["Poisson's Ratio"]
            except: v = 0

            try: t = material_properties["Thickness"]
            except: t = 0

            # Assign variables to ExcelOutputFormat
            output = ExcelOutputFormat(
                    n_element=n_element,
                    n_nodes=n_nodes,
                    ncon1=ncon1,
                    ncon2=ncon2,
                    ncon3=ncon3,
                    X=X,
                    Y=Y,
                    E=E,
                    A=0,
                    F=F,
                    NDU=NDU,
                    dzero=dzero,
                    v=v,
                    t=t
                )

            return output

        except Exception as e:
            raise e

    def write_to_excel(self, data, header, filename):
        df_full = pd.DataFrame({
            header: data,
        })

        df_full.to_excel(filename, index=False)
    
    def write_data_structure_to_excel(self, output, filename):
        max_len = max(
            len(output.F),
            len(output.X),
            len(output.Y),
            len(output.dzero),
        )

        def pad(lst):
            if not isinstance(lst, list):
                lst = [lst]
            return lst + [None] * (max_len - len(lst))

        # Build full dataframe including ncon
        df_full = pd.DataFrame({
            "n_element": pad(output.n_element),
            "n_nodes":   pad(output.n_nodes),
            "ncon1":     pad(output.ncon1),
            "ncon2":     pad(output.ncon2),
            "ncon3":     pad(output.ncon3),
            "X":         pad(output.X),
            "Y":         pad(output.Y),
            "E":         pad(output.E),
            "A":         pad(output.A),
            "F":         pad(output.F),
            "NDU":       pad(output.NDU),
            "dzero":     pad(output.dzero),
            "v":         pad(output.v),
            "t":         pad(output.t),
        })    
        print(df_full.to_string())
        df_full.to_excel(filename, index=False)

    # ---------- RUN ----------
    def run(self):
        self.root.mainloop()

