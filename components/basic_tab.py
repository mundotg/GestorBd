import datetime
from sqlalchemy import text, inspect
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable
from DataFrameTable import DataFrameTable
import pandas as pd
from DatabaseLoader import get_filter_condition
from components.DataWidger import DatabaseDateWidget

class BasicTab:
    def __init__(self, notebook: ttk.Notebook, config_manager: Any, log_message: Callable, db_type: str, engine: Any, current_profile: str):
        self.config_manager = config_manager
        self.log_message = log_message
        self.db_type = db_type
        self.engine = engine
        self.current_profile = current_profile
        self.root = notebook.master

        self.frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame, text="Consulta Básica")

        self.table_widget = None
        self.tables = []
        self.column_filters = {}
        self.table_frame = None
        self.df = None

        self.setup_ui()
        self.load_table_names()

    def setup_ui(self):
        # Create a main content frame with proper weight configuration
        main_content = ttk.Frame(self.frame)
        main_content.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights properly for responsive layout
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(0, weight=0)  # Header area - fixed height
        main_content.rowconfigure(1, weight=1)  # Table/filter area - expandable
        main_content.rowconfigure(2, weight=0)  # Status bar - fixed height

        # Top section: Input controls
        input_frame = ttk.LabelFrame(main_content, text="Seleção de Tabela")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Improve table selection layout
        table_controls = ttk.Frame(input_frame)
        table_controls.pack(fill=tk.X, pady=5, padx=5)
        table_controls.columnconfigure(1, weight=1)  # Make combobox column expandable
        
        # Table count display
        ttk.Label(table_controls, text="Número de Tabelas:").grid(row=0, column=0, sticky=tk.W, padx=(0,5), pady=(0,5))
        self.table_count_var = tk.StringVar(value="Carregando...")
        ttk.Label(table_controls, textvariable=self.table_count_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=(0,5))
        
        # Table selection
        ttk.Label(table_controls, text="Nome da Tabela:").grid(row=1, column=0, sticky=tk.W, padx=(0,5), pady=2)
        self.table_combobox = ttk.Combobox(table_controls, state="normal")
        self.table_combobox.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        self.table_combobox.bind("<<ComboboxSelected>>", self.load_columns)

        # Button group with consistent spacing
        button_frame = ttk.Frame(table_controls)
        button_frame.grid(row=1, column=2, sticky=tk.E, padx=(10,0))
        ttk.Button(button_frame, text="Carregar", command=self.load_data).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(button_frame, text="Limpar", command=self.clear_entry).pack(side=tk.LEFT)

        # Middle section: Paned window for filter and table areas
        middle_frame = ttk.PanedWindow(main_content, orient=tk.HORIZONTAL)
        middle_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Filter area (left side)
        filter_frame = ttk.LabelFrame(middle_frame, text="Filtros")
        middle_frame.add(filter_frame, weight=1)
        
        # Improve scrollable frame for filters with proper padding
        self.filter_container = ttk.Frame(filter_frame)
        self.filter_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Configure grid weights for responsive scrolling
        self.filter_container.columnconfigure(0, weight=1)
        self.filter_container.rowconfigure(0, weight=1)
        
        # Create canvas with scrollbar for filters
        self.filter_canvas = tk.Canvas(self.filter_container, borderwidth=0, highlightthickness=0)
        self.filter_canvas.grid(row=0, column=0, sticky="nsew")
        
        button_frame = ttk.Frame(self.filter_container)
        button_frame.grid(row=2, column=0, columnspan=4, pady=10, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        
        # Center-align buttons
        buttons_container = ttk.Frame(button_frame)
        buttons_container.grid(row=0, column=0)
        
        ttk.Checkbutton(buttons_container, variable=self.aplicar_filter, text="Aplicar Filtro", command=self.Aplicar_filter).pack(side=tk.LEFT, padx=10)
        ttk.Button(buttons_container, text="Limpar Filtros", command=self.clear_filters).pack(side=tk.LEFT, padx=10)
        
        # Scrollbars with consistent styling
        self.v_scrollbar = ttk.Scrollbar(self.filter_container, orient="vertical", command=self.filter_canvas.yview)
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")

        self.h_scrollbar = ttk.Scrollbar(self.filter_container, orient="horizontal", command=self.filter_canvas.xview)
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Scrollable frame with proper column configuration
        self.scrollable_frame = ttk.Frame(self.filter_canvas)
        self.scrollable_frame.columnconfigure(0, weight=0)  # Column name - fixed width
        self.scrollable_frame.columnconfigure(1, weight=1)  # Type - fixed width
        self.scrollable_frame.columnconfigure(2, weight=0)  # Filter input - expandable
        
        # Create window inside canvas with proper positioning
        self.filter_window = self.filter_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.filter_canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.filter_canvas.bind("<Configure>", self._on_canvas_configure)
        # Configure event bindings
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))
        )
        
        # Better scroll wheel handling
        self.filter_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.filter_canvas.bind("<Shift-MouseWheel>", self._on_horizontal_scroll)

        # Table area (right side) with more space
        self.table_frame = ttk.LabelFrame(middle_frame, text="Resultados")
        middle_frame.add(self.table_frame, weight=3)
        
        # Set initial pane positions (gives more space to results)
        middle_frame.sashpos(0, 200)
        
        # Filter application checkbox
        self.aplicar_filter = tk.BooleanVar(value=True)

        # Status bar with better styling
        status_frame = ttk.Frame(main_content)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(5, 5))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN, padding=(5, 2))
        status_bar.grid(row=0, column=0, sticky="ew")

    def _on_horizontal_scroll(self, event):
        self.filter_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_canvas_configure(self, event):
        # Update the scrollable region and window width when the canvas size changes
        self.filter_canvas.itemconfig(self.filter_window, width=event.width)
        self.filter_canvas.configure(scrollregion=self.filter_canvas.bbox("all"))

    def _on_mousewheel(self, event):
        if not self.filter_canvas:
            return  # Exit if canvas doesn't exist

        # Get the widget under the mouse cursor
        widget = self.filter_canvas.winfo_containing(event.x_root, event.y_root)

        # Check if widget is valid and belongs to the canvas
        if widget and widget.winfo_exists():
            try:
                parent = widget.winfo_toplevel()
                if parent == self.filter_canvas or widget in self.filter_canvas.winfo_children():
                    self.filter_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except KeyError as e:
                self.log_message(f"Erro ao rolar o canvas: {e}", level="error")
                pass

    def load_table_names(self):
        try:
            inspector = inspect(self.engine)
            self.tables = inspector.get_table_names()
            self.table_combobox["values"] = self.tables
            self.table_count_var.set(f"{len(self.tables)} tabelas")
            self.log_message(f"Tabelas carregadas: {self.tables}")
        except Exception as e:
            self.log_message(f"Erro ao carregar tabelas: {e}", level="error")
            self.status_var.set(f"Erro: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao obter tabelas: {e}")

    def load_columns(self, event=None):
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        table_name = self.table_combobox.get().strip()
        if not table_name:
            return

        try:
            inspector = inspect(self.engine)
            columns = inspector.get_columns(table_name)
            self.column_filters = {}

            # Header with consistent padding and styling
            ttk.Label(self.scrollable_frame, text="Coluna", font=("", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            ttk.Label(self.scrollable_frame, text="Tipo", font=("", 9, "bold")).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            ttk.Label(self.scrollable_frame, text="Filtro", font=("", 9, "bold")).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

            # Separator with proper padding
            separator = ttk.Separator(self.scrollable_frame, orient='horizontal')
            separator.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5, padx=2)

            # Create filter entries with consistent spacing
            for i, col in enumerate(columns):
                row_idx = i + 2  # Start after headers

                col_name = col["name"]
                col_type = str(col["type"]).lower()

                # Column info with proper alignment
                ttk.Label(self.scrollable_frame, text=col_name).grid(row=row_idx, column=0, sticky=tk.W, padx=5, pady=3)
                ttk.Label(self.scrollable_frame, text=col_type).grid(row=row_idx, column=1, sticky=tk.W, padx=5, pady=3)

                # Select appropriate widget for each data type
                if "enum" in col_type:
                    entry = ttk.Combobox(self.scrollable_frame, values=["Opção 1", "Opção 2"], state="readonly")
                    entry.grid(row=row_idx, column=2, sticky=tk.EW, padx=5, pady=3)
                    ttk.Button(self.scrollable_frame, text="📜", width=3, command=lambda c=col: self.show_enum_values(c)).grid(row=row_idx, column=3, padx=5, pady=3)

                elif "integer" in col_type or "float" in col_type or "decimal" in col_type:
                    entry = ttk.Entry(self.scrollable_frame, validate="key")
                    entry.grid(row=row_idx, column=2, sticky=tk.EW, padx=5, pady=3)
                    entry.configure(validatecommand=(entry.register(self.validate_numeric), "%P"))

                elif "boolean" in col_type:
                    entry = tk.BooleanVar()
                    checkbutton = ttk.Checkbutton(self.scrollable_frame, variable=entry)
                    checkbutton.grid(row=row_idx, column=2, sticky=tk.W, padx=5, pady=3)

                elif "date" in col_type or "timestamp" in col_type:
                    try:
                        date_widget = DatabaseDateWidget(
                            self.scrollable_frame,
                            db_type=self.db_type,
                            field_name=col["name"]
                        )
                        date_widget.grid(row=row_idx, column=2, sticky=tk.EW, padx=5, pady=3)
                        self.column_filters[col["name"]] = date_widget
                    except Exception as e:
                        print(f"Error creating date widget: {e}")
                        entry = ttk.Entry(self.scrollable_frame)
                        entry.grid(row=row_idx, column=2, sticky=tk.EW, padx=5, pady=3)
                        self.column_filters[col["name"]] = entry

                else:
                    entry = ttk.Entry(self.scrollable_frame)
                    entry.grid(row=row_idx, column=2, sticky=tk.EW, padx=5, pady=3)

                self.column_filters[col_name] = entry  # Save widget reference

            # Action buttons with better positioning and spacing
            self.status_var.set(f"Colunas carregadas para tabela: {table_name}")
        except Exception as e:
            self.log_message(f"Erro ao carregar colunas: {e}", level="error")
            messagebox.showerror("Erro", f"Erro ao obter colunas: {e}")

    def Aplicar_filter(self):
        self.aplicar_filter.set(True) 

    def validate_numeric(self, value):
        return value.isdigit() or value == "" or value.replace(".", "", 1).isdigit()

    def show_enum_values(self, column):
        messagebox.showinfo("Valores ENUM", f"Valores possíveis: {column['type']}")

    def load_data(self):
        table_name = self.table_combobox.get().strip()
        if not table_name:
            messagebox.showwarning("Aviso", "Selecione uma tabela.")
            return

        try:
            self.status_var.set(f"Carregando {table_name}...")
            base_query = f"SELECT * FROM {table_name}"
            filters = []
            params = {}

            inspector = inspect(self.engine)
            columns = {col["name"]: col["type"] for col in inspector.get_columns(table_name)}

            for col_name, entry in self.column_filters.items():
                value = entry.get().strip()
                if value:
                    try:
                        filter_condition = get_filter_condition(self, col_name, columns.get(col_name, ""), value, params)
                        filters.append(filter_condition)
                    except ValueError as e:
                        messagebox.showwarning("Aviso", str(e))
                        return

            query_string = base_query if not filters else f"{base_query} WHERE {' AND '.join(filters)}"
            query = text(query_string)

            self.df = pd.read_sql(query, self.engine, params=params)

            if self.df.empty:
                messagebox.showinfo("Info", "Nenhum dado encontrado com os filtros aplicados.")
                return

            if self.table_widget:
                self.table_widget.destroy()

            self.table_widget = DataFrameTable(
                master=self.table_frame,
                df=self.df,
                rows_per_page=15,
                column_width=100,
                on_data_change=self.on_data_changed,
                edit_enabled=True,
                delete_enabled=True
            )
            self.table_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            self.status_var.set(f"{len(self.df)} linhas carregadas.")

        except Exception as e:
            error_message = f"Erro ao carregar dados: {e}"
            self.status_var.set(f"Erro: {error_message}")
            self.log_message(error_message, level="error")
            messagebox.showerror("Erro", error_message)

    def clear_entry(self):
        self.table_combobox.set("")
        self.clear_filters()
        
        if self.table_widget is not None:
            self.table_widget.destroy()
            self.table_widget = None
            
        self.status_var.set("Pronto")
        self.log_message("Combobox e filtros limpos.")

    def clear_filters(self):
        for entry in self.column_filters.values():
            entry.delete(0, tk.END)
        self.aplicar_filter.set(False)
        self.log_message("Filtros limpos.")

    def on_data_changed(self, df):
        self.df = df
        self.status_var.set(f"Dados modificados: {len(df)} linhas")
        self.log_message("Dados modificados na tabela.")