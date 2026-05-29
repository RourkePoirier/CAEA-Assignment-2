import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt

from displacement_window import create_displacement_window
from stress_window        import create_stress_window
from strain_window        import create_strain_window
from temp_window          import create_temp_window


class GUIManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Data Visualisation")
        self.root.geometry("1200x800")
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=1)

        tabs = [
            ("Deformation",  create_displacement_window),
            ("Stress",       create_stress_window),
            ("Strain",       create_strain_window),
            ("Temperature",  create_temp_window),
        ]

        for label, create_fn in tabs:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=label)
            create_fn(tab)

    def on_close(self):
        plt.close('all')
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
