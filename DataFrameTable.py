from tkinter import ttk
import pandas as pd
from typing import Callable, Any, Optional

from sqlalchemy import text
from components.treeview_frame import TreeViewFrame
from components.navigation_frame import NavigationFrame
from components.edit_modal import EditModal
from logger import log_message

class DataFrameTable(ttk.Frame):
    """
    A tkinter widget for displaying, editing, and paginating pandas DataFrames.
    """
    
    def __init__(
        self, 
        master: Any, 
        df: Optional[pd.DataFrame] = None,
        rows_per_page: int = 10,
        column_width: int = 100,
        on_data_change: Optional[Callable[[pd.DataFrame], None]] = None,
        edit_enabled: bool = True,
        delete_enabled: bool = True,
        query_executed: Optional[text] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        try:
            # Configuration
            self.df = df.copy() if df is not None else pd.DataFrame()
            self.rows_per_page = rows_per_page
            self.column_width = column_width
            self.on_data_change = on_data_change
            self.edit_enabled = edit_enabled
            self.delete_enabled = delete_enabled
            self.query_executed = query_executed
            
            # State variables
            self.current_page = 0
            self.total_pages = self._calculate_total_pages()
            self.selected_row_index = None
            
            log_message(self, f"Data carregada com {len(self.df)} linhas e {len(self.df.columns)} colunas.")
            
            # Setup the widget
            self._create_styles()
            log_message(self, "Estilos configurados.")

            self.treeview_frame = TreeViewFrame(self, self.df, self.column_width)
            self.navigation_frame = NavigationFrame(self, self.prev_page, self.next_page, self.update_table)
            log_message(self, "Componentes de interface criados.")

            self.update_table()
            log_message(self, "Tabela atualizada com sucesso.")
            
            self.treeview_frame.pack(expand=True, fill="both")
            self.navigation_frame.pack(fill="x")
        
        except Exception as e:
            log_message(self, f"Erro ao inicializar DataFrameTable: {e}", level="error")

    def _calculate_total_pages(self) -> int:
        try:
            total_pages = max(1, -(-len(self.df) // self.rows_per_page))  # Arredondamento para cima
            log_message(self, f"Número total de páginas calculado: {total_pages}")
            return total_pages
        except Exception as e:
            log_message(self, f"Erro ao calcular total de páginas: {e}", level="error")
            return 1

    def _create_styles(self) -> None:
        """Create custom styles for the widget."""
        try:
            self.style = ttk.Style()
            self.style.configure(
                "DataTable.Treeview", 
                background="#f0f0f0",
                foreground="black",
                rowheight=25,
                fieldbackground="#f0f0f0"
            )
            self.style.map(
                "DataTable.Treeview", 
                background=[("selected", "#347083")],
                foreground=[("selected", "white")]
            )
            log_message(self, "Estilos criados com sucesso.")
        except Exception as e:
            log_message(self, f"Erro ao criar estilos: {e}", level="error")
   
    def update_table(self, df: Optional[pd.DataFrame] = None) -> None:
        """Update the table with data from the current page."""
        try:
            if df is not None:
                self.df = df.copy()
                self.total_pages = self._calculate_total_pages()
                self.current_page = min(self.current_page, self.total_pages - 1)

            log_message(self, f"Atualizando tabela para a página {self.current_page}...")
            self.treeview_frame.update_table(self.df, self.current_page, self.rows_per_page)
            self.navigation_frame.update_pagination(self.current_page, self.total_pages)
            log_message(self, "Tabela e paginação atualizadas com sucesso.")
        except Exception as e:
            log_message(self, f"Erro ao atualizar tabela: {e}", level="error")

    def prev_page(self) -> None:
        """Go to the previous page if possible."""
        try:
            if self.current_page > 0:
                self.current_page -= 1
                log_message(self, f"Indo para a página anterior: {self.current_page}")
                self.update_table()
            else:
                log_message(self, "Página anterior não disponível.", level="warning")
        except Exception as e:
            log_message(self, f"Erro ao navegar para a página anterior: {e}", level="error")

    def next_page(self) -> None:
        """Go to the next page if possible."""
        try:
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                log_message(self, f"Indo para a próxima página: {self.current_page}")
                self.update_table()
            else:
                log_message(self, "Próxima página não disponível.")
        except Exception as e:
            log_message(self, f"Erro ao navegar para a próxima página: {e}", level="error")

    def show_edit_modal(self) -> None:
        """Display a modal dialog for editing the selected row."""
        try:
            if self.selected_row_index is not None and self.selected_row_index < len(self.df):
                log_message(self, f"Abrindo modal de edição para linha {self.selected_row_index}")
                EditModal(self, self.df, self.selected_row_index, self.on_data_change)
            else:
                log_message(self, "Nenhuma linha selecionada para edição.")
        except Exception as e:
            log_message(self, f"Erro ao abrir modal de edição: {e}", level="error")
