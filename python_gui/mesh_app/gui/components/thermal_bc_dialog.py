import tkinter as tk
from tkinter import simpledialog, messagebox


class FixedTemperatureDialog(simpledialog.Dialog):
    """Simple dialog to set a fixed temperature (°C) on a boundary edge."""

    def __init__(self, parent, existing: float | None = None):
        self.result = None
        self.existing = existing
        super().__init__(parent, title="Fixed Temperature")

    def body(self, master):
        tk.Label(master, text="Temperature (°C):", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4),
        )
        self._entry = tk.Entry(master, width=12)
        self._entry.grid(row=0, column=1, sticky="w")
        if self.existing is not None:
            self._entry.insert(0, str(self.existing))
        return self._entry

    def validate(self):
        try:
            self.result = float(self._entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a numeric temperature.")
            return False
        return True

    def apply(self):
        pass

    def buttonbox(self):
        box = tk.Frame(self)
        tk.Button(box, text="OK", width=8, command=self.ok).pack(side="left", padx=4, pady=4)
        tk.Button(box, text="Clear", width=8, command=self._clear).pack(side="left", padx=4, pady=4)
        tk.Button(box, text="Cancel", width=8, command=self.cancel).pack(side="left", padx=4, pady=4)
        box.pack()

    def _clear(self):
        self.result = "clear"
        self.destroy()
