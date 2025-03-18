import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Any

class TreeViewFrame(ttk.Frame):
    """Creates a Treeview widget to display a pandas DataFrame."""
    
    def __init__(self, master: Any, df: pd.DataFrame, column_width: int = 100):
        super().__init__(master)
        self.df = df
        self.column_width = column_width
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Creates the Treeview and associated scrollbars."""
        self.tree_scroll_y = ttk.Scrollbar(self, orient="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")

        self.tree_scroll_x = ttk.Scrollbar(self, orient="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            self,
            columns=list(self.df.columns),
            show='headings',
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set,
            style="DataTable.Treeview"
        )
        
        for col in self.df.columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, width=self.column_width, anchor=tk.CENTER)
        
        self.tree.pack(expand=True, fill='both')
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)
    
    def update_table(self, df: pd.DataFrame, current_page: int, rows_per_page: int):
        """Updates the table with new data."""
        self.df = df
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        start = current_page * rows_per_page
        end = min(start + rows_per_page, len(df))
        
        for _, row in df.iloc[start:end].iterrows():
            self.tree.insert('', tk.END, values=row.tolist())