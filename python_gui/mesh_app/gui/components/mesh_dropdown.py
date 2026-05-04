from tkinter import ttk
import tkinter as tk

from geometry.components.types import MeshScheme

class MeshSelectDropdown(tk.Frame):

    def __init__(self, parent, on_change=None, width=700, height=50):
        super().__init__(parent)

        # Title
        title = tk.Label(self, text="Mesh Generation Scheme:", font=("Arial", 10, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")

        # Combobox
        self._var = tk.StringVar()
        self.combo = ttk.Combobox(self, width=25, state="readonly", values=[s.value for s in MeshScheme], textvariable=self._var)
        self.combo.current(0)
        self.combo.grid(row=1, column=1, columnspan=3, pady=10, sticky="ew")

        # Change state
        if on_change: self.combo.bind("<<ComboboxSelected>>", lambda e: on_change(self.get_scheme()))

    def get_scheme(self) -> MeshScheme:
        return MeshScheme(self._var.get()) # Return currently selected mesh scheme