from tkinter import ttk
import traceback
import pandas as pd
from typing import Callable, Any, Optional

from sqlalchemy import text
from components.treeview_frame import TreeViewFrame
from components.navigation_frame import NavigationFrame
from components.edit_modal import EditModal
from utils.logger import log_message
from sqlalchemy import inspect

class DataFrameTable(ttk.Frame):
    """
    Um widget tkinter para exibir, editar e paginar DataFrames do pandas.
    """
    
    def __init__(
        self, 
        master: Any,
        engine: Optional[Any] = None,
        db_type:str='PostgreSQL' ,
        df: Optional[pd.DataFrame] = None,
        rows_per_page: int = 10,
        column_width: int = 100,
        edit_enabled: bool = True,
        delete_enabled: bool = True,
        query_executed: Optional[text] = None,
        table_name: Optional[str]= None,
        on_data_change: Optional[Callable[[pd.DataFrame], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        try:
            self.engine = engine
            self.df = df.copy() if df is not None else pd.DataFrame()
            self.rows_per_page = rows_per_page
            self.column_width = column_width
            self.edit_enabled = edit_enabled
            self.delete_enabled = delete_enabled
            self.query_executed = query_executed
            self.table_name = table_name
            self.on_data_change = on_data_change
            self.db_type = db_type
            self.modal_edit = None
            
            self.current_page = 0
            self.total_pages = self._calculate_total_pages()
            self.selected_row_index = None
            
            log_message(self, f"Data carregada com {len(self.df)} linhas e {len(self.df.columns)} colunas.")
            
            self._create_styles()
            log_message(self, "Estilos configurados.")

            self.treeview_frame = TreeViewFrame(
                master=self, show_edit_modal=self.show_edit_modal, df=self.df, column_width=self.column_width,log_message=log_message
            )
            self.navigation_frame = NavigationFrame(master=self, prev_page=self.prev_page, next_page=self.next_page, update_table=self.update_table, df=self.df,
                                                    db_type=self.db_type,engine=self.engine,on_data_change=self.on_data_change,table_name=self.table_name)
            log_message(self, "Componentes de interface criados.")

            self.update_table()
            log_message(self, "Tabela atualizada com sucesso.")
            
            self.treeview_frame.pack(expand=True, fill="both")
            self.navigation_frame.pack(fill="x")
        
        except Exception as e:
            log_message(self, f"Erro ao inicializar DataFrameTable: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")

    def _calculate_total_pages(self) -> int:
        try:
            total_pages = max(1, -(-len(self.df) // self.rows_per_page))
            log_message(self, f"Número total de páginas calculado: {total_pages}")
            return total_pages
        except Exception as e:
            log_message(self, f"Erro ao calcular total de páginas: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            return 1

    def _create_styles(self) -> None:
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
            log_message(self, f"Erro ao criar estilos: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
   
    def update_table(self, df: Optional[pd.DataFrame] = None) -> None:
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
            log_message(self, f"Erro ao atualizar tabela: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")

    def prev_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            log_message(self, f"Indo para a página anterior: {self.current_page}")
            self.update_table()

    def next_page(self) -> None:
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            log_message(self, f"Indo para a próxima página: {self.current_page}")
            self.update_table()

    def show_edit_modal(self, index=None):
        """Exibe um modal para editar a linha selecionada."""
        try:
            # Se um índice foi passado, atualiza a linha selecionada
            if index is not None:
                self.selected_row_index = int(index)
                print(f'Índice selecionado: {index}')

            # Fecha o modal de edição se já existir
            if self.modal_edit:
                self.modal_edit.destroy()

            # Valida se o índice é válido
            if self.selected_row_index is None or self.selected_row_index >= len(self.df):
                log_message(self, "Nenhuma linha válida selecionada para edição.", level="warning")
                return

            # Obtém a chave primária da tabela no banco de dados
            inspector = inspect(self.engine)
            pk_constraint = inspector.get_pk_constraint(self.table_name)
            primary_keys = pk_constraint.get("constrained_columns", [])

            # Determina a chave primária a ser usada
            if primary_keys:
                campo_primary_key = primary_keys[0]  # Usa a primeira chave primária encontrada
            else:
                # Caso não tenha chave primária explícita, busca uma coluna com valores únicos
                unique_cols = [col for col in self.df.columns if self.df[col].is_unique]
                campo_primary_key = unique_cols[0] if unique_cols else self.df.columns[0]  # Usa a primeira coluna disponível

            # Obtém o valor da chave primária
            primary_key_value = self.df.at[self.selected_row_index, campo_primary_key]

            if primary_key_value is None:
                log_message(self, f"Chave primária `{campo_primary_key}` não encontrada na linha {self.selected_row_index}.", level="error")
                return

            log_message(self, f"Abrindo modal de edição para linha {self.selected_row_index} (Campo: {campo_primary_key}, ID: {primary_key_value})")

            # Instancia e exibe o modal de edição
            self.modal_edit = EditModal(
                master=self,
                engine=self.engine,
                df=self.df,
                row_index=self.selected_row_index,
                name_campo_primary_key=campo_primary_key,
                primary_key_value=primary_key_value,
                table_name=self.table_name,
                on_data_change=self.on_data_change,
                edit_enabled=self.edit_enabled
            )

        except Exception as e:
            error_msg = f"Erro ao abrir modal de edição: {e} ({type(e).__name__})\n{traceback.format_exc()}"
            log_message(self, error_msg, level="error")

            
