import tkinter as tk
from tkinter import ttk
from components.status_bar import StatusBar
from components.menu_bar import MenuBar
from components.basic_tab import BasicTab
from components.advanced_tab import AdvancedTab
from components.saved_tab import SavedTab
from typing import Any, Callable
import pandas as pd

class DataAnalysisGUI:
    """Interface principal da aplicação."""

    def __init__(
        self, root: tk.Tk, connection: Any, engine: Any, db_type: str,
        current_profile: str, database_var: Any, dark_mode: bool,
        connection_status: str, config_manager: Any, log_message: Callable[[str], None], master: Any
    ):
        self.root = root
        self.connection = connection
        self.engine = engine
        self.db_type = db_type
        self.current_profile = current_profile
        self.database_var = database_var
        self.dark_mode = dark_mode
        self.connection_status = connection_status
        self.config_manager = config_manager
        self.log_message = log_message
        self.master = master

        self.log_message("Iniciando a interface gráfica de análise de dados.")
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface gráfica."""
        self.log_message("Configurando interface gráfica...")
        self.root.title("Análise de Dados")
        self.root.geometry("900x650")

        # Notebook (Abas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Criar abas
        self.log_message("Criando abas de navegação.")
        self.basic_tab = BasicTab(
            self.notebook, self.config_manager, self.log_message,
            self.db_type, self.engine, self.current_profile
        )
        self.advanced_tab = AdvancedTab(
            self.notebook, self.config_manager, self.log_message,
            self.db_type, self.engine, self.current_profile
        )
        self.saved_tab = SavedTab(
            self.notebook, self.config_manager, self.log_message,
            self.db_type, self.engine, self.current_profile
        )

        self.notebook.add(self.basic_tab.frame, text="Consulta Básica")
        self.notebook.add(self.advanced_tab.frame, text="SQL Avançado")
        self.notebook.add(self.saved_tab.frame, text="Tabelas Salvas")

        # Menu
        self.log_message("Criando menu de navegação.")
        self.menu_bar = MenuBar(self.root, self.config_manager, self.log_message,
            self.db_type, self.engine, self.current_profile)

        # Barra de status
        self.log_message("Configurando barra de status.")
        self.status_bar = StatusBar(self.root, self.log_message,self.engine,type_db=self.db_type)

        self.log_message("Interface gráfica configurada com sucesso.")
