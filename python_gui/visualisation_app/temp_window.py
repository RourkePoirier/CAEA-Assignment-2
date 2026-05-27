import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import matplotlib.tri as mtri

class TempWindow(tk.Frame):
    def __init__(self, X, Y, ncon, n_element, temperature_C, tab):

        fig = Figure()
        ax = fig.add_subplot(111)

        if temperature_C is None or (isinstance(temperature_C, np.ndarray) and np.all(np.isnan(temperature_C))):
            ax.text(
                0.5,
                0.5,
                "No thermal results found.\nRun Project 2 to generate project2_results.xlsx",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.axis("off")
        else:
            triang = mtri.Triangulation(X, Y, triangles=ncon[:n_element])

            tvals = np.asarray(temperature_C, dtype=float)
            im = ax.tripcolor(triang, tvals, shading="gouraud", cmap="inferno")
            ax.triplot(triang, color="k", linewidth=0.2, alpha=0.35)

            fig.colorbar(im, ax=ax, label="Temperature (°C)")

            ax.set_aspect("equal")
            ax.set_title("Nodal Temperature")
            ax.axis("off")

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
 
if __name__ == "__main__":
    # Visualisation app entrypoint is `main.py`.
    pass
