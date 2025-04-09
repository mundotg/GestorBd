
import gc
import threading
import time
from tkinter import font
import traceback
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable
from sqlalchemy import text, inspect
import pandas as pd
from DataFrameTable import DataFrameTable
from components.ComboBoxComBusca import ComboBoxComBusca
from config.DatabaseLoader import get_filter_condition
from components.FilterContainer import FilterContainer
from utils.validarText import get_query_string_threads, get_valor_idependente_entry,get_query_string

class BasicTab:
    def __init__(self, notebook: ttk.Notebook, config_manager: Any, log_message: Callable, db_type: str, engine: Any, current_profile: str,database_var):
        self.config_manager = config_manager
        self.log_message = log_message
        self.db_type = db_type.strip().lower()
        self.engine = engine
        self.current_profile = current_profile
        self.root = notebook.master
        self.enum_values = {}
        self.stop_event = None
        self.thread = None
        self.frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.frame, text="Consulta Básica")
        self.database_var = database_var
        self.table_widget = None
        self.tables = []
        self.filtered_options = []
        self.column_filters = {}
        self.df = None
        self.columns = {}
        self.setup_ui()
        self._table_lock = None
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
        
    def process_queue(self,tables):
        """Processa a fila de mensagens na thread principal."""
        self.tables = tables
        self.table_combobox["value"]=tables # Atualiza a GUI na thread principal
        self.table_count_var.config(text=f"{len(tables)} tabelas")
    def filter_options(self, event=None):
        search_term = self.selected_option.get().lower()
        # Filtra as opções com base no que foi digitado
        self.filtered_options = [option for option in self.tables if search_term in option.lower()]
        # Atualiza as opções da ComboBox
        self.table_combobox['values'] = self.filtered_options
        
    def setup_input_frame(self, parent):
        self.title_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.normal_font = font.Font(family="Helvetica", size=10)
        self.small_font = font.Font(family="Helvetica", size=9, slant="italic")
        input_frame = ttk.LabelFrame(parent, text="📌Seleção de Tabela")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        table_controls = ttk.Frame(parent)
        table_controls.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        # table_controls.pack(fill=tk.X, padx=5, pady=5)
        table_controls.columnconfigure(1, weight=1)

        ttk.Label(table_controls, text="Número de Tabelas:📊").grid(row=0, column=0, sticky=tk.W)
        self.table_count_var =ttk.Label(table_controls, text="Carregando...")
        self.table_count_var.grid(row=0, column=1, sticky=tk.W)
        self.selected_option = tk.StringVar()
        ttk.Label(table_controls, text="Nome da Tabela:🗃").grid(row=1, column=0, sticky=tk.W)
        self.table_combobox = ttk.Combobox(table_controls, 
                                     textvariable=self.selected_option, 
                                     values=self.filtered_options, 
                                     state="normal",
                                     font=self.normal_font,
                                     width=10)  # Largura ajustada para a janela
        
        # self.table_combobox.grid(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.table_combobox.bind("<KeyRelease>", self.filter_options)
        self.table_combobox.grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        button_frame = ttk.Frame(table_controls)
        button_frame.grid(row=1, column=2, sticky=tk.E, padx=10)
        self.style = ttk.Style()
        self.style.configure(
            'Green.TButton',
            font=self.normal_font,
            foreground='white',
            background='#4CAF50'
        )
        # Em alguns temas do ttk (como o Windows), pode ser necessário usar map para garantir a cor
        self.style.map(
            'Green.TButton',
            background=[('active', '#45a049'), ('!disabled', '#4CAF50')],
            foreground=[('disabled', 'gray'), ('!disabled', 'white')]
        )
        self.carregar_button = ttk.Button(
            button_frame,
            text="🔍Carregar",
            command=self.carregar_dados_assincrono,
            style='Green.TButton'
        )
        self.carregar_button.pack(side=tk.LEFT, padx=5)

        # Botão "Limpar" com estilo semelhante ou padrão
        ttk.Button(
            button_frame,
            text="🗑️Limpar",
            command=self.clear_entry,
            style='Green.TButton'  # ou use outro estilo se quiser cores diferentes
        ).pack(side=tk.LEFT)
        self.databse_name = self.database_var.get()
    def setup_middle_frame(self, parent):
        middle_frame = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        middle_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        self.filter_container = FilterContainer(
            parent=middle_frame,
            log_message=self.log_message,
            engine=self.engine,
            columns=self.columns,
            enum_values=self.enum_values,
            status_var=self.status_var,
            table_combobox=self.table_combobox,
            db_type=self.db_type,
            update_table_widget = self.carregar_dados_assincrono,
            database_name=self.databse_name
        )
        
        self.table_frame = ttk.LabelFrame(middle_frame, text="Resultados: click duas vezes no item para visualizar")
        middle_frame.add(self.filter_container, weight=1)
        middle_frame.add(self.table_frame, weight=3)
        middle_frame.sashpos(0, 200)
    
    def setup_status_bar(self, parent):
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Pronto")
        self.status_bar = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN, padding=(5, 2))
        self.status_bar.grid(row=0, column=0, sticky="ew")
    
    def load_table_names(self):
        """Carrega os nomes das tabelas do banco de dados de forma assíncrona."""
        
        # Garante que o Lock seja inicializado corretamente
        if not hasattr(self, "_table_lock") or self._table_lock is None:
            self._table_lock = threading.Lock()

        # Se o Lock já estiver em uso, evita concorrência
        if self._table_lock is not None:
            if self._table_lock.locked():
                self.log_message("Carregamento de tabelas já em andamento...", level="warning")
                return  

        def _fetch_tables():
            """Busca as tabelas e atualiza a interface."""
            with self._table_lock:  # Garante que apenas uma thread acesse o código
                try:
                    if not self.engine:
                        raise ValueError("Engine do banco de dados não está configurado.")

                    # Obtém as tabelas do banco de forma segura
                    tables = inspect(self.engine).get_table_names()
                     
                    self.root.after(100, self.process_queue, tables)
                except Exception as e:
                    self.queue.put(("error", str(e)))

        # Executa a função em uma nova thread
        thread = threading.Thread(target=_fetch_tables, daemon=True)
        thread.start()
    
    def carregar_dados_assincrono(self):
        if self.stop_event and not self.stop_event.is_set():
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join()
                self.stop_event = None
                self.carregar_button.config(text="🔍Carregar", state="normal")
                return
        def carregar():
            try:
                self.carregar_button.config(text="❌Cancelar")
                self.status_var.set("Carregando dados...")
                self.log_message("Iniciando carregamento de dados...")
                self.root.after(0, self.load_data) 
                self.status_var.set("Carregamento concluído.")
                self.log_message("Carregamento concluído com sucesso.")
            except Exception as e:
                self.handle_error("Erro ao carregar dados", e)
        # self.carregar_button.config(state="disabled")
        threading.Thread(target=carregar, daemon=True).start()

        
        
    def table_exists(self,table_name):
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()
    def clear_entry(self):
        self.table_combobox.set("")
        self.filter_container.clear_filters()
        
        if self.table_widget is not None:
            self.table_widget.destroy()
            self.table_widget = None
        if self.stop_event and not self.stop_event.is_set():
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join()
            self.stop_event = None

            
        self.status_var.set("Pronto")
        self.log_message("Combobox e filtros limpos.")
    def on_data_changed(self, df):
        self.table_widget.update_table(df)
        self.status_var.set(f"Dados modificados: {len(df)} linhas")
        self.status_bar.config(text=f"Dados modificados: {len(df)} linhas")
        self.log_message("Dados modificados na tabela.")
    
    def load_data(self, max_rows=1000):
        """Finaliza a thread antiga e inicia uma nova."""
        # Evita erro caso self.thread não exista na primeira execução
        if self.stop_event and not self.stop_event.is_set():
            print("Finalizando a thread anterior...")
            self.stop_event.set()  # Sinaliza para a thread parar
            if self.thread and self.thread.is_alive():
                self.thread.join()  # Aguarda a finalização corretamente
            self.thread = None
            self.stop_event = None
            print("fechado com sucesso")
            time.sleep(1)

        # Criando e iniciando uma nova thread
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._load_data_thread, args=(max_rows,), daemon=True)
        print("Iniciando nova thread...")
        self.thread.start()
        
        
    

    def _load_data_thread(self, max_rows):
        """Executa a carga inicial de dados em segundo plano."""
        try:
            table_name = self.table_combobox.get().strip()

            if not table_name:
                self.root.after(0, lambda: messagebox.showwarning("Aviso", "Selecione uma tabela."))
                self.carregar_button.config(text="🔍Carregar", state="normal")
                return

            if not self.table_exists(table_name):
                self.root.after(0, lambda: messagebox.showerror("Erro", f"A tabela '{table_name}' não existe no banco de dados."))
                self.carregar_button.config(text="🔍Carregar", state="normal")
                return
            filter_column = self.filter_container.get_for_query()
            
            base_query = f'SELECT {filter_column if filter_column is not None else ""} FROM {self.validate_database(table_name)}'
            filters, params = [], {}
            columns = {col["name"]: col["type"] for col in inspect(self.engine).get_columns(table_name)}
            print(" testnado  *****")
            for col_name, entry in self.filter_container.column_filters.items():
                value = get_valor_idependente_entry(entry, tk, ttk)
                if value is not None and value != "":
                    filter_condition = get_filter_condition(self, col_name, columns.get(col_name, ""), value, params, self.db_type)
                    if filter_condition:
                        filters.append(filter_condition)

            # self.log_message(f"Executando query: {query_string}")
            # self.log_message(f"Parâmetros da query: {params}")

            try:
                query_string = get_query_string(base_query, filters, max_rows, self.db_type)

                with self.engine.connect() as conn:
                    result = conn.execute(text(query_string), params)
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())

                self.root.after(0, lambda: self.update_table_widget(df, table_name))

            except Exception as e:
                self.handle_error("Erro ao carregar dados", e)

            # self.root.after(0, lambda: self.update_table_widget(df, table_name))
            self.status_var.set(f"Carregados {len(df)} de {max_rows} linhas possíveis.")
            print(f"Carregados {len(df)} de {max_rows} linhas possíveis.")

            if len(df) < max_rows:
                self.carregar_button.config(text="🔍Carregar", state="normal")
                return

            unique_cols = [col for col in df.columns if df[col].is_unique]
            campo_chave = unique_cols[0] if unique_cols else df.columns[0]
            valor_ultima_linha = df.iloc[-1][campo_chave]

            threading.Thread(target=self.fetch_remaining_rows, args=(base_query, filters, max_rows, campo_chave, valor_ultima_linha,params,df), daemon=True).start()

        except Exception as e:
            self.handle_error("Erro ao carregar dados", e)
            self.carregar_button.config(text="🔍Carregar", state="normal")
    def validate_database(self, table_name: str) -> str:
        db_type = self.db_type.lower()

        if db_type == "postgresql":
            return f'"{table_name}"'  # PostgreSQL usa aspas duplas para identificadores

        elif "mysql" in db_type:
            return f"`{table_name}`"  # MySQL usa crases

        elif "mssql" in db_type or "sql server" in db_type:
            return f"[{table_name}]"  # SQL Server usa colchetes

        elif "oracle" in db_type:
            return table_name.upper()  # Oracle geralmente usa nomes em maiúsculas, sem aspas

        else:
            # SQLite usa aspas duplas, como PostgreSQL
            return f'"{table_name}"'

    
    def update_table_widget(self, df, table_name):
        """ Atualiza ou recria o widget da tabela com os novos dados. """
        if self.table_widget:
            self.table_widget.destroy()
        

        self.table_widget = DataFrameTable(
            master=self.table_frame,
            databse_name=self.databse_name,
            df=df,
            rows_per_page=15,
            column_width=100,
            edit_enabled=True, 
            delete_enabled=True, 
            engine=self.engine,
            table_name=table_name,
            log_message=self.log_message,
            on_data_change=self.on_data_changed,
            db_type=self.db_type,
            columns=self.filter_container.columns,
            enum_values=self.filter_container.enum_values,
        )
        self.table_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    
    def fetch_remaining_rows(self, base_query, filters, max_rows, campo_chave, valor_ultima_linha, params,f_df):
        cont = 0
        concat_df = f_df.copy()  # Inicializa um DataFrame vazio para evitar erros
        del f_df
        while True :  # Verifica o evento de parada corretamente
            # print(f"Thread ativa? {not self.stop_event.is_set()}") 
            if not self.stop_event: 
                 break
            if self.stop_event and self.stop_event.is_set() :
                break
            cont += 1
            query_string = get_query_string_threads(base_query, filters, max_rows, self.db_type, campo_chave, valor_ultima_linha)

            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(query_string), params)
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())

                print(f"Tamanho = {len(df)} | Último ID = {valor_ultima_linha}")

                if df.empty:
                    break  # Sai do loop se não houver mais dados

                # Atualiza concat_df corretamente
                if concat_df.empty:
                    concat_df = df 
                else:
                    concat_df = pd.concat([concat_df, df], ignore_index=True).drop_duplicates()
                    

                # Atualiza UI a cada 10 iterações para evitar bloqueio da interface
                valor_ultima_linha = df[campo_chave].iloc[-1] if campo_chave in df.columns else None
                n_linha = len(df)
                
                
                if  n_linha < max_rows:
                    break  
                if cont == 10:
                    self.root.after(0, self.update_ui, concat_df)
                    cont = 0
                    del concat_df
                    concat_df = df.copy()
                    del df
                    gc.collect()

                # Atualiza o valor da última linha para continuar a busca
                # Sai do loop se o último lote de dados for menor que `max_rows`

            except Exception as e:
                error_message = "Erro ao carregar dados"
                self.handle_error(error_message, e)
                self.carregar_button.config(text="🔍Carregar", state="normal")
                break

        # Atualiza a UI com os dados finais após o loop
        if not concat_df.empty:
            if  self.stop_event and not self.stop_event.is_set():
                self.root.after(0, self.update_ui, concat_df)
            del concat_df
        self.carregar_button.config(text="🔍Carregar", state="normal")
        return

    def update_ui(self, df):
        """ Atualiza a tabela na thread principal """
        if not df.empty:
            self.table_widget.update_table_for_search(df)

    def handle_error(self, msg, exception):
        """ Exibe um erro no log e na interface """
        self.log_message(f"{msg}: {exception}\n{traceback.format_exc()}", level="error")
        self.status_var.set(f"Erro: {msg}")
        messagebox.showerror("Erro", f"{msg}: {exception}")