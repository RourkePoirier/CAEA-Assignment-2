import pandas as pd
from data_handling.types import *

def write_to_excel(data, header, filename):
        df_full = pd.DataFrame({
            header: data,
        })

        df_full.to_excel(filename, index=False)
    
def write_data_structure_to_excel(output: ExcelOutputFormat, filename):
    
    max_len = max(
        len(output.F),
        len(output.X),
        len(output.Y),
        len(output.dzero),
    )

    def pad(lst):
        if not isinstance(lst, list):
            lst = [lst]
        return lst + [None] * (max_len - len(lst))

    # Build full dataframe including ncon
    df_full = pd.DataFrame({
        "n_element": pad(output.n_element),
        "n_nodes":   pad(output.n_nodes),
        "ncon1":     pad(output.ncon1),
        "ncon2":     pad(output.ncon2),
        "ncon3":     pad(output.ncon3),
        "X":         pad(output.X),
        "Y":         pad(output.Y),
        "E":         pad(output.E),
        "A":         pad(output.A),
        "F":         pad(output.F),
        "NDU":       pad(output.NDU),
        "dzero":     pad(output.dzero),
        "v":         pad(output.v),
        "t":         pad(output.t),
    })    
    print(df_full.to_string())
    df_full.to_excel(filename, index=False)