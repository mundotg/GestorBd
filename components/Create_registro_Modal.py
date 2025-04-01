import gc
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Callable, Optional, Dict, Union, List, TypedDict
import traceback

from components.CheckboxWithEntry import CheckboxWithEntry
from components.Data_wiget2 import DateTimeEntry
from components.DataWidget import DatabaseDateWidget
from utils.logger import log_message as escrever
from utils.validarText import _convert_column_type, _fetch_enum_values, _get_placeholder, _map_column_type, get_valor_idependente_entry, validar_numero, convert_values,_is_system_field

class ColumnInfo(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Any

class CreateModal(tk.Toplevel):
    """Creates a modal to add a new record to a database table."""
    def __init__(
        self, master: Any, engine, table_name: str, df: Any,column_name_key:str,
        db_type: str = "postgresql", on_data_change: Optional[Callable[[pd.DataFrame], None]] = None,
        column_types: Optional[Dict[str, str]] = None, enum_values: Optional[Dict[str, List[str]]] = None
    ):
        super().__init__(master)
        self.engine = engine
        self.table_name = table_name
        self.on_data_change = on_data_change
        self.column_types = column_types or {}
        self.db_type = db_type.lower()
        self.field_entries: Dict[str, Union[ttk.Entry, ttk.Combobox, tk.BooleanVar, DatabaseDateWidget, tk.Text]] = {}
        self.enum_values = enum_values or {}
        self.column_info = []
        self.df = df
        self.column_name_key=column_name_key
        
        self._setup_window()
        self._create_widgets()

    def log_message(self, message: str, level: str = "info"):
        """Log a message with the specified level."""
        escrever(self=self, message=message, level=level)

    def _setup_window(self):
        """Configure the modal window."""
        self.title(f'Novo Registro - {self.table_name}')
        self.geometry("600x600")
        self.minsize(500, 400)
        self.transient(self.master)
        self.grab_set()
        self.resizable(True, True)
        self._center_window()

    def _center_window(self):
        """Centers the window on the screen."""
        self.update_idletasks()
        width, height = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def _create_widgets(self):
        """Create input fields and buttons."""
        self._configure_styles()
        main_frame = ttk.Frame(self, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_header(main_frame)
        self._create_content(main_frame)
        self._create_buttons(main_frame)
        self._create_fields()
    
    def _configure_styles(self):
        """Configures the styles for the widgets."""
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
    
    def _create_header(self, parent):
        """Creates the header section."""
        header_frame = ttk.Frame(parent, style="TFrame")
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 5), padx=10)
        
        ttk.Label(header_frame, text=f"Novo Registro na Tabela: {self.table_name}",
                  font=("Arial", 12, "bold"), style="TLabel").pack(anchor=tk.W)
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, padx=10)
    
    def _create_content(self, parent):
        """Creates the scrollable content section."""
        content_frame = ttk.Frame(parent, style="TFrame")
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(content_frame, bg="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.fields_frame = ttk.Frame(self.canvas, style="TFrame")
        
        self.canvas.create_window((0, 0), window=self.fields_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fields_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.bind_all("<MouseWheel>", self._scroll_canvas)
    
    def _create_buttons(self, parent):
        """Creates the action buttons."""
        button_frame = ttk.Frame(parent, style="TFrame")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        
        self.button_salvar = ttk.Button(button_frame, text="💾 Salvar", command=self._save_record)
        self.button_salvar.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑 Limpar", command=self._clear_fields).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def _create_fields(self):
        """Create input fields based on database schema."""
        try:
            # Get column information
            self.column_info = self._get_column_info()
            
            # Create a header row
            ttk.Label(self.fields_frame, text="Campo", font=("Arial", 10, "bold"), 
                     style="TLabel").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            ttk.Label(self.fields_frame, text="Valor", font=("Arial", 10, "bold"), 
                     style="TLabel").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            
            ttk.Separator(self.fields_frame, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
            
            # Create input fields for each column
            for i, col in enumerate(self.column_info, start=2):
                col_name, col_type = col["name"], str(col["type"]).lower()
                nullable = col.get("nullable", True)
                default_value = col.get("default", None)
                
                # Skip auto-increment columns and other system fields
                if _is_system_field(col_name, col_type, self.column_info,self.db_type,self.table_name,self.engine):
                    continue
                
                # Create label with required indicator
                label_text = f"{col_name}" + (" *" if not nullable else "")
                
                ttk.Label(self.fields_frame, text=label_text, style="TLabel").grid(
                    row=i, column=0, sticky=tk.W, padx=5, pady=3
                )
                
                # Create the appropriate widget based on column type
                self._create_typed_widget(col_name, col_type, default_value, i, nullable)
            
            # Configure the fields frame columns
            self.fields_frame.columnconfigure(0, weight=0, minsize=150)
            self.fields_frame.columnconfigure(1, weight=1, minsize=300)
            
        except Exception as e:
            self.log_message(f"Erro ao criar campos: {traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao criar campos de edição: {str(e)}")
            raise  # Relevanta a exceção para depuração


    def _get_column_info(self) -> List[Dict]:
        """Get column information from the database."""
        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(self.table_name)
            
            # Fetch enum values if not provided
            if not self.enum_values:
                _fetch_enum_values(self,columns,text,traceback)
                
            return columns
        except Exception as e:
            self.log_message(f"Erro ao obter informações das colunas: {traceback.format_exc()}", level="error")
            raise RuntimeError(f"Falha ao obter esquema da tabela: {str(e)}")

    def _scroll_canvas(self, event):
        """Scroll the canvas with the mouse wheel."""
        canvas = self.canvas
        try:
            # Handle different platforms
            if event.num == 5 or event.delta < 0:  # Scroll down
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:  # Scroll up
                canvas.yview_scroll(-1, "units")
        except Exception:
            self.log_message(f"Erro ao rolar o canvas: {traceback.format_exc()}", level="error")

    def _create_typed_widget(self, col_name, col_type, default_value, row, nullable):
        """Create a widget appropriate for the column type."""
        try:
            # Convert default value to string if it exists
            str_value = str(default_value) if default_value is not None else ""
            widget = None
            no_data = True
            # Normalize type for case-insensitive comparison
            col_type = col_type.lower()
            # Create the appropriate widget based on type
            if "enum" in col_type or (self.enum_values.get(col_name) not in [None, "", []]):
                if not self.column_types.get(col_name):
                    self.column_types[col_name] = _map_column_type(col_type)
                values = self.enum_values.get(col_name, ["Valor não disponível"])
                widget = ttk.Combobox(self.fields_frame, values=values, state="readonly")
                if values:
                    widget.set(values[0])  # Set the first value as default
            
            elif "int" in col_type or "integer" in col_type:
                if not self.column_types.get(col_name):
                    self.column_types[col_name] = _map_column_type(col_type)
                vcmd = self.register(validar_numero)
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"))
                if default_value is not None:
                    widget.insert(0, str_value)
            
            elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
                if not self.column_types.get(col_name):
                    self.column_types[col_name] = _map_column_type(col_type)
                vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"))
                if default_value is not None:
                    widget.insert(0, str_value)
            
            elif "bool" in col_type or col_type in "bit" or col_type in "boolean":
                if not self.column_types.get(col_name):
                    self.column_types[col_name] = _map_column_type(col_type)
                no_data = False
                # var = tk.BooleanVar(value=False)
                entry = CheckboxWithEntry(self.fields_frame)
                entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
                entry = entry.entry
            
            elif "date" in col_type or "datetime" in col_type or "timestamp" in col_type  or "time" in col_type:
                try:
                    if not  self.column_types.get(col_name):
                        self.column_types[col_name] = _map_column_type(col_type)
                    entry = DateTimeEntry(self.fields_frame,col_type)
                    entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
                    # entry.set_date(date=str_value,time=str_value)
                    widget = entry.entry
                    no_data = False
                except Exception:
                    self.log_message(f"Erro criando widget de data: {traceback.format_exc()}", level="error")
                    widget = ttk.Entry(self.fields_frame)
                    if default_value is not None:
                        widget.insert(0, str_value)
           
            else:
                # Default to a simple entry for unrecognized types
                if not  self.column_types.get(col_name):
                        self.column_types[col_name] = _map_column_type(col_type)
                widget = ttk.Entry(self.fields_frame)
                if default_value is not None:
                    widget.insert(0, str_value)
            
            # Add the widget to the grid and store it in field_entries
            if no_data:
                widget.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=3)
            self.field_entries[col_name] = widget
            
        except Exception as e:
            self.log_message(f"Erro ao criar widget para {col_name}: {traceback.format_exc()}", level="error")
            # Create a simple entry as fallback
            fallback = ttk.Entry(self.fields_frame)
            if default_value is not None:
                fallback.insert(0, str(default_value))
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

    def _clear_fields(self):
        """Clear all input fields."""
        for col_name, widget in self.field_entries.items():
            if isinstance(widget, tk.BooleanVar):
                widget.set(False)
            elif isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
            elif isinstance(widget, DatabaseDateWidget):
                widget.clear()
            elif isinstance(widget, ttk.Combobox):
                if widget['values']:
                    widget.set(widget['values'][0])
                else:
                    widget.set("")
            else:
                widget.delete(0, tk.END)
   

    def build_create_query(self, table_name, updated_values):
        """Constrói dinamicamente uma query de inserção, compatível com diferentes bancos."""
        if not updated_values:
            return None
        
        # Converte os tipos dos valores
        updated_values = _convert_column_type(self.column_types, updated_values)
        columns = ", ".join(updated_values.keys())
        values = ", ".join(f"'{value}'" if isinstance(value, str) else "NULL" if value is None else str(value) for value in updated_values.values())
        # Verifica se o banco suporta RETURNING
        if self.db_type in ["postgresql", "mariadb", "oracle"]:
            query = text(f"INSERT INTO {table_name} ({columns}) VALUES ({values}) RETURNING {self.column_name_key}")
        elif self.db_type == "mysql":
            query = text(f"INSERT INTO {table_name} ({columns}) VALUES ({values})")
        elif self.db_type == "sqlite":
            query = text(f"INSERT INTO {table_name} ({columns}) VALUES ({values})")
        elif self.db_type in ["mssql", "sqlserver", "sql server", "sqlserver"]:  # SQL Server usa OUTPUT INSERTED
            query = text(f"INSERT INTO {table_name} ({columns}) OUTPUT INSERTED.{self.column_name_key} VALUES ({values})")
        else:
            raise ValueError(f"Banco de dados {self.db_type} não suportado!")
        return query


    def _save_record(self):
        """Função genérica para salvar alterações em qualquer banco de dados."""
        OK= ""
        try:
            self.button_salvar.config(state="disabled")
          
            errors = self._validate_fields()
            if errors:
                messagebox.showerror("Validação", "\n".join(errors))
                self.button_salvar.config(state="normal")
                return
            
            updated_values ={} 
            for col_name, entry in self.field_entries.items():
                updated_values[col_name] = get_valor_idependente_entry(entry,tk,ttk)   
           
            query = self.build_create_query(self.table_name, updated_values)
            if query is None:
                messagebox.showinfo("Sem alterações", "Nenhuma alteração foi detectada.")
                self.log_message("Nenhuma alteração foi detectada.", level="info")
                return
            print("query: ",query)
            record_id= ""
            with self.engine.begin() as conn:
                result =conn.execute(query)
                # print(f"result: {result}")
                try:
                    record_id = result.fetchone()[0] if result.returns_rows and result.rowcount > 0 else None
                except Exception:
                    record_id = None  # Garante que não haverá erro ao acessar scalar()
            
            self.log_message(f"Registro {record_id} atualizado com sucesso!", level="info")
            df = self.df.copy()
            new_row = pd.DataFrame([{**updated_values, self.column_name_key: record_id}])  # Cria um DataFrame com a nova linha
            df = pd.concat([df, new_row], ignore_index=True)
                    
            if self.on_data_change:
                self.on_data_change(df)
            del df
            gc.collect()
            
            OK = messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
        except SQLAlchemyError as e:
            self.log_message(f"Erro SQL ao atualizar o registro:{e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao salvar as alterações: {str(e)}")
            self.button_salvar.config(state="normal")
        except Exception as e:
            self.log_message(f"Erro ao atualizar o registro:{e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao salvar as alterações: {str(e)}")
            self.button_salvar.config(state="normal")
        if OK.lower() == "ok":
            self.destroy()
        
        

   