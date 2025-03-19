import tkinter as tk
from tkinter import ttk
import pandas as pd
from typing import Any, Optional

class TreeViewFrame(ttk.Frame):
    """Creates a Treeview widget to display a pandas DataFrame."""
    
    def __init__(self, master: Any, df: Optional[pd.DataFrame] = None, column_width: int = 100):
        super().__init__(master)
        self.df = df.copy() if df is not None else pd.DataFrame()
        self.column_width = column_width

        self._create_widgets()
        self._setup_columns()
        self._populate_table()

    def _create_widgets(self):
        """Creates the Treeview and associated scrollbars."""
        self.tree_scroll_y = ttk.Scrollbar(self, orient="vertical")
        self.tree_scroll_x = ttk.Scrollbar(self, orient="horizontal")

        self.tree = ttk.Treeview(
            self,
            columns=[],
            show='headings',
            yscrollcommand=self.tree_scroll_y.set,
            xscrollcommand=self.tree_scroll_x.set,
            style="DataTable.Treeview"
        )

        # Scrollbars
        self.tree_scroll_y.config(command=self.tree.yview)
        self.tree_scroll_x.config(command=self.tree.xview)

        self.tree.pack(expand=True, fill='both')
        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x.pack(side="bottom", fill="x")

    def _setup_columns(self):
        """Configura as colunas do Treeview."""
        self.tree["columns"] = list(self.df.columns) if not self.df.empty else []

        for col in self.df.columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, width=self.column_width, anchor=tk.CENTER)

    def _populate_table(self):
        """Popula a tabela com os dados atuais."""
        for _, row in self.df.iterrows():
            self.tree.insert("", "end", values=row.tolist())

    def update_table(self, df: pd.DataFrame, current_page: int, rows_per_page: int):
        """Atualiza a tabela com novos dados mantendo a paginação."""
        self.df = df.copy()

        # Limpa os dados antigos
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Atualiza as colunas se necessário
        if list(self.tree["columns"]) != list(self.df.columns):
            self._setup_columns()

        # Calcula o intervalo correto para exibir
        start_idx = current_page * rows_per_page
        end_idx = start_idx + rows_per_page
        paged_df = self.df.iloc[start_idx:end_idx]

        # Adiciona os novos dados
        for _, row in paged_df.iterrows():
            self.tree.insert("", "end", values=row.tolist())

        
        start = current_page * rows_per_page
        end = min(start + rows_per_page, len(df))
        
        for _, row in df.iloc[start:end].iterrows():
            self.tree.insert('', tk.END, values=row.tolist())