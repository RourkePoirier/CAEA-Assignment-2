import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class TempWindow(tk.Frame):
    def __init__(self, tab):

        fig = Figure()
        ax = fig.add_subplot(111)

        # Radii (make the hole clearly visible)
        R = 3.0   # major radius
        r = 1.0   # minor radius

        # Higher resolution = smoother torus
        u = np.linspace(0, 2*np.pi, 120)
        v = np.linspace(0, 2*np.pi, 60)
        u, v = np.meshgrid(u, v)

        # Parametric torus
        x = (R + r * np.cos(v)) * np.cos(u)
        y = (R + r * np.cos(v)) * np.sin(u)
        z = r * np.sin(v)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # IMPORTANT: equal aspect ratio
        ax.set_box_aspect([1, 1, 1])

        surf = ax.plot_surface(x, y, z, cmap='viridis', edgecolor='none')

        def update(frame):
            ax.view_init(elev=25, azim=frame)
            return surf,

        ani = FuncAnimation(fig, update, frames=np.arange(0, 360, 2), interval=40)
        ax.axis('off')

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
 
if __name__ == "__main__":
    root = tk.Tk()
    pw = PropertiesWindow(root)
    pw.pack(padx=20, pady=20)
    root.mainloop()
