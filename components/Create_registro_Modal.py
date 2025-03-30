import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from components.CheckboxWithEntry import CheckboxWithEntry
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Any, Callable, Optional, Dict, Union, List, TypedDict
import traceback
import numpy as np
from components.Data_wiget2 import DateTimeEntry
from utils.logger import log_message as escrever
from components.DataWidget import DatabaseDateWidget
from utils.validarText import _fetch_enum_values, get_valor_idependente_entry, validar_numero,convert_values


class ColumnInfo(TypedDict):
    name: str
    type: str
    nullable: bool
    default: Any


class CreateModal(tk.Toplevel):
    """Creates a modal to add a new record to a database table."""

    def __init__(
        self, master: Any, engine, table_name: str, df:Any,
        db_type: str = "postgresql", on_data_change: Optional[Callable[[pd.DataFrame], None]] = None,
        column_types: Optional[Dict[str, str]] = None, enum_values: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize the CreateModal.
        
        Args:
            master: The parent widget
            engine: SQLAlchemy engine
            table_name: Name of the database table
            db_type: Database type (postgresql, mysql, etc.)
            on_data_change: Callback function when data changes
            column_types: Dictionary of column types
            enum_values: Dictionary of enum values for dropdown fields
        """
        super().__init__(master)
        self.engine = engine
        self.table_name = table_name
        self.on_data_change = on_data_change
        self.column_types = column_types or {}
        self.db_type = db_type
        self.field_entries: Dict[str, Union[ttk.Entry, ttk.Combobox, tk.BooleanVar, DatabaseDateWidget, tk.Text]] = {}
        self.enum_values = enum_values or {}
        self.column_info = []
        
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
        
        # Center the window on the screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def _create_widgets(self):
        """Create input fields and buttons."""
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        
        main_frame = ttk.Frame(self, style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with table name
        header_frame = ttk.Frame(main_frame, style="TFrame")
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 5), padx=10)
        
        ttk.Label(header_frame, 
                 text=f"Novo Registro na Tabela: {self.table_name}",
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
        
        canvas.create_window((0, 0), window=self.fields_frame, anchor=tk.NW, tags="win",width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Button configuration
        save_button = ttk.Button(
            button_frame, 
            text="💾Salvar", 
            command=self._save_record
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(
            button_frame,
            text="🗑Limpar",
            command=self._clear_fields
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="❌Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Make sure canvas adjusts to window size
        self.fields_frame.bind("<Configure>", lambda e: self._adjust_canvas_scrollregion(canvas))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig("win", width=e.width-4))
        
        # Mouse wheel scrolling
        self.bind_all("<MouseWheel>", lambda e: self._scroll_canvas(e, canvas))
        
        # Create the fields
        self._create_fields()

    def _adjust_canvas_scrollregion(self, canvas):
        """Adjust the canvas scroll region to encompass all content."""
        canvas.configure(scrollregion=canvas.bbox("all"))

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
                if self._is_system_field(col_name, col_type):
                    continue
                
                # Create label with required indicator
                label_text = f"{col_name}"
                if not nullable:
                    label_text += " *"
                    
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

    def _is_system_field(self, col_name, col_type):
        """Determine if a field is a system field that should be skipped."""
        # Skip auto-increment IDs, created/updated timestamps that are managed by the database
        auto_increment_keywords = ["serial", "identity", "autoincrement"]
        system_field_names = ["id", "created_at", "updated_at", "created_by", "updated_by"]
        
        # Check if it's an auto-increment field
        if any(keyword in col_type.lower() for keyword in auto_increment_keywords):
            return True
            
        # Check if it's a common system field name
        if col_name.lower() in system_field_names:
            # Check if it has a default value (like NOW() for timestamps)
            inspector = inspect(self.engine)
            columns = inspector.get_columns(self.table_name)
            for col in columns:
                if col["name"] == col_name and col.get("default") is not None:
                    return True
                    
        return False

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
            self.log_message(f"Erro ao obter informações das colunas: {traceback.format_exc()}", level="error")
            raise RuntimeError(f"Falha ao obter esquema da tabela: {str(e)}")

    def _scroll_canvas(self, event, canvas):
        """Scroll the canvas with the mouse wheel."""
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
            if "enum" in col_type:
                values = self.enum_values.get(col_name, ["Valor não disponível"])
                widget = ttk.Combobox(self.fields_frame, values=values, state="readonly")
                if default_value:
                    widget.set(str_value)
                elif values:
                    widget.set(values[0])  # Set the first value as default
            
            elif "int" in col_type or "integer" in col_type:
                vcmd = self.register(validar_numero)
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"))
                if default_value is not None:
                    widget.insert(0, str_value)
            
            elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
                vcmd = self.register(lambda s: validar_numero(s, allow_float=True))
                widget = ttk.Entry(self.fields_frame, validate="key", validatecommand=(vcmd, "%P"))
                if default_value is not None:
                    widget.insert(0, str_value)
            
            elif "bool" in col_type or col_type in ["bit", "boolean"]:
                
                no_data = False
                # var = tk.BooleanVar(value=False)
                entry = CheckboxWithEntry(self.fields_frame)
                entry.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
                entry = entry.entry
            
            elif "date" in col_type or "timestamp" in col_type  or "time" in col_type:
                try:
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

    def _get_widget_value(self, col_name, widget):
        """Get the value from a widget based on its type."""
        if isinstance(widget, tk.BooleanVar):
            return widget.get()
        elif isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        elif isinstance(widget, DatabaseDateWidget):
            return widget.get_date()
        else:
            value = widget.get()
            # Handle empty strings for non-string fields
            if value == "":
                return None
            return value

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
                value = self._get_widget_value(col_name, widget)
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
   

    def build_create_query(self,table_name, updated_values):
        """Constrói dinamicamente uma query de inserção."""
        if not updated_values:
            return None

        # Lista de colunas e placeholders para os valores
        updated_values= convert_values(updated_values=updated_values,np=np)
        columns = ", ".join(updated_values.keys())
        placeholders = ", ".join([f":{col}" for col in updated_values.keys()])

        # Monta a query de inserção
        query = text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})")
        return query

    def _save_record(self):
        """Função genérica para salvar alterações em qualquer banco de dados."""
        try:
            errors = self._validate_fields()
            if errors:
                messagebox.showerror("Validação", "\n".join(errors))
                return
            
            updated_values ={} 
            for col_name, entry in self.field_entries.items():
                updated_values[col_name] = get_valor_idependente_entry(entry,tk,ttk)   
                  
            query = self.build_create_query(self.table_name, updated_values)
            if query is None:
                messagebox.showinfo("Sem alterações", "Nenhuma alteração foi detectada.")
                self.log_message("Nenhuma alteração foi detectada.", level="info")
                return
            
            with self.engine.begin() as conn:
                conn.execute(query, updated_values)
            
            self.log_message(f"Registro {self.record_id} atualizado com sucesso!", level="info")
            
            for col, value in updated_values.items():
                if col in self.df.columns:
                    self.df.at[self.row_index, col] = value
            
            if self.on_data_change:
                self.on_data_change(self.df)
            
            messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
        except SQLAlchemyError as e:
            self.log_message(f"Erro SQL ao atualizar o registro:{e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro de Banco de Dados", f"Falha ao salvar as alterações: {str(e)}")
        except Exception as e:
            self.log_message(f"Erro ao atualizar o registro:{e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Falha ao salvar as alterações: {str(e)}")

   