import tkinter as tk
from tkinter import simpledialog, messagebox
from geometry.components.types import ThermalBC, ThermalBCType

class ThermalBCDialog(simpledialog.Dialog):

    def __init__(self, parent, existing: ThermalBC | None = None):
        self.result   = None
        self.existing = existing
        super().__init__(parent, title="Define Thermal BC")

    def body(self, master):
        bold = ("Arial", 10, "bold")

        self._type_var = tk.StringVar(value=(
            self.existing.type.value if self.existing else ThermalBCType.HEAT_FLUX.value
        ))

        tk.Label(master, text="Boundary Condition Type:", font=bold).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0,4))

        tk.Label(master, text="Value:", font=bold).grid(
            row=2, column=0, sticky="w", pady=(8,0))

        self._value_entry = tk.Entry(master, width=12)
        self._value_entry.grid(row=2, column=1, sticky="w", pady=(8,0))
        if self.existing and self.existing.value:
            self._value_entry.insert(0, str(self.existing.value))

        self._unit_label = tk.Label(master, text="deg C", fg="#666666")
        self._unit_label.grid(row=2, column=2, sticky="w", padx=4, pady=(8,0))

        return self._value_entry

    def apply(self):
        pass

    def buttonbox(self):
        box = tk.Frame(self)
        tk.Button(box, text="OK",     width=8, command=self.ok).pack(side="left",  padx=4, pady=4)
        tk.Button(box, text="Clear",  width=8, command=self._clear).pack(side="left", padx=4, pady=4)
        tk.Button(box, text="Cancel", width=8, command=self.cancel).pack(side="left", padx=4, pady=4)
        box.pack()

    def _clear(self):
        self.result = "clear"
        self.destroy()