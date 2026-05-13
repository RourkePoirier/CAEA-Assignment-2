import tkinter as tk
from tkinter import simpledialog, messagebox

class ForceDialog(simpledialog.Dialog):
    
    def __init__(self, parent, title="Define Force"):
        self.magnitude = None
        self.angle = None
        self.is_pxy = None
        self.is_pz = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Magnitude (N):").grid(row=0, column=0, sticky="w")
        self.mag_entry = tk.Entry(master)
        self.mag_entry.grid(row=0, column=1)
        
        tk.Label(master, text="Angle (deg):").grid(row=1, column=0, sticky="w")
        self.angle_entry = tk.Entry(master)
        self.angle_entry.grid(row=1, column=1)

        self.pxy_var = tk.IntVar()
        self.pz_var = tk.IntVar()

        tk.Checkbutton(master, text="Pxy", variable=self.pxy_var, command=self._on_pxy).grid(row=2, column=0, sticky="w")
        tk.Checkbutton(master, text="Pz",  variable=self.pz_var, command=self._on_pz).grid(row=2, column=1, sticky="w")

        return self.mag_entry

    def _on_pxy(self):
        if self.pxy_var.get():
            self.pz_var.set(0)   # uncheck Pz if Pxy selected

    def _on_pz(self):
        if self.pz_var.get():
            self.pxy_var.set(0)  # uncheck Pxy if Pz selected

    def validate(self):
        try:
            self.magnitude = float(self.mag_entry.get())
            self.angle = float(self.angle_entry.get())
            self.is_pxy = bool(self.pxy_var.get())
            self.is_pz = bool(self.pz_var.get())
            return True
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter numeric values")
            return False

    def apply(self):
        pass