import tkinter as tk
from tkinter import ttk
from typing import Any

class SavedTab:
    """Cria a aba de tabelas salvas."""

    def __init__(
        self, notebook: ttk.Notebook, config_manager: Any, log_message: Any,
        db_type: str, engine: Any, current_profile: str
    ):
        self.config_manager = config_manager
        self.log_message = log_message
        self.db_type = db_type.strip().lower()
        self.engine = engine
        self.current_profile = current_profile
        
        self.frame = ttk.Frame(notebook, padding=10)
        self.setup_ui()

    def setup_ui(self):
        """Configura a aba de tabelas salvas."""
        ttk.Label(self.frame, text="Tabelas Salvas").pack(pady=5)

        self.listbox = tk.Listbox(self.frame)
        self.listbox.pack(pady=5, fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Carregar", command=self.load_saved_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remover", command=self.remove_saved_table).pack(side=tk.LEFT, padx=5)

    def load_saved_table(self):
        """Carrega uma tabela salva."""
        selected = self.listbox.curselection()
        if selected:
            table_name = self.listbox.get(selected[0])
            self.log_message(f"Carregando tabela: {table_name}")
            print(f"Carregando tabela: {table_name}")
        else:
            self.log_message("Nenhuma tabela selecionada")
            print("Nenhuma tabela selecionada")
    
    def remove_saved_table(self):
        """Remove uma tabela salva da lista."""
        selected = self.listbox.curselection()
        if selected:
            table_name = self.listbox.get(selected[0])
            self.listbox.delete(selected[0])
            self.log_message(f"Tabela removida: {table_name}")
            print(f"Tabela removida: {table_name}")
        else:
            self.log_message("Nenhuma tabela selecionada para remoção")
            print("Nenhuma tabela selecionada para remoção")

