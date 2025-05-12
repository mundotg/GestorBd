from tkinter import ttk
import traceback
import pandas as pd
from typing import Callable, Any, Optional, Union
from sqlalchemy import text, inspect
from components.treeview_frame import TreeViewFrame
from components.navigation_frame import NavigationFrame
from components.edit_modal import EditModal
from config.DatabaseLoader import pesquisar_in_db

class DataFrameTable(ttk.Frame):
    """
    Um widget tkinter para exibir, editar e paginar DataFrames do pandas.
    """
    def __init__(self, master: Any,databse_name, engine: Optional[Any] = None, db_type: str = 'PostgreSQL',log_message: Any=None,
                 columns:Optional[dict[str, Any]] = None, enum_values: Optional[dict[str,Any]] = None,
                 df: Optional[pd.DataFrame] = None, rows_per_page: int = 10, column_width: int = 100,
                 edit_enabled: bool = True, delete_enabled: bool = True, query_executed: Optional[text] = None,
                 table_name: Optional[Union[str, list]] = None, on_data_change: Optional[Callable[[pd.DataFrame], None]] = None, **kwargs):
        super().__init__(master, **kwargs)

        try:
            self.engine = engine
            self.df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
            self.rows_per_page = rows_per_page
            self.column_width = column_width
            self.edit_enabled = edit_enabled
            self.delete_enabled = delete_enabled
            self.query_executed = query_executed
            self.table_name = table_name
            self.on_data_change = on_data_change
            self.db_type = db_type.lower()
            self.modal_edit = None
            self.log_message = log_message
            self.current_page = 0
            self.total_pages = self._calculate_total_pages()
            self.selected_row_index = None
            self.enum_values = enum_values.copy() if enum_values is not None else {}
            self.columns = columns.copy() if columns is not None else {}
            self.databse_name = databse_name
            self.log_message( f"Data carregada com {len(self.df)} linhas e {len(self.df.columns)} colunas.")

            self._create_styles()
            self.log_message( "Estilos configurados.")

            self.treeview_frame = TreeViewFrame(
                master=self, show_edit_modal=self.show_edit_modal, df=self.df,columns=self.columns,
                column_width=self.column_width, log_message=log_message,databse_name=self.databse_name,
            )

            self.navigation_frame = NavigationFrame(
                master=self, prev_page=self.prev_page, next_page=self.next_page, update_table=self.update_table,
                df=self.df, db_type=self.db_type, engine=self.engine, on_data_change=self.on_data_change,
                table_name=self.table_name, databse_name=self.databse_name, log_message=log_message, 
                columns=self.columns,enum_values=self.enum_values, query_executed=self.query_executed,edit_table=edit_enabled
            )

            self.log_message( "Componentes de interface criados.")

            self.update_table()
            self.log_message( "Tabela atualizada com sucesso.")

            self.treeview_frame.pack(expand=True, fill="both")
            self.navigation_frame.pack(fill="x")

        except Exception as e:
            self.log_message( f"Erro ao inicializar DataFrameTable: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")

    def _calculate_total_pages(self) -> int:
        try:
            total_pages = max(1, -(-len(self.df) // self.rows_per_page))  # Equivalente a math.ceil(len(df) / rows_per_page)
            self.log_message( f"Número total de páginas calculado: {total_pages}")
            return total_pages
        except Exception as e:
            self.log_message( f"Erro ao calcular total de páginas: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
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
            self.log_message( "Estilos criados com sucesso.")
        except Exception as e:
            self.log_message( f"Erro ao criar estilos: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")

    def update_table(self, df: Optional[pd.DataFrame] = None,  
                     columns: Optional[dict] = None,  enum_values: Optional[dict] = None,  on_data_change: Optional[callable] = None, 
                    table_name: Optional[str] = None, query_executed: str = "") -> None:
        """Atualiza a tabela e seus dados internos, apenas se novos valores forem fornecidos."""
        try:
            # Atualiza apenas se valores novos forem passados
            if query_executed:
                self.query_executed = query_executed
                
            if table_name:
                self.table_name = table_name
                self.navigation_frame.table_name = table_name
                # self.treeview_frame.query_executed = query_executed
                
            if on_data_change:
                self.on_data_change = on_data_change
            if enum_values is not None:
                self.enum_values = enum_values.copy()
            if columns is not None:
                self.columns = columns.copy()
                self.navigation_frame.columns = self.columns

            if df is not None:
                self.df = df.copy()
                self.total_pages = self._calculate_total_pages()
                self.current_page = min(self.current_page, max(self.total_pages - 1, 0))

                # Só atualiza a tabela se o DataFrame foi alterado
                self.treeview_frame.update_table(self.df, self.current_page, self.rows_per_page)
                self.navigation_frame.update_pagination(self.current_page, self.total_pages, len(self.df))

        except Exception as e:
            self.log_message(
                f"Erro ao atualizar tabela: {e} ({type(e).__name__})\n{traceback.format_exc()}",
                level="error"
            )


    def prev_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self) -> None:
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_table()

    def show_edit_modal(self, index=None, _fechar_modal=None) -> None:
        """Exibe um modal para editar a linha selecionada ou atualiza a existente."""
        try:
            if index is not None:
                self.selected_row_index = int(index)

            if self.selected_row_index is None or self.selected_row_index >= len(self.df):
                self.log_message("Nenhuma linha válida selecionada para edição.", level="warning")
                return

            campo_primary_key = None

            if self.engine and not isinstance(self.table_name, list):
                inspector = inspect(self.engine)
                pk_constraint = inspector.get_pk_constraint(self.table_name)
                primary_keys = pk_constraint.get("constrained_columns", [])
                campo_primary_key = primary_keys[0] if primary_keys else None

            if not campo_primary_key:
                unique_cols = [col for col in self.df.columns if self.df[col].is_unique]
                campo_primary_key = unique_cols[0] if unique_cols else self.df.columns[0]
            
            primary_key_value = None
            if campo_primary_key in self.df.columns:
                primary_key_value = self.df.at[self.selected_row_index, campo_primary_key]

            if primary_key_value is None:
                primary_key_value = pesquisar_in_db(self.engine, self.db_type, campo_primary_key, primary_key_value, 
                                                    self.table_name, self.selected_row_index, text, self.log_message)
                self.log_message(f"Chave primária `{campo_primary_key}` não encontrada na linha {self.selected_row_index}.", level="error")
                if primary_key_value is None:
                    return
            # Se não existe modal ou é para uma tabela diferente, cria um novo
            self.log_message(f"Abrindo modal de edição para linha {self.selected_row_index} (Campo: {campo_primary_key}, ID: {primary_key_value})")
            if self.modal_edit :
                self.modal_edit.destroy()
                self.modal_edit = None
                del self.modal_edit
                
                # Show loading indicator
            # loading_frame = ttk.Frame(self)
            # loading_frame.pack(expand=True, fill=tk.BOTH)
            
            # ttk.Label(
            #     loading_frame,
            #     text=f"Carregando dados da tabela {self.table_name}...",
            #     font=("Arial", 12)
            # ).pack(expand=True)
            
            # progress = ttk.Progressbar(loading_frame, mode="indeterminate")
            # progress.pack(fill=tk.X, padx=50, pady=20)
            # progress.start()
               
                # Atualiza o modal existente
            self.modal_edit = EditModal(
                master=self, 
                engine=self.engine, 
                df=self.df, 
                row_index=self.selected_row_index,
                is_opened_callback=_fechar_modal,
                name_campo_primary_key=campo_primary_key, 
                primary_key_value=primary_key_value,
                db_type=self.db_type,
                table_name=self.table_name, 
                on_data_change=self.on_data_change, 
                edit_enabled=self.edit_enabled,
                column_types=self.columns, 
                enum_values=self.enum_values, 
                log_message=self.log_message,
                databse_name=self.databse_name,
            )

        except Exception as e:
            self.log_message(f"Erro ao abrir modal de edição: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            
    def update_table_for_search(self, df: Optional[pd.DataFrame] = None) -> None:
        try:
            if df is not None and not df.empty:
                # 🔹 Se já houver dados, concatena em vez de sobrescrever
                if hasattr(self, "df") and isinstance(self.df, pd.DataFrame):
                    self.df = pd.concat([self.df, df], ignore_index=True)
                    # del df
                else:
                    self.df = df.copy()
                    # del df

                # 🔹 Recalcula a paginação
                self.total_pages = self._calculate_total_pages()
                self.current_page = min(self.current_page, self.total_pages - 1)

            # 🔹 Atualiza a exibição da tabela
            n_linha = len(self.df) if hasattr(self, "df") and isinstance(self.df, pd.DataFrame) else 0
            self.navigation_frame.update_pagination(self.current_page, self.total_pages, n_linha)
            
            # self.log_message( "Tabela e paginação atualizadas com sucesso.")
        
        except Exception as e:
            self.log_message( f"Erro ao atualizar tabela: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")


