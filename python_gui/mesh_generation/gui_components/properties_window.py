import tkinter as tk

class PropertiesWindow(tk.Frame):
    def __init__(self, parent, entries=None, width=700, height=50):
        
        super().__init__(parent)

        self.material_properties = {}
        self.vars = {}

        if entries is None:
            entries = [
                ("Young's Modulus", "Pa"),
                ("Thickness", "m"),
                ("Poisson's Ratio", "")
            ]

        self.entry_widgets = {}

        #########################################
        # Title
        #########################################

        title = tk.Label(self, text="System Properties:", font=("Arial", 10, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")

        #########################################
        # Create key-value-unit rows
        #########################################

        for i, (key, unit) in enumerate(entries, start=1):

            label = tk.Label(self, text=f"{key}:")
            var = tk.StringVar()
            entry = tk.Entry(self, textvariable=var, width=10)
            unit_label = tk.Label(self, text=f"({unit})" if unit else "")

            label.grid(row=i, column=0, sticky="w")
            entry.grid(row=i, column=1)
            unit_label.grid(row=i, column=2, sticky="w")

            self.entry_widgets[key] = entry
            self.vars[key] = var

            var.trace_add("write", lambda *args, k=key: self._update_property(k))
    

    #########################################
    # Autosave update
    #########################################
    def _update_property(self, key):
        val_str = self.vars[key].get()
        try:
            value = float(val_str)
            self.material_properties[key] = value
        except ValueError:
            pass

    def get_material_properties(self):
        return self.material_properties


if __name__ == "__main__":
    root = tk.Tk()
    pw = PropertiesWindow(root)
    pw.pack(padx=20, pady=20)
    root.mainloop()
