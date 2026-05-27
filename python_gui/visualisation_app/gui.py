##########################################################################################

# Imports
import pandas as pd
import tkinter as tk
from tkinter import ttk
import numpy as np

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from displacement_window import DisplacementWindow
from stress_window import StressWindow
from strain_window import StrainWindow
from temp_window import TempWindow

##########################################################################################

class GUIManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Data Visualisation")
        self.root.geometry("1200x800")
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)  # handle close button

        # Read data
        try:
            data   = pd.read_excel('data_structure.xlsx', header=None, skiprows=1).values
            #U      = pd.read_excel('displacement.xlsx',   header=None).values.flatten()
            #Sx     = pd.read_excel('stress_x.xlsx',       header=None).values.flatten()
            #Sy     = pd.read_excel('stress_y.xlsx',       header=None).values.flatten()
            #Sxy    = pd.read_excel('stress_xy.xlsx',      header=None).values.flatten()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to read Excel files: {e}")
            self.root.destroy()
            return

        # Optional Project 2 thermal results (loaded after we know n_nodes below)
        temperature_C = None

        # Parse structure parameters (matching MATLAB hardcoded positions)
        n_element = int(data[0, 0])
        n_nodes   = int(data[0, 1])
        E         = float(data[0, 7])
        v         = float(data[0, 12])

        # Optional Project 2 thermal results
        try:
            temp_df = pd.read_excel('project2_results.xlsx', sheet_name='temperature_results')
            # Expected columns from ThermalSolver_1.m:
            # Node, X_original, Y_original, X_m, Y_m, Temperature_C
            if 'Node' in temp_df.columns and 'Temperature_C' in temp_df.columns:
                temperature_C = np.full(n_nodes, np.nan, dtype=float)
                for _, row in temp_df.iterrows():
                    node_id = int(row['Node'])
                    if 1 <= node_id <= n_nodes:
                        temperature_C[node_id - 1] = float(row['Temperature_C'])
        except Exception:
            temperature_C = None

        # Only take first n_element rows for connectivity
        ncon = data[:n_element, 2:5].astype(int) - 1  # 0-indexed

        # Only take rows with valid X/Y data (first n_nodes rows that aren't NaN)
        xy = data[:, 5:7]
        valid = ~np.isnan(xy[:, 0])
        X = xy[valid, 0]
        Y = xy[valid, 1]

        triangles = ncon[:n_element]

        # trim to exactly n_nodes
        X = X[:n_nodes]
        Y = Y[:n_nodes]

        # Notebook with three
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=1)

        '''
        # Strain from plane stress constitutive relations
        Ex  = (Sx - v * Sy) / E
        Ey  = (Sy - v * Sx) / E
        Exy = Sxy * 2 * (1 + v) / E

        #
        #   Page 1 - Displacement
        #

        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text='Deformation')

        DisplacementWindow(X, Y, U, n_element, ncon, tab1) 

        #
        #   Page 2 - Stress
        #

        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text='Stress')

        StressWindow(X, Y, Sx, Sy, Sxy, n_element, n_nodes, ncon, tab2)


        #
        #   Page 3 - Strain
        #

        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text='Strain')

        StrainWindow(X, Y, Ex, Ey, Exy, n_element, n_nodes, ncon, tab3)
        '''
        #
        #   Page 4 - Temperature
        #

        tab4 = ttk.Frame(notebook)
        notebook.add(tab4, text='Temperature')

        TempWindow(X, Y, ncon, n_element, temperature_C, tab4)

    def on_close(self):
        plt.close('all')
        self.root.quit()
        self.root.destroy()

# ---------- RUN ----------
    def run(self):
        self.root.mainloop()


