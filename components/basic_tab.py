from sqlalchemy import text 
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable
from DataFrameTable import DataFrameTable
import pandas as pd

class BasicTab:
    """Cria a aba de consulta básica."""

    def __init__(
        self, notebook: ttk.Notebook, config_manager: Any, log_message: Callable,
        db_type: str, engine: Any, current_profile: str
    ):
        self.config_manager = config_manager
        self.log_message = log_message
        self.db_type = db_type
        self.engine = engine
        self.current_profile = current_profile
        self.root = notebook.master  # Get the root window from notebook
        
        self.frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame, text="Consulta Básica")  # Add frame to notebook with tab title
        self.table_widget = None  # Initialize table widget reference
        
        self.setup_ui()

    def setup_ui(self):
        """Configura a aba de consulta básica."""
        ttk.Label(self.frame, text="Nome da Tabela:").pack(pady=5)
        
        self.table_entry = ttk.Entry(self.frame)
        self.table_entry.pack(pady=5, fill=tk.X, expand=True)
        
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Carregar", command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar", command=self.clear_entry).pack(side=tk.LEFT, padx=5)
        
        # Result frame to hold the table
        self.result_frame = ttk.Frame(self.frame)
        self.result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

    def load_data(self):
        """Carrega dados do banco de dados."""
        table_name = self.table_entry.get().strip()
        if not table_name:
            self.log_message("Nenhum nome de tabela informado.")
            messagebox.showwarning("Aviso", "Por favor, informe o nome da tabela.")
            return
        
        try:
            self.log_message(f"Carregando dados da tabela {table_name} no banco {self.db_type} para o perfil {self.current_profile}...")
            
            query = text(f"SELECT * FROM {table_name}")
            df = pd.read_sql(query, self.engine)
            
            if df.empty:
                self.log_message("A tabela está vazia ou não foi encontrada.")
                messagebox.showinfo("Info", "A tabela não contém dados ou não foi encontrada.")
                return
            
            # Clear previous table if exists
            if self.table_widget:
                self.table_widget.destroy()
            
            self.log_message(f"Dados carregados com sucesso. {len(df)} linhas e {len(df.columns)} colunas.")
            
            # Create new table widget
            self.table_widget = DataFrameTable(
                master=self.result_frame,
                df=df,
                rows_per_page=10,
                column_width=100,
                on_data_change=self.on_data_changed,
                edit_enabled=True,
                delete_enabled=True
            )
            self.table_widget.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            self.log_message(f"Erro ao carregar dados: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")

    def clear_entry(self):
        """Limpa o campo de entrada da tabela."""
        self.table_entry.delete(0, tk.END)
        self.log_message("Campo de entrada limpo.")
        
    def on_data_changed(self, df):
        """Called when data in the table is modified."""
        self.log_message("Dados modificados na tabela.")