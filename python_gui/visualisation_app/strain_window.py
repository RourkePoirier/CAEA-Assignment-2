import tkinter as tk
import pandas as pd
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


def create_strain_window(tab):
    try:
        data = pd.read_excel('data_structure.xlsx', header=None, skiprows=1).values
        Sx   = pd.read_excel('stress_x.xlsx',       header=None).values.flatten()
        Sy   = pd.read_excel('stress_y.xlsx',       header=None).values.flatten()
        Sxy  = pd.read_excel('stress_xy.xlsx',      header=None).values.flatten()
    except Exception as e:
        tk.messagebox.showerror("Error", f"Failed to read Excel files: {e}")
        return

    n_element = int(data[0, 0])
    n_nodes   = int(data[0, 1])
    E         = float(data[0, 7])
    v         = float(data[0, 12])

    ncon      = data[:n_element, 2:5].astype(int) - 1  # 0-indexed
    triangles = ncon[:n_element]

    xy    = data[:, 5:7]
    valid = ~np.isnan(xy[:, 0])
    X     = xy[valid, 0][:n_nodes]
    Y     = xy[valid, 1][:n_nodes]

    Ex  = (Sx - v * Sy) / E
    Ey  = (Sy - v * Sx) / E
    Exy = Sxy * 2 * (1 + v) / E

    VM_strain = np.sqrt(Ex**2 - Ex*Ey + Ey**2 + 0.75 * Exy**2)

    fig = Figure()

    strain_plots = [
        (Ex,        None,    'Normal Strain X'),
        (Ey,        None,    'Normal Strain Y'),
        (Exy,       None,    'Shear Strain XY'),
        (VM_strain, 'hot_r', 'Von Mises Equivalent Strain'),
    ]

    for idx, (strain, cmap, title) in enumerate(strain_plots):
        ax          = fig.add_subplot(2, 2, idx + 1)
        node_strain = elem_to_node(strain, n_nodes, n_element, ncon) / 1000
        p           = ax.tripcolor(X, Y, triangles, node_strain, cmap=cmap, shading='gouraud')
        ax.triplot(X, Y, triangles, color='k', linewidth=0.3, alpha=0.2)
        fig.colorbar(p, ax=ax, orientation='horizontal', pad=0.05)
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=9)
        ax.axis('off')

    canvas = FigureCanvasTkAgg(fig, master=tab)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
