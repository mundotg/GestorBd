import tkinter as tk
from tkinter import ttk
from typing import Any

class MenuBar:
    """Cria o menu principal da aplicação."""

    def __init__(
        self, root: tk.Tk, config_manager: Any, log_message: Any,
        db_type: str, engine: Any, current_profile: str
    ):
        self.config_manager = config_manager
        self.log_message = log_message
        self.db_type = db_type
        self.engine = engine
        self.current_profile = current_profile
        
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        # Menu Arquivo
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Abrir", command=self.open_file)
        self.file_menu.add_command(label="Salvar", command=self.save_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Sair", command=root.quit)

        # Menu Configurações
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Preferências", command=self.open_settings)

        # Menu Ajuda
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Sobre", command=self.show_about)

        # Adiciona menus à barra
        self.menu_bar.add_cascade(label="Arquivo", menu=self.file_menu)
        self.menu_bar.add_cascade(label="Configurações", menu=self.settings_menu)
        self.menu_bar.add_cascade(label="Ajuda", menu=self.help_menu)

    def open_file(self):
        """Ação para abrir um arquivo."""
        self.log_message("Abrir arquivo selecionado")
        print("Abrindo arquivo...")

    def save_file(self):
        """Ação para salvar um arquivo."""
        self.log_message("Salvar arquivo selecionado")
        print("Salvando arquivo...")

    def open_settings(self):
        """Abre o menu de configurações."""
        self.log_message("Abrindo configurações")
        print("Abrindo configurações...")

    def show_about(self):
        """Exibe informações sobre o programa."""
        self.log_message("Exibindo informações sobre o programa")
        print("Este é um sistema de análise de dados.")
