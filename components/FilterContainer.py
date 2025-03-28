from tkinter import messagebox
import traceback
from typing import Any
from sqlalchemy import inspect, text
import tkinter as tk
from tkinter import ttk
from components.Data_wiget2 import DateTimeEntry
from config.DatabaseLoader import get_filter_condition
from components.DataWidget import DatabaseDateWidget
from utils.validarText import _fetch_enum_values, validar_numero_float, validar_numero_inteiro

class FilterContainer(ttk.LabelFrame):
    def __init__(self, parent, log_message, engine: Any, db_type: str, status_var: Any, table_combobox: Any, aplicar_filter: Any, *args, **kwargs):
        super().__init__(parent, text="Filtros", *args, **kwargs)
        self.log_message = log_message
        self.engine = engine
        self.status_var = status_var
        self.table_combobox = table_combobox
        self.aplicar_filter = aplicar_filter
        self.enum_values = {}
        self.db_type = db_type
        
        self._setup_ui()
    
    def _setup_ui(self):
        # Configurar o container para preencher todo o espaço disponível
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.container = ttk.Frame(self)
        self.container.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # Configurar o container para preencher todo o espaço
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)
        
        self._setup_canvas()
        self._setup_scrollbars()
        self._setup_buttons()
        
        self.table_combobox.bind("<<ComboboxSelected>>", self.load_columns)
    
    def _setup_canvas(self):
        self.filter_canvas = tk.Canvas(self.container, borderwidth=0, highlightthickness=0)
        self.filter_canvas.grid(row=0, column=0, sticky="nsew")
        
        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.filter_window = self.filter_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configurar o scrollable_frame para que as colunas sejam responsivas
        self.scrollable_frame.columnconfigure(2, weight=1)  # A coluna dos widgets de filtro expande
        
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", lambda e: self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all")))
    
    def _setup_scrollbars(self):
        self.v_scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.filter_canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.h_scrollbar = ttk.Scrollbar(self.container, orient="horizontal", command=self.filter_canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.filter_canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.filter_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.filter_canvas.bind("<Shift-MouseWheel>", self._on_horizontal_scroll)
    
    def aplicar_filter_func(self):
        self.aplicar_filter(apply_filter_var=self.aplicar_filter_var)
    
    def _setup_buttons(self):
        button_frame = ttk.Frame(self.container)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Configurar o button_frame para que os botões fiquem bem posicionados
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        self.aplicar_filter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_frame, text="Aplicar Filtro", variable=self.aplicar_filter_var, command=self.aplicar_filter_func).grid(row=0, column=0, padx=10, sticky="w")
        ttk.Button(button_frame, text="Limpar Filtros", command=self.clear_filters).grid(row=0, column=1, padx=10, sticky="e")
    
    def _on_canvas_configure(self, event):
        self.filter_canvas.itemconfig(self.filter_window, width=event.width)
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.filter_canvas.yview_scroll(-1 * (event.delta // 120), "units")
    
    def _on_horizontal_scroll(self, event):
        self.filter_canvas.xview_scroll(-1 * (event.delta // 120), "units")
    
    def clear_filters(self):
        """Limpa todos os campos de filtro sem destruir os widgets"""
        if not hasattr(self, 'column_filters'):
            self.column_filters = {}  # Inicializa caso ainda não exista
            return
        
        if not self.column_filters:
            return
        for col_name, widget in self.column_filters.items():
            # Limpar o widget baseado em seu tipo
            if isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
            elif isinstance(widget, ttk.Combobox):
                if widget['values']:
                    widget.set(widget['values'][0])  # Resetar para o primeiro valor
                else:
                    widget.set('')
            elif isinstance(widget, ttk.Checkbutton):
                # Para checkbutton, precisamos acessar a variável associada
                for child in widget.winfo_children():
                    if isinstance(child, tk.BooleanVar):
                        child.set(False)
                # Se o widget não tem filhos com variáveis, tentamos buscar por atributos
                if hasattr(widget, 'variable'):
                    widget.variable.set(False)
            elif isinstance(widget, DatabaseDateWidget):
                # Assumindo que o DatabaseDateWidget tem um método clear ou reset
                if hasattr(widget, 'clear'):
                    widget.clear()
                # Se não tiver, tentamos limpar os campos de entrada internos
                else:
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Entry):
                            child.delete(0, tk.END)
                        elif isinstance(child, ttk.Combobox):
                            child.set('')
    
    def load_columns(self, event=None):
        if self.scrollable_frame:
            self.scrollable_frame.destroy()
        table_name = self.table_combobox.get().strip()
        if not table_name:
            return
        if hasattr(self, "scrollable_frame") and self.scrollable_frame:
            self.scrollable_frame.destroy()
        # Criar um novo frame rolável para os filtros
        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.filter_window = self.filter_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        # Configurar o scrollable_frame para que as colunas sejam responsivas
        self.scrollable_frame.columnconfigure(2, weight=1)  # A coluna dos widgets de filtro expande
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_frame.bind("<Configure>", lambda e: self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all")))

        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name, schema=None)
            self.column_filters = {}
            _fetch_enum_values(self=self, columns=columns, text=text, traceback=traceback)
            
            # Configurar o cabeçalho
            headers = ["Coluna", "Tipo", "Filtro"]
            for col, header in enumerate(headers):
                ttk.Label(self.scrollable_frame, text=header, font=("", 9, "bold")).grid(row=0, column=col, sticky=tk.W, padx=5, pady=5)
            
            ttk.Separator(self.scrollable_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky="ew", pady=5, padx=2)
            
            for i, col in enumerate(columns, start=2):
                col_name, col_type = col["name"], str(col["type"]).lower()
                ttk.Label(self.scrollable_frame, text=col_name).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
                
                if "(" in col_type and ")" in col_type:
                    col_value = col_type.split("(")[0].split(")")[0].lower()
                else:
                    col_value = col_type.lower()  # Usa o próprio col_type se não houver parênteses
                
                ttk.Label(self.scrollable_frame, text=col_value).grid(row=i, column=1, sticky=tk.W, padx=5, pady=3)
                self._add_filter_widget(col, col_type, i)
        
            self.status_var.set(f"Colunas carregadas para tabela: {table_name}")
        except Exception as e:
            self.log_message(f"Erro ao carregar colunas: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
            messagebox.showerror("Erro", f"Erro ao obter colunas: {e}")
    
    def get_column_filters(self):
        return self.column_filters
    
    def _add_filter_widget(self, col, col_type, row):
        no_data = True
        if "enum" in col_type:
            values = self.enum_values.get(col["name"], ["Valor não disponível"])
            entry = ttk.Combobox(self.scrollable_frame, values=values, state="readonly")
            entry.set(values[0])  # Set the first value as default
        
        elif "int" in col_type or "integer" in col_type:
            vcmd = self.register(validar_numero_inteiro)
            entry = ttk.Entry(self.scrollable_frame, validate="key", validatecommand=(vcmd, "%P"))
        
        elif "float" in col_type or "decimal" in col_type or "numeric" in col_type:
            vcmd = self.register(lambda s: validar_numero_float(s, allow_float=True))
            entry = ttk.Entry(self.scrollable_frame, validate="key", validatecommand=(vcmd, "%P"))
        
        elif "bool" in col_type or col_type in ["bit", "boolean"]:
            var = tk.BooleanVar(value=False)
            entry = ttk.Checkbutton(self.scrollable_frame, variable=var)
        
        elif "date" in col_type or "timestamp" in col_type or "time" in col_type:
            try:
                widget = DateTimeEntry(self.scrollable_frame,col_type)
                widget.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
                entry = widget.entry
                no_data = False
            except Exception as e:
                self.log_message(f"Erro criando widget de data: {e} ({type(e).__name__})\n{traceback.format_exc()}", level="error")
                entry = ttk.Entry(self.scrollable_frame)
        
        else:
            entry = ttk.Entry(self.scrollable_frame)
        
        # Configurar o widget para ser responsivo
        if no_data:
            entry.grid(row=row, column=2, sticky=tk.EW, padx=5, pady=3)
        self.column_filters[col["name"]] = entry
        
    def on_date_change(self,selected_data):
        """Simple callback to handle date changes."""
        print(f"Date changed: {selected_data}")