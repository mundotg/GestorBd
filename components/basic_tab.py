import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable
from sqlalchemy import text, inspect
import pandas as pd
from DataFrameTable import DataFrameTable
from config.DatabaseLoader import get_filter_condition
from components.FilterContainer import FilterContainer
from utils.validarText import get_valor_idependente_entry

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
        self.df = None

        self.setup_ui()
        self.load_table_names()

    def setup_ui(self):
        main_content = ttk.Frame(self.frame)
        main_content.pack(fill=tk.BOTH, expand=True)
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure([0, 2], weight=0)
        main_content.rowconfigure(1, weight=1)

        self.setup_input_frame(main_content)
        self.setup_status_bar(main_content)
        self.setup_middle_frame(main_content)
        

    def setup_input_frame(self, parent):
        input_frame = ttk.LabelFrame(parent, text="Seleção de Tabela")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        table_controls = ttk.Frame(input_frame)
        table_controls.pack(fill=tk.X, padx=5, pady=5)
        table_controls.columnconfigure(1, weight=1)

        ttk.Label(table_controls, text="Número de Tabelas:").grid(row=0, column=0, sticky=tk.W)
        self.table_count_var = tk.StringVar(value="Carregando...")
        ttk.Label(table_controls, textvariable=self.table_count_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(table_controls, text="Nome da Tabela:").grid(row=1, column=0, sticky=tk.W)
        self.table_combobox = ttk.Combobox(table_controls, state="normal", values=[])
        self.table_combobox.grid(row=1, column=1, sticky=tk.EW, padx=5)
        

        button_frame = ttk.Frame(table_controls)
        button_frame.grid(row=1, column=2, sticky=tk.E, padx=10)
        
        self.carregar_button = ttk.Button(button_frame, text="Carregar", command=self.carregar_dados_assincrono)
        self.carregar_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpar", command=self.clear_entry).pack(side=tk.LEFT)

    def setup_middle_frame(self, parent):
        middle_frame = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        middle_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.filter_container = FilterContainer(
            parent=middle_frame,
            log_message=self.log_message,
            aplicar_filter=self.aplicar_filter,
            engine=self.engine,
            status_var=self.status_var,
            table_combobox=self.table_combobox,
            db_type=self.db_type
        )
        
        self.table_frame = ttk.LabelFrame(middle_frame, text="Resultados")
        middle_frame.add(self.filter_container, weight=1)
        middle_frame.add(self.table_frame, weight=3)
        middle_frame.sashpos(0, 200)
    
    def setup_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN, padding=(5, 2))
        status_bar.grid(row=0, column=0, sticky="ew")
    
    def load_table_names(self):
        try:
            if not self.engine:
                raise ValueError("Engine não está configurado.")
            
            self.tables = inspect(self.engine).get_table_names()
            self.table_combobox["values"] = self.tables
            self.table_count_var.set(f"{len(self.tables)} tabelas")
            self.log_message(f"Tabelas carregadas: {self.tables}")
        except Exception as e:
            self.handle_error("Erro ao carregar tabelas", e)
    
    def aplicar_filter(self,apply_filter_var:Any):
        if hasattr(self, "aplicar_filter") and isinstance(apply_filter_var, tk.BooleanVar):
            if not apply_filter_var.get():
                apply_filter_var.set(True)
                self.carregar_dados_assincrono()
        else:
            print("Erro: 'aplicar_filter' não está definido corretamente.")
    
    def carregar_dados_assincrono(self):
        def carregar():
            try:
                self.status_var.set("Carregando dados...")
                self.log_message("Iniciando carregamento de dados...")
                self.root.after(0, self.load_data) 
                self.status_var.set("Carregamento concluído.")
                self.log_message("Carregamento concluído com sucesso.")
            except Exception as e:
                self.handle_error("Erro ao carregar dados", e)
            finally:
                self.carregar_button.config(state="normal")
        
        self.carregar_button.config(state="disabled")
        threading.Thread(target=carregar, daemon=True).start()
    def table_exists(self,table_name):
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()
    
    def load_data(self):
        table_name = self.table_combobox.get().strip()
        if not table_name:
            messagebox.showwarning("Aviso", "Selecione uma tabela.")
            return
        if not self.table_exists(table_name):
            messagebox.showerror("Erro", f"A tabela '{table_name}' não existe no banco de dados.")
            return
        
        try:
            base_query = f'SELECT * FROM "{table_name}"'
            filters, params = [], {}
            columns = {col["name"]: col["type"] for col in inspect(self.engine).get_columns(table_name)}
            # print(f'filtro: {}')
            for col_name, entry in self.filter_container.column_filters.items():
                
                value =get_valor_idependente_entry(entry,tk,ttk)
                # print(f'filtro:{col_name} ={value}')
                if value:
                    filters.append(get_filter_condition(self, col_name, columns.get(col_name, ""), value, params))
            
            query_string = base_query if not filters else f"{base_query} WHERE {' AND '.join(filters)}"
            print(f'query: {query_string}',params)
            self.df = pd.read_sql(text(query_string), self.engine, params=params)
            
            if self.df.empty:
                messagebox.showinfo("Info", "Nenhum dado encontrado.")
                return
            
            if self.table_widget:
                self.table_widget.destroy()
            
            self.table_widget = DataFrameTable(master=self.table_frame,df= self.df,rows_per_page= 15,column_width= 100,edit_enabled= True, delete_enabled=True, 
                                               engine=self.engine,table_name= table_name,on_data_change= self.on_data_changed,db_type=self.db_type)
            self.table_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.status_var.set(f"{len(self.df)} linhas carregadas.")
        except Exception as e:
            self.handle_error("Erro ao carregar dados", e)
    
    def handle_error(self, msg, exception):
        self.log_message(f"{msg}: {exception}\n{traceback.format_exc()}", level="error")
        self.status_var.set(f"Erro: {msg}")
        messagebox.showerror("Erro", f"{msg}: {exception}")
    def clear_entry(self):
        self.table_combobox.set("")
        self.filter_container.clear_filters()
        
        if self.table_widget is not None:
            self.table_widget.destroy()
            self.table_widget = None
            
        self.status_var.set("Pronto")
        self.log_message("Combobox e filtros limpos.")
    def on_data_changed(self, df):
        self.df = df
        self.status_var.set(f"Dados modificados: {len(df)} linhas")
        self.log_message("Dados modificados na tabela.")