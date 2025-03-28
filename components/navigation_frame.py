import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Optional
import pandas as pd

from components.Create_registro_Modal import CreateModal
from components.analit_frame_table import AnalysisFrame 

class NavigationFrame(ttk.Frame):
    """Creates a navigation frame with pagination controls."""
    
    def __init__(self, master: Any, prev_page: Callable, next_page: Callable, update_table: Callable, df: pd.DataFrame,engine: Any, table_name: str='',db_type:str ='PostgreSQL', on_data_change: Optional[Callable[[pd.DataFrame], None]] = None):
        super().__init__(master)
        self.prev_page = prev_page
        self.next_page = next_page
        self.update_table = update_table
        self.df = df  # Armazena o DataFrame
        self.on_data_change = on_data_change
        self.engine = engine
        self.table_name = table_name
        self.db_type = db_type

        self._create_widgets()
    
    def _create_widgets(self):
        """Creates navigation buttons with validation."""
        self.prev_button = ttk.Button(self, text='Previous', command=self._validate_prev_page, style="DataTable.TButton")
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        self.page_label = ttk.Label(self, text="Page 1 of 1", font=("Arial", 10))
        self.page_label.pack(side=tk.LEFT, padx=5)
        
        self.next_button = ttk.Button(self, text='Next', command=self._validate_next_page, style="DataTable.TButton")
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(self, text='Refresh', command=self.update_table, style="DataTable.TButton")
        self.refresh_button.pack(side=tk.RIGHT, padx=5)

        

        # Botão para ver registros mal formados
        self.invalid_button = ttk.Button(self, text="criar novo registro", command=self.cria_regitro, style="DataTable.TButton")
        self.invalid_button.pack(side=tk.RIGHT, padx=5)
        self.analysis_button = ttk.Button(self, text="Analisar Tabela", command=self.open_analysis)
        self.analysis_button.pack(pady=5)
    def cria_regitro(self):
        self.on_data_change(self.df)
        CreateModal(master=self, engine=self.engine, table_name=self.table_name, on_data_change=self.on_data_change, db_type=self.db_type, df=self.df)
        return
    def open_analysis(self):
        analysis_window = tk.Toplevel()
        analysis_window.title("Análise Detalhada")
        analysis_frame = AnalysisFrame(analysis_window, self.df)
        analysis_frame.pack(fill=tk.BOTH, expand=True)

    def update_pagination(self, current_page: int, total_pages: int):
        """Updates the page label and button states."""
        self.page_label.config(text=f'Page {current_page + 1} of {total_pages}')
        self.prev_button.config(state=tk.NORMAL if current_page > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if current_page < total_pages - 1 else tk.DISABLED)
    
    def _validate_prev_page(self):
        """Validates and navigates to the previous page."""
        if callable(self.prev_page):
            self.prev_page()
        else:
            messagebox.showerror("Error", "Invalid previous page function.")
    
    def _validate_next_page(self):
        """Validates and navigates to the next page."""
        if callable(self.next_page):
            self.next_page()
        else:
            messagebox.showerror("Error", "Invalid next page function.")
  
