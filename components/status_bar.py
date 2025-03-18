import tkinter as tk
from tkinter import ttk
from typing import Any
from sqlalchemy.exc import OperationalError

class StatusBar:
    """Cria uma barra de status robusta e responsiva na parte inferior da janela."""

    def __init__(self, root: tk.Tk, log_message: Any, engine: Any,type_db: str):
        self.type_db = type_db
        self.log_message = log_message
        self.engine = engine
        
        # Verifica a conexão inicial
        self.connection_status_text = self.check_connection()

        # Frame principal da barra de status
        self.status_frame = ttk.Frame(root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        # Sub-frame para organização responsiva
        self.inner_frame = ttk.Frame(self.status_frame)
        self.inner_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status de conexão
        self.status_label = ttk.Label(self.inner_frame, text=f"Banco: {self.type_db}", anchor="w")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
        # Status dinâmico
        self.connection_status_label = ttk.Label(
            self.inner_frame, 
            text=f"Status: {self.connection_status_text}",
            foreground="green" if self.connection_status_text == "Conectado" else "red",
            anchor="e"
        )
        self.connection_status_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.log_message("Barra de status inicializada com sucesso.")

    def check_connection(self) -> str:
        """Verifica se o banco de dados está conectado."""
        if not self.engine:
            return "Desconectado"
        try:
            with self.engine.connect() as conn:
                return "Conectado"
        except OperationalError:
            return "Desconectado"

    def update_status(self, message: str):
        """Atualiza a mensagem de status e o estado da conexão."""
        connection_status = self.check_connection()
        
        self.status_label.config(text=message)
        self.connection_status_label.config(
            text=f"Status: {connection_status}",
            foreground="green" if connection_status == "Conectado" else "red"
        )
        self.log_message(f"Status atualizado: {message} - {connection_status}")

    def refresh_status(self):
        """Atualiza dinamicamente o status de conexão."""
        self.update_status(self.status_label.cget("text"))
