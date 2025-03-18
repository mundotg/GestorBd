import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Any, Callable

class EditModal(tk.Toplevel):
    """Creates a modal dialog for editing a row in a pandas DataFrame."""
    
    def __init__(self, master: Any, df: pd.DataFrame, row_index: int, on_data_change: Callable[[pd.DataFrame], None]):
        super().__init__(master)
        self.df = df
        self.row_index = row_index
        self.on_data_change = on_data_change
        
        self.title("Edit Record")
        self.geometry("400x300")
        self.transient(master)
        self.grab_set()
        
        self.field_entries = {}
        self._create_widgets()
    
    def _create_widgets(self):
        """Creates entry fields for editing row data."""
        row_data = self.df.iloc[self.row_index]
        
        for col_name, value in row_data.items():
            frame = ttk.Frame(self)
            frame.pack(fill=tk.X, pady=5)
            
            label = ttk.Label(frame, text=f"{col_name}:", width=15, anchor=tk.W)
            label.pack(side=tk.LEFT)
            
            entry = ttk.Entry(frame, width=30)
            entry.insert(0, str(value))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            self.field_entries[col_name] = entry
        
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(button_frame, text="Save", command=self._save_changes)
        save_button.pack(side=tk.LEFT, padx=5)
        
        close_button = ttk.Button(button_frame, text="Close", command=self.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)
    
    def _save_changes(self):
        """Saves the changes back to the DataFrame."""
        for col, entry in self.field_entries.items():
            self.df.at[self.row_index, col] = entry.get()
        
        if self.on_data_change:
            self.on_data_change(self.df)
        
        messagebox.showinfo("Success", "Record updated successfully!")
        self.destroy()