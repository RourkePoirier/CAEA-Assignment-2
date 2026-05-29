import tkinter as tk
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.tri as mtri


def create_temp_window(tab):
    try:
        data = pd.read_excel('data_structure.xlsx', header=None, skiprows=1).values
    except:
        return

    n_element = int(data[0, 0])
    n_nodes   = int(data[0, 1])

    temperature_C = None

    try:
        temp_df = pd.read_excel('project2_results.xlsx', sheet_name='temperature_results')
        if 'Node' in temp_df.columns and 'Temperature_C' in temp_df.columns:
            temperature_C = np.full(n_nodes, np.nan, dtype=float)
            for _, row in temp_df.iterrows():
                node_id = int(row['Node'])
                if 1 <= node_id <= n_nodes:
                    temperature_C[node_id - 1] = float(row['Temperature_C'])
    except Exception:
        temperature_C = None

    ncon  = data[:n_element, 2:5].astype(int) - 1  # 0-indexed

    xy    = data[:, 5:7]
    valid = ~np.isnan(xy[:, 0])
    X     = xy[valid, 0][:n_nodes]
    Y     = xy[valid, 1][:n_nodes]

    fig = Figure()
    ax  = fig.add_subplot(111)

    if temperature_C is None or np.all(np.isnan(temperature_C)):
        ax.text(
            0.5, 0.5,
            "No thermal results found.\nRun Project 2 to generate project2_results.xlsx",
            ha="center", va="center", transform=ax.transAxes,
        )
        ax.axis("off")
    else:
        triang = mtri.Triangulation(X, Y, triangles=ncon[:n_element])
        tvals  = np.asarray(temperature_C, dtype=float)
        im     = ax.tripcolor(triang, tvals, shading="gouraud", cmap="inferno")
        ax.triplot(triang, color="k", linewidth=0.2, alpha=0.35)
        fig.colorbar(im, ax=ax, label="Temperature (°C)")
        ax.set_aspect("equal")
        ax.set_title("Nodal Temperature")
        ax.axis("off")

    canvas = FigureCanvasTkAgg(fig, master=tab)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
