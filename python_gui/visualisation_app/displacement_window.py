import pandas as pd
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def create_displacement_window(tab):
    try:
        data = pd.read_excel('data_structure.xlsx', header=None, skiprows=1).values
        U    = pd.read_excel('displacement.xlsx',   header=None).values.flatten()
    except:
        return

    n_element = int(data[0, 0])
    n_nodes   = int(data[0, 1])

    ncon = data[:n_element, 2:5].astype(int) - 1  # 0-indexed

    xy    = data[:, 5:7]
    valid = ~np.isnan(xy[:, 0])
    X     = xy[valid, 0][:n_nodes]
    Y     = xy[valid, 1][:n_nodes]

    fig = Figure()
    ax  = fig.add_subplot(111)

    mesh_size = max(X.max() - X.min(), Y.max() - Y.min())
    scale     = 0.1 * mesh_size / np.max(np.abs(U))

    for i in range(n_element):
        n1, n2, n3 = ncon[i]

        x_orig = [X[n1], X[n2], X[n3], X[n1]]
        y_orig = [Y[n1], Y[n2], Y[n3], Y[n1]]

        u1, v1 = U[2*n1], U[2*n1+1]
        u2, v2 = U[2*n2], U[2*n2+1]
        u3, v3 = U[2*n3], U[2*n3+1]

        x_def = [X[n1] + scale*u1, X[n2] + scale*u2, X[n3] + scale*u3, X[n1] + scale*u1]
        y_def = [Y[n1] + scale*v1, Y[n2] + scale*v2, Y[n3] + scale*v3, Y[n1] + scale*v1]

        ax.plot(x_orig, y_orig, color='blue', linewidth=1, label='Original' if i == 0 else "")
        ax.plot(x_def,  y_def,  color='red',  linewidth=2, label='Deformed' if i == 0 else "")

    ax.set_aspect('equal')
    ax.legend()
    ax.set_title('FEA Structure: Original vs Deformed')
    ax.axis('off')

    canvas = FigureCanvasTkAgg(fig, master=tab)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
