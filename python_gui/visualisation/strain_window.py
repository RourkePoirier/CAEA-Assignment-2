import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

class StrainWindow(tk.Frame):
    def __init__(self, X, Y, Ex, Ey, Exy, n_element, n_nodes, ncon, tab):
        self.n_element = n_element
        self.n_nodes = n_nodes
        self.ncon = ncon
        triangles = ncon[:n_element]
        
        # Von Mises equivalent strain
        VM_strain = np.sqrt(Ex**2 - Ex*Ey + Ey**2 + 0.75 * Exy**2)

        fig = Figure()

        stress_plots = [
            (Ex,       None,    'Normal Strain X'),
            (Ey,       None,    'Normal Strain Y'),
            (Exy,      None,    'Shear Strain XY'),
            (VM_strain,'hot_r', 'Von Mises Equivalent Strain'),
        ]
 
        for idx, (stress, cmap, title) in enumerate(stress_plots):
            row, col = divmod(idx, 2)
            ax = fig.add_subplot(2, 2, idx + 1)
            node_strain = self.elem_to_node(stress) / 1000
            p = ax.tripcolor(X, Y, triangles, node_strain, cmap=cmap, shading='gouraud')
            ax.triplot(X, Y, triangles, color='k', linewidth=0.3, alpha=0.2)
            fig.colorbar(p, ax=ax, orientation='horizontal', pad=0.05)
            ax.set_aspect('equal')
            ax.set_title(title, fontsize=9)
            ax.axis('off')

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)
 
    def elem_to_node(self, vals):
        node_vals   = np.zeros(self.n_nodes)
        node_counts = np.zeros(self.n_nodes)
        for i in range(self.n_element):
            n1, n2, n3 = self.ncon[i]
            for n in [n1, n2, n3]:
                node_vals[n]   += vals[i]
                node_counts[n] += 1
        return node_vals / node_counts


if __name__ == "__main__":
    root = tk.Tk()
    pw = PropertiesWindow(root)
    pw.pack(padx=20, pady=20)
    root.mainloop()
