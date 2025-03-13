import tkinter as tk
from tkinter import ttk
class Theme:
    """Classe para gerenciar os temas da aplicação"""
    
    LIGHT = {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "button": "#e0e0e0",
        "highlight": "#0078d7",
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#ffc107"
    }
    
    DARK = {
        "bg": "#2d2d2d",
        "fg": "#ffffff",
        "button": "#3d3d3d",
        "highlight": "#0078d7",
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#ffc107"
    }
    
    @staticmethod
    def apply_theme(root, theme_dict):
        """Aplica o tema aos widgets"""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configurar estilo para widgets ttk
        style.configure("TFrame", background=theme_dict["bg"])
        style.configure("TLabel", background=theme_dict["bg"], foreground=theme_dict["fg"])
        style.configure("TButton", background=theme_dict["button"], foreground=theme_dict["fg"])
        style.configure("TOptionMenu", background=theme_dict["bg"], foreground=theme_dict["fg"])
        style.configure("TEntry", fieldbackground=theme_dict["bg"], foreground=theme_dict["fg"])
        style.configure("TCombobox", fieldbackground=theme_dict["bg"], foreground=theme_dict["fg"])
        
        # Configurar cores para a janela principal
        root.configure(bg=theme_dict["bg"])
        
        return style
