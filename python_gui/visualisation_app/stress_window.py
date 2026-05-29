import pandas as pd
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


def elem_to_node(vals, n_nodes, n_element, ncon):
    node_vals   = np.zeros(n_nodes)
    node_counts = np.zeros(n_nodes)
    for i in range(n_element):
        n1, n2, n3 = ncon[i]
        for n in [n1, n2, n3]:
            node_vals[n]   += vals[i]
            node_counts[n] += 1
    return node_vals / node_counts

def create_stress_window(tab):
    try:
        data = pd.read_excel('data_structure.xlsx', header=None, skiprows=1).values
        Sx   = pd.read_excel('stress_x.xlsx',       header=None).values.flatten()
        Sy   = pd.read_excel('stress_y.xlsx',       header=None).values.flatten()
        Sxy  = pd.read_excel('stress_xy.xlsx',      header=None).values.flatten()
    except:
        return

    n_element = int(data[0, 0])
    n_nodes   = int(data[0, 1])

    ncon      = data[:n_element, 2:5].astype(int) - 1  # 0-indexed
    triangles = ncon[:n_element]

    xy    = data[:, 5:7]
    valid = ~np.isnan(xy[:, 0])
    X     = xy[valid, 0][:n_nodes]
    Y     = xy[valid, 1][:n_nodes]

    VM_stress = np.sqrt(Sx**2 - Sx*Sy + Sy**2 + 3*Sxy**2)

    fig = Figure()

    stress_plots = [
        (Sx,        None,    'Normal Stress X'),
        (Sy,        None,    'Normal Stress Y'),
        (Sxy,       None,    'Shear Stress XY'),
        (VM_stress, 'hot_r', 'Von Mises Equivalent Stress'),
    ]

    for idx, (stress, cmap, title) in enumerate(stress_plots):
        ax         = fig.add_subplot(2, 2, idx + 1)
        node_strain = elem_to_node(stress, n_nodes, n_element, ncon) / 1000
        p          = ax.tripcolor(X, Y, triangles, node_strain, cmap=cmap, shading='gouraud')
        ax.triplot(X, Y, triangles, color='k', linewidth=0.3, alpha=0.2)
        fig.colorbar(p, ax=ax, orientation='horizontal', pad=0.05)
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=9)
        ax.axis('off')

    canvas = FigureCanvasTkAgg(fig, master=tab)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
