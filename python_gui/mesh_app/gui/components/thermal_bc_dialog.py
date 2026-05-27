import tkinter as tk
from tkinter import simpledialog, messagebox


class ThermalBCDialog(simpledialog.Dialog):
    """Dialog to set an edge thermal BC: convecting (default), fixed temperature, or insulated."""

    def __init__(self, parent, existing: float | None = None):
        self.result = None  # ("convecting", None) | ("insulated", None) | ("fixed", float)
        self.existing = existing
        super().__init__(parent, title="Thermal Boundary Condition")

    def body(self, master):
        tk.Label(master, text="Type:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))

        self._mode = tk.StringVar(value="fixed" if self.existing is not None else "convecting")
        tk.Radiobutton(master, text="Convecting (default)", variable=self._mode, value="convecting", command=self._sync).grid(
            row=1, column=0, columnspan=2, sticky="w"
        )
        tk.Radiobutton(master, text="Insulated", variable=self._mode, value="insulated", command=self._sync).grid(
            row=2, column=0, columnspan=2, sticky="w"
        )
        tk.Radiobutton(master, text="Fixed Temperature", variable=self._mode, value="fixed", command=self._sync).grid(
            row=3, column=0, columnspan=2, sticky="w"
        )

        tk.Label(master, text="Temperature (°C):").grid(row=4, column=0, sticky="w", pady=(6, 0))
        self._entry = tk.Entry(master, width=12)
        self._entry.grid(row=4, column=1, sticky="w", pady=(6, 0))
        if self.existing is not None:
            self._entry.insert(0, str(self.existing))

        self._sync()
        return self._entry

    def validate(self):
        mode = self._mode.get()
        if mode == "convecting":
            self.result = ("convecting", None)
            return True
        if mode == "insulated":
            self.result = ("insulated", None)
            return True

        try:
            temp = float(self._entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter a numeric temperature.")
            return False
        self.result = ("fixed", temp)
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
        self.result = ("convecting", None)
        self.destroy()

    def _sync(self):
        mode = self._mode.get()
        state = "normal" if mode == "fixed" else "disabled"
        self._entry.configure(state=state)
