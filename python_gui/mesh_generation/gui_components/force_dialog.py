import tkinter as tk
from tkinter import simpledialog

class ForceDialog(simpledialog.Dialog):
    def __init__(self, parent, title="Define Force"):
        self.magnitude = None
        self.angle = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Magnitude (N):").grid(row=0, column=0, sticky="w")
        self.mag_entry = tk.Entry(master)
        self.mag_entry.grid(row=0, column=1)
        
        tk.Label(master, text="Angle (deg):").grid(row=1, column=0, sticky="w")
        self.angle_entry = tk.Entry(master)
        self.angle_entry.grid(row=1, column=1)
        
        return self.mag_entry  # initial focus

    def validate(self):
        try:
            self.magnitude = float(self.mag_entry.get())
            self.angle = float(self.angle_entry.get())
            return True
        except ValueError:
            tk.messagebox.showerror("Invalid input", "Please enter numeric values.")
            return False

    def apply(self):
        pass  # values are stored in self.magnitude and self.angle