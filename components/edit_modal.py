import re
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from components.CheckboxWithEntry import CheckboxWithEntry
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Callable, Optional, Dict, Union, List, TypedDict
import traceback
from components.Data_wiget2 import DateTimeEntry
from components.DataWidget import DatabaseDateWidget
from utils.validarText import  _convert_column_type_for_string_one, _map_column_type, get_valor_idependente_entry, quote_identifier, validar_numero, _fetch_enum_values,convert_values
import numpy as np


class ColumnInfo(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Any


class EditModal(tk.Toplevel):
    """Creates a modal to edit a record from a DataFrame and save to the database."""

    def __init__(
        self, master: Any,databse_name, engine,log_message, df: pd.DataFrame, table_name: str, row_index: int,
        primary_key_value: str, name_campo_primary_key: str, edit_enabled: bool,is_opened_callback: Optional[Callable] = None,
        db_type: str = "postgresql", on_data_change: Optional[Callable[[pd.DataFrame], None]] = None,
        column_types: Optional[Dict[str, str]] = None, enum_values: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize the EditModal.
        
        Args:
            master: The parent widget
            engine: SQLAlchemy engine
            df: DataFrame containing the data
            table_name: Name of the database table
            row_index: Index of the row being edited
            primary_key_value: Value of the primary key
            name_campo_primary_key: Column name of the primary key
            edit_enabled: Whether editing is allowed
            db_type: Database type (postgresql, mysql, etc.)
            on_data_change: Callback function when data changes
            column_types: Dictionary of column types
            enum_values: Dictionary of enum values for dropdown fields
        """
        super().__init__(master)
        self.df = df
        self.engine = engine
        self.table_name = table_name
        self.row_index = row_index
        self.name_campo_primary_key = name_campo_primary_key
        self.on_data_change = on_data_change
        self.edit_enabled = edit_enabled
        self.column_info = column_types or {}
        self.db_type = db_type.strip().lower()
        self.databse_name = databse_name
        self.is_opened_callback = is_opened_callback
        self.record_id = primary_key_value if primary_key_value else self.df.at[self.row_index, self.name_campo_primary_key]
        self.field_entries: Dict[str, Union[ttk.Entry, ttk.Combobox, tk.BooleanVar, DatabaseDateWidget]] = {}
        self.enum_values = enum_values or {}
        self.column_types = {}
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Disabled.TEntry", foreground="#FFFFFF", fieldbackground="#0000FF")
        self.log_message=log_message
        self._setup_window()
        self._create_widgets()

    def _setup_window(self):
        """Configure the modal window."""
        self.title(f'Editar Registro - {self.table_name}')
        self.geometry("600x600")
        self.minsize(500, 400)
        self.transient(self.master)
        self.grab_set()
        self.resizable(True, True)
        
        # Center the window on the screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
# 4009
    def _create_widgets(self):
        """Create input fields and buttons."""
        
        main_frame = ttk.Frame(self, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with table name and record ID
        header_frame = ttk.Frame(main_frame, style="TFrame")
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 5), padx=10)
        
        ttk.Label(header_frame, 
                 text=f"Tabela: {self.table_name} | ID: {self.record_id}",
                 font=("Arial", 12, "bold"), 
                 style="TLabel").pack(anchor=tk.W)
        
        ttk.Separator(main_frame, orient="horizontal").pack(fill=tk.X, padx=10)

        # Buttons at the bottom
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        # Scrollable content frame
        content_frame = ttk.Frame(main_frame, style="TFrame")
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(content_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        self.fields_frame = ttk.Frame(canvas, style="TFrame")
        
        # canvas.create_window((0, 0), window=self.fields_frame, anchor=tk.NW, width=canvas.winfo_width())
        canvas.create_window((0, 0), window=self.fields_frame, anchor=tk.NW, tags="win",width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Button configuration
        self.save_button = ttk.Button(
            button_frame, 
            text="✏Salvar", 
            command=self._save_changes,
            state="normal" if self.edit_enabled else "disabled"
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.delete_button = ttk.Button(
            button_frame, 
            text="🗑 Apagar", 
            command=self._delete_record,
            state="normal" if self.edit_enabled else "disabled"
        )
        self.delete_button.pack(side=tk.LEFT, padx=5)
                
        ttk.Button(button_frame, text=" ❌Cancelar", command=self._on_close).pack(side=tk.RIGHT, padx=5)
        
        # Make sure canvas adjusts to window size
        self.fields_frame.bind("<Configure>", lambda e: self._adjust_canvas_scrollregion(canvas))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("win", width=e.width-4))
        
        # Mouse wheel scrolling
        self.bind_all("<MouseWheel>", lambda e: self._scroll_canvas(e, canvas))
        
        # Create the fields
        self._create_fields()
        self._adjust_canvas_scrollregion(canvas)
        self.fields_frame.update_idletasks()
    def _on_close(self):
        """Handle window close event."""
        if self.is_opened_callback:
            self.is_opened_callback()
        self.destroy()
    def _adjust_canvas_scrollregion(self, canvas):
        """Adjust the canvas scroll region to encompass all content."""
        canvas.configure(scrollregion=canvas.bbox("all"))
        
    def verificar_num_column(self):
    # Verifica se o número de campos da linha selecionada e a lista de colunas são diferentes
        if len(self.linha_select_df) != len(self.column_info):
            self.log_message(
                "O número de campos da linha selecionada e da lista de colunas não coincidem.",
                level="error"
            )

            try:
                query = None
                params = None

                # Proteção para nomes de tabela e chave primária
                table = self.table_name.strip().replace("`", "").replace('"', '')
                pk = self.name_campo_primary_key.strip().replace("`", "").replace('"', '')

                # Define a consulta de acordo com o tipo de banco de dados
                if self.db_type in ['mysql', 'sqlite']:
                    query = f"SELECT * FROM `{table}` WHERE `{pk}` = %s"
                    params = (self.record_id,)

                elif self.db_type in ['postgresql', 'oracle']:
                    from sqlalchemy import text
                    query = text(f'SELECT * FROM "{table}" WHERE "{pk}" = :record_id')
                    params = {"record_id": self.record_id}

                elif self.db_type in ['mssql', 'sql server']:
                    query = f"SELECT * FROM [{table}] WHERE [{pk}] = ?"
                    params = (self.record_id,)

                else:
                    self.log_message(f"Banco de dados não suportado: {self.db_type}", level="error")
                    return

                # Executa a consulta
                df = pd.read_sql(query, self.engine, params=params)

                # Verifica se houve retorno da consulta
                if not df.empty:
                    self.linha_select_df = df.iloc[0]
                else:
                    self.log_message(
                        f"Nenhuma linha encontrada para {pk} = {self.record_id}.",
                        level="error"
                    )
                    self.linha_select_df = None

            except Exception as e:
                self.log_message(f"Erro ao consultar o banco de dados: {e}", level="error")
                self.linha_select_df = None




    def _create_fields(self):
        """Create edit fields based on database schema."""
        try:
            # Create a header row
            ttk.Label(self.fields_frame, text="Campo", font=("Arial", 10, "bold"), 
                     style="TLabel").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            ttk.Label(self.fields_frame, text="Valor", font=("Arial", 10, "bold"), 
                     style="TLabel").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            
            ttk.Separator(self.fields_frame, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
            self.linha_select_df = (self.df.iloc[self.row_index]).copy()
            if self.edit_enabled:
                self.verificar_num_column()
            # Create input fields for each column
            for i, col in enumerate(self.column_info, start=2):
                col_name, col_type = col["name"], str(col["type"]).lower()
                nullable = col.get("nullable", True)
                
                # Create label with required indicator
                label_text = f"{col_name}"
                if not nullable:
                    label_text += " *"
                    
                ttk.Label(self.fields_frame, text=label_text, style="TLabel").grid(
                    row=i, column=0, sticky=tk.W, padx=5, pady=3
                )
                
                # Create the appropriate widget based on column type
                if col_name in self.linha_select_df:
                    value = self.linha_select_df[col_name]
                self._create_typed_widget(col_name, col_type, value, i, nullable)
            # print(self.linha_select_df.to_dict())
            self.linha_select_df =self.linha_select_df.to_dict()
            # Configure the fields frame columns
            self.fields_frame.columnconfigure(0, weight=0, minsize=150)
            self.fields_frame.columnconfigure(1, weight=1, minsize=300)
            
        except Exception as e:
            self.log_message(f"Erro ao criar campos: {traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao criar campos de edição: {str(e)}")


    def _scroll_canvas(self, event, canvas):
        """Scroll the canvas with the mouse wheel."""
        try:
            if canvas.winfo_exists():
                # Handle different platforms
                if event.num == 5 or event.delta < 0:  # Scroll down
                    canvas.yview_scroll(1, "units")
                elif event.num == 4 or event.delta > 0:  # Scroll up
                    canvas.yview_scroll(-1, "units")
        except Exception:
            self.log_message(f"Erro ao rolar o canvas: {traceback.format_exc()}", level="error")

    def _create_typed_widget(self, col_name, col_type, value, row, nullable):
        """Create a widget appropriate for the column type with visibility for disabled fields."""
        try:
            str_value = str(value) if value is not None else ""
            self.linha_select_df[col_name]= str_value
            widget = None
            no_data = True
            # Normalize type for case-insensitive comparison
            col_type = col_type.lower()

            # Primary key field should be disabled
            is_primary_key = False  # col_name == self.name_campo_primary_key
            state = "disabled" if is_primary_key else "normal"
            if not  self.column_types.get(col_name):
                self.column_types[col_name] = _map_column_type(col_type)

            # Criar o widget apropriado com base no tipo de dado
            if "enum" in col_type:
                values = self.enum_values.get(col_name, ["Valor não disponível"])
                widget = ttk.Combobox(self.fields_frame, values=values, state="readonly" if not is_primary_key else "disabled")
                widget.set(str_value)

            elif "int" in col_type or "integer" in col_type :
                vcmd = self.register(validar_numero)
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"), state=state)
                widget.insert(0, str_value)

            elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
                vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"), state=state)
                widget.insert(0, str_value)

            elif "bool" in col_type or col_type in ["bit", "boolean"]:
                no_data = False
                # var = tk.BooleanVar(value=False)
                entry = CheckboxWithEntry(self.fields_frame,entry_value=str_value,entry_width=7)
                entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
                widget = entry.entry
                self.linha_select_df[col_name] = widget.get().strip()

            elif "date" in col_type or "timestamp" in col_type or "time" in col_type or "datatime" in col_type:
                try:
                    entry = DateTimeEntry(self.fields_frame,col_type)
                    if str_value != "":
                        entry.set_date(date=str_value,time=str_value)
                    entry.grid(row=row, column=1, sticky=tk.EW, padx=1, pady=3)
                    widget = entry.entry
                    self.linha_select_df[col_name] =entry.entry.get().strip()
                    no_data = False
                except Exception as e:
                    self.log_message(f"Erro criando widget de data: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
                    widget = ttk.Entry(self.fields_frame, state=state)
                    widget.insert(0, str_value)

            else:
                # Default to a simple entry for unrecognized types
                widget = ttk.Entry(self.fields_frame, state=state)
                widget.insert(0, str_value)

            # Aplicar cor personalizada para campos desabilitados
            if is_primary_key:
                widget.configure(style="Disabled.TEntry")

            # Adicionar widget ao grid e armazenar referência
            if no_data:
                widget.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
            self.field_entries[col_name] = widget

        except Exception as e:
            self.log_message(f"Erro ao criar widget para {col_name}: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            # Criar entrada padrão em caso de falha
            fallback = ttk.Entry(self.fields_frame)
            fallback.insert(0, str(value) if value is not None else "")
            fallback.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
            self.field_entries[col_name] = fallback

    def _validate_fields(self):
        """Validate that all required fields have values."""
        errors = []
        for col in self.column_info:
            col_name, nullable = col["name"], col.get("nullable", True)
            
            # Skip system fields that aren't in our entries
            if col_name not in self.field_entries:
                continue
                
            if not nullable:
                widget = self.field_entries[col_name]
                if widget is None:
                    continue
                value = get_valor_idependente_entry(widget,tk,ttk)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    errors.append(f"O campo '{col_name}' é obrigatório.")
        return errors
    
    def build_update_query(self,table_name, updated_values, primary_key):
        """Constrói a query de atualização dinâmica."""
        # set_clauses = [f"{col} = {value}" for col,value in updated_values.items() if col != primary_key]
        set_clauses = [f"{quote_identifier(self.db_type,col)} = {value}" for col,value in updated_values.items() ]
        if not set_clauses:
            return None  # Nenhuma coluna para atualizar

        # Obtendo o valor da chave primária formatado corretamente
        primary_value = _convert_column_type_for_string_one(self.column_types,primary_key,self.record_id) #updated_values[primary_key]

        # Construindo a query final
        query = text(f"UPDATE {quote_identifier(self.db_type,self.table_name)} SET {', '.join(set_clauses)} WHERE {quote_identifier(self.db_type,primary_key)} = {primary_value};")

        return query
    
    def normalizar(self,texto):
        """Remove espaços extras e normaliza strings."""
        return "" if texto is None else re.sub(r'\s+', ' ', str(texto).strip())
    
    def _save_changes(self):
        """Função genérica para salvar alterações em qualquer banco de dados."""
        try:
            self.save_button.config(state="disabled")
            errors = self._validate_fields()
            if errors:
                messagebox.showerror("Validação", "\n".join(errors))
                return
            
            updated_values = {}
            for col_name, entry in self.field_entries.items():
                valor = self.linha_select_df[col_name]
                valor_in_table = _convert_column_type_for_string_one(self.column_types, col_name, valor).strip()
                new_valor = _convert_column_type_for_string_one(self.column_types, col_name, get_valor_idependente_entry(entry, tk, ttk))
                old, last = self.normalizar(valor_in_table), self.normalizar(new_valor)
                
                if old != last:
                    updated_values[col_name] = new_valor

            if not updated_values:
                messagebox.showinfo("Sem alterações", "Nenhuma alteração foi detectada.")
                self.log_message("Nenhuma alteração foi detectada.", level="info")
                return
            
            updated_values[self.name_campo_primary_key] = _convert_column_type_for_string_one(self.column_types,self.name_campo_primary_key,self.record_id)
            query = self.build_update_query(self.table_name, updated_values, self.name_campo_primary_key)
            
            if query is None:
                return

            confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja salvar as alterações?")
            if not confirm:
                return

            with self.engine.begin() as conn:
                conn.execute(query)

            self.log_message(f"Registro {self.record_id} atualizado com sucesso!", level="info")
            
            
            for col, value in updated_values.items():
                if value is not None or value != "NULL":
                    if col in self.df.columns:
                        self.df.at[self.row_index, col] =self.column_types[col](value.strip("'"))
                 

            if self.on_data_change:
                self.on_data_change(self.df)

            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")

        except SQLAlchemyError as e:
            self.log_message(f"Erro SQL ao atualizar o registro: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            error_message = str(e)
        
            if "ForeignKeyViolation" in error_message:
                msg = "Falha ao salvar devido à violação de chave estrangeira. Verifique se todos os dados estão corretos e se as referências entre tabelas estão consistentes."
            elif "UniqueViolation" in error_message:
                msg = "Falha ao salvar devido a uma violação de unicidade. O valor informado já existe no banco de dados."
            else:
                msg = f"Ocorreu um erro ao tentar salvar as alterações no banco de dados. Erro: {error_message}"
            messagebox.showerror("Erro de Banco de Dados", msg)
        except Exception as es:
            self.log_message(f"Erro ao atualizar o registro: {es} ({type(es).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao salvar as alterações: {str(es)}")
        finally:
            self.save_button.config(state="normal")

    def _delete_record(self):
        """Função para deletar um registro do banco de dados."""
        try:
            confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este registro?")
            if not confirm:
                return

            self.delete_button.config(state="disabled")
            query = text(f"DELETE FROM {quote_identifier(self.db_type,self.table_name)} WHERE {quote_identifier(self.db_type,self.name_campo_primary_key)} = :primary_key")
            params = {"primary_key": _convert_column_type_for_string_one(self.column_types,self.name_campo_primary_key,self.record_id)}

            with self.engine.begin() as conn:
                conn.execute(query, params)

            self.log_message(f"Registro {self.record_id} deletado com sucesso! query ={query}", level="info")
            messagebox.showinfo("Sucesso", "Registro deletado com sucesso!")
            
            self.df = self.df[self.df[self.name_campo_primary_key] != self.record_id]

            if self.on_data_change:
                self.on_data_change(self.df)

        except SQLAlchemyError as e:
            self.log_message(f"Erro SQL ao deletar o registro: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao deletar o registro: {str(e)}")
        except Exception as e:
            self.log_message(f"Erro ao deletar o registro: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao deletar o registro: {str(e)}")
        finally:
            self.delete_button.config(state="normal")