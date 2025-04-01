import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from components.CheckboxWithEntry import CheckboxWithEntry
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Callable, Optional, Dict, Union, List, TypedDict
import traceback
from components.Data_wiget2 import DateTimeEntry
from utils.logger import log_message as escrever
from components.DataWidget import DatabaseDateWidget
from utils.validarText import  get_valor_idependente_entry, validar_numero_float,validar_numero_inteiro,_fetch_enum_values,convert_values
import numpy as np


class ColumnInfo(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Any


class EditModal(tk.Toplevel):
    """Creates a modal to edit a record from a DataFrame and save to the database."""

    def __init__(
        self, master: Any, engine, df: pd.DataFrame, table_name: str, row_index: int,
        primary_key_value: str, name_campo_primary_key: str, edit_enabled: bool,
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
        self.primary_key = primary_key_value
        self.name_campo_primary_key = name_campo_primary_key
        self.on_data_change = on_data_change
        self.edit_enabled = edit_enabled
        self.column_types = column_types or {}
        self.db_type = db_type
        self.record_id = self.df.at[self.row_index, self.name_campo_primary_key]
        self.field_entries: Dict[str, Union[ttk.Entry, ttk.Combobox, tk.BooleanVar, DatabaseDateWidget]] = {}
        self.enum_values = enum_values or {}
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Disabled.TEntry", foreground="#FFFFFF", fieldbackground="#0000FF")
        
        self._setup_window()
        self._create_widgets()

    def log_message(self, message: str, level: str = "info"):
        """Log a message with the specified level."""
        escrever(self=self, message=message, level=level)

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
                
        ttk.Button(button_frame, text=" ❌Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Make sure canvas adjusts to window size
        self.fields_frame.bind("<Configure>", lambda e: self._adjust_canvas_scrollregion(canvas))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("win", width=e.width-4))
        
        # Mouse wheel scrolling
        self.bind_all("<MouseWheel>", lambda e: self._scroll_canvas(e, canvas))
        
        # Create the fields
        self._create_fields()
        self._adjust_canvas_scrollregion(canvas)
        self.fields_frame.update_idletasks()
    def _adjust_canvas_scrollregion(self, canvas):
        """Adjust the canvas scroll region to encompass all content."""
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _create_fields(self):
        """Create edit fields based on database schema."""
        try:
            print("Criando campos...")  # Debug
            # Get column information
            columns = self._get_column_info()
            
            # Create a header row
            ttk.Label(self.fields_frame, text="Campo", font=("Arial", 10, "bold"), 
                     style="TLabel").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            ttk.Label(self.fields_frame, text="Valor", font=("Arial", 10, "bold"), 
                     style="TLabel").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            
            ttk.Separator(self.fields_frame, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
            
            # Create input fields for each column
            for i, col in enumerate(columns, start=2):
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
                value = self.df.at[self.row_index, col_name]
                
                self._create_typed_widget(col_name, col_type, value, i, nullable)
            
            # Configure the fields frame columns
            self.fields_frame.columnconfigure(0, weight=0, minsize=150)
            self.fields_frame.columnconfigure(1, weight=1, minsize=300)
            
        except Exception as e:
            self.log_message(f"Erro ao criar campos: {traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao criar campos de edição: {str(e)}")

    def _get_column_info(self) -> List[ColumnInfo]:
        """Get column information from the database."""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(self.table_name)
            
            # Get enum values if not provided
            if not self.enum_values:
                _fetch_enum_values(self=self,columns=columns,text=text,traceback=traceback)
                
            return columns
        except Exception as e:
            self.log_message(f"Erro ao obter informações das colunas: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            raise RuntimeError(f"Falha ao obter esquema da tabela: {str(e)}")


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
            widget = None
            no_data = True
            # Normalize type for case-insensitive comparison
            col_type = col_type.lower()

            # Primary key field should be disabled
            is_primary_key = False  # col_name == self.name_campo_primary_key
            state = "disabled" if is_primary_key else "normal"

            # Criar o widget apropriado com base no tipo de dado
            if "enum" in col_type:
                values = self.enum_values.get(col_name, ["Valor não disponível"])
                widget = ttk.Combobox(self.fields_frame, values=values, state="readonly" if not is_primary_key else "disabled")
                widget.set(str_value)

            elif "int" in col_type or "integer" in col_type :
                vcmd = self.register(validar_numero_inteiro)
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"), state=state)
                widget.insert(0, str_value)

            elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
                vcmd = self.register(lambda s: validar_numero_float(s, allow_float=True))
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"), state=state)
                widget.insert(0, str_value)

            elif "bool" in col_type or col_type in ["bit", "boolean"]:
                var = tk.BooleanVar(value=bool(value))
                no_data = False
                # var = tk.BooleanVar(value=False)
                entry = CheckboxWithEntry(self.scrollable_frame,entry_value=value)
                entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
                entry = entry.entry

            elif "date" in col_type or "timestamp" in col_type or "time" in col_type or "datatime" in col_type:
                try:
                    entry = DateTimeEntry(self.fields_frame,col_type)
                    entry.set_date(date=str_value,time=str_value)
                    entry.grid(row=row, column=1, sticky=tk.EW, padx=1, pady=3)
                    widget = entry.entry
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
        inspector = inspect(self.engine)
        columns = inspector.get_columns(self.table_name)
        
        errors = []
        for col in columns:
            col_name, nullable = col["name"], col.get("nullable", True)
            if not nullable and col_name in self.field_entries:
                widget = self.field_entries[col_name]
                value = self._get_widget_value(col_name, widget)
                
                if value is None or str(value).strip() == "":
                    errors.append(f"O campo '{col_name}' é obrigatório.")
        
        return errors

    def build_update_query(self,table_name, updated_values, primary_key):
        """Constrói a query de atualização dinâmica."""
        updated_values= convert_values(updated_values=updated_values,np=np) 
        set_clauses = [f"{col} = :{col}" for col in updated_values.keys() if col != primary_key]
        if not set_clauses:  # 🚀 Correção: Verificação antes da criação da query
            return None
        if not set_clauses:
            return None
        return text(f"UPDATE {table_name} SET " + ", ".join(set_clauses) + f" WHERE {primary_key} = :{primary_key}")
    

    def _save_changes(self):
        """Função genérica para salvar alterações em qualquer banco de dados."""
        try:
            self.save_button.config(state="disabled")
            errors = self._validate_fields()
            if errors:
                messagebox.showerror("Validação", "\n".join(errors))
                return
            
            updated_values ={} 
            for col_name, entry in self.field_entries.items():
                updated_values[col_name] = get_valor_idependente_entry(entry, tk, ttk)  
            updated_values[self.primary_key] = self.record_id  
                
            query = self.build_update_query(self.table_name, updated_values, self.primary_key)
            if query is None:
                messagebox.showinfo("Sem alterações", "Nenhuma alteração foi detectada.")
                self.log_message("Nenhuma alteração foi detectada.", level="info")
                return
            
            confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja salvar as alterações?")
            if not confirm:
                return
            
            with self.engine.begin() as conn:
                conn.execute(query, updated_values)
            
            self.log_message(f"Registro {self.record_id} atualizado com sucesso!", level="info")
            df = self.df.copy()
            for col, value in updated_values.items():
                if col in df.columns:
                    df.at[self.row_index, col] = value
            
            if self.on_data_change:
                self.on_data_change(df)
            
            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
        except SQLAlchemyError as e:
            self.log_message(f"Erro SQL ao atualizar o registro:{e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao salvar as alterações: {str(e)}")
        except Exception as es:
            self.log_message(f"Erro ao atualizar o registro:{es} ({type(es).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao salvar as alterações: {str(es)}")
        self.save_button.config(state="normal")
            
    def _delete_record(self):
        """Função para deletar um registro do banco de dados."""
        resposta =""
        try:
            confirm = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este registro?")
            if not confirm:
                return
            self.delete_button.config(state="disabled")
            query = text(f"DELETE FROM {self.table_name} WHERE {self.name_campo_primary_key} = :primary_key")
            params = {"primary_key": self.primary_key}
            
            with self.engine.begin() as conn:
                conn.execute(query, params)
            
            self.log_message(f"Registro {self.primary_key} deletado com sucesso!", level="info")
            resposta =messagebox.showinfo("Sucesso", "Registro deletado com sucesso!")
            df = self.df.copy()
            df = df[df[self.name_campo_primary_key] != self.primary_key]
        
            if self.on_data_change:
                self.on_data_change(df)
            
        except SQLAlchemyError as es:
            self.log_message(f"Erro SQL ao deletar o registro: {es} ({type(es).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao deletar o registro: {str(es)}")
        except Exception as e:
            self.log_message(f"Erro ao deletar o registro: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao deletar o registro: {str(e)}")
        self.delete_button.config(state="normal")
        if resposta.lower() == "ok":
            print("fechar")
            self.destroy()

