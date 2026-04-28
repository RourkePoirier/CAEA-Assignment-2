from tkinter import ttk
import tkinter as tk

from data_types import MeshScheme

class MeshGenWindow(tk.Frame):
    def __init__(self, parent, mesh_method: tk.StringVar, on_change=None, entries=None, width=700, height=50):
        
        super().__init__(parent)        
        self.mesh_method = mesh_method

        #########################################
        # Title
        #########################################
        title = tk.Label(self, text="Mesh Generation Scheme:", font=("Arial", 10, "bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")

        #########################################
        # Mesh Generation Combo Box
        #########################################

        self.combo = ttk.Combobox(self, 
                                  width=25, 
                                  state="readonly", 
                                  values=[s.value for s in MeshScheme], 
                                  textvariable=self.mesh_method
                                  )
        self.combo.current(0)

        self.combo.grid(row=1, column=1, columnspan=3, pady=10, sticky="ew")
        


        #self.label = tk.Label(self, text=self.mesh_method.get(), font=("Arial", 10))
        #self.label.grid(row=0, column=4, columnspan=1, pady=(0, 10), sticky="w")

        if on_change:
            def on_select(e):
                on_change()
            self.combo.bind("<<ComboboxSelected>>", on_select)

    def get_mesh_scheme(self):
        return self.combo.get()
    
    
        


if __name__ == "__main__":
    root = tk.Tk()
    pw = MeshGenWindow(root)
    pw.pack(padx=20, pady=20)
    root.mainloop()
