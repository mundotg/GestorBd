
import queue
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
from utils.validarText import get_query_string_threads, get_valor_idependente_entry,get_query_string

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
        self.queue = queue.Queue()
        self._table_lock = None
        self.load_table_names()
        self.process_queue()

    def setup_ui(self):
        main_content = ttk.Frame(self.frame)
        main_content.pack(fill=tk.BOTH, expand=True)
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure([0, 2], weight=0)
        main_content.rowconfigure(1, weight=1)

        self.setup_input_frame(main_content)
        self.setup_status_bar(main_content)
        self.setup_middle_frame(main_content)
        
    def process_queue(self):
        """Processa a fila de mensagens na thread principal."""
        try:
            while not self.queue.empty():
                message_type, data = self.queue.get_nowait()

                if message_type == "tables":
                    self.tables = data
                    self.table_combobox["values"] = self.tables  # Atualiza a GUI na thread principal
                    self.table_count_var.config(text=f"{len(self.tables)} tabelas")
                    self.log_message(f"Tabelas carregadas: {self.tables}")
                elif message_type == "error":
                    print(f"Erro: {data}")  # Substitua pelo seu sistema de logs ou exibição de erro

        except queue.Empty:
            pass

        # Chama essa função novamente após 100ms para processar novas mensagens
        self.root.after(100, self.process_queue)
    def setup_input_frame(self, parent):
        input_frame = ttk.LabelFrame(parent, text="📌Seleção de Tabela")
        input_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        table_controls = ttk.Frame(input_frame)
        table_controls.pack(fill=tk.X, padx=5, pady=5)
        table_controls.columnconfigure(1, weight=1)

        ttk.Label(table_controls, text="Número de Tabelas:📊").grid(row=0, column=0, sticky=tk.W)
        self.table_count_var =ttk.Label(table_controls, text="Carregando...")
        self.table_count_var.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(table_controls, text="Nome da Tabela:🗃").grid(row=1, column=0, sticky=tk.W)
        self.table_combobox = ttk.Combobox(table_controls, state="normal", values=[])
        self.table_combobox.grid(row=1, column=1, sticky=tk.EW, padx=5)
        

        button_frame = ttk.Frame(table_controls)
        button_frame.grid(row=1, column=2, sticky=tk.E, padx=10)
        
        self.carregar_button = ttk.Button(button_frame, text="🔍Carregar", command=self.carregar_dados_assincrono)
        self.carregar_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️Limpar", command=self.clear_entry).pack(side=tk.LEFT)

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
                     
                    self.queue.put(("tables", tables))
                except Exception as e:
                    self.queue.put(("error", str(e)))

        # Executa a função em uma nova thread
        thread = threading.Thread(target=_fetch_tables, daemon=True)
        thread.start()
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
    
    def load_data(self, max_rows=1000):
        """
        Carrega dados da tabela selecionada, aplicando filtros e paginação assíncrona.

        Args:
            max_rows (int): Número máximo de linhas a recuperar inicialmente.
        """
        table_name = self.table_combobox.get().strip()

        # 🔹 Verifica se uma tabela foi selecionada
        if not table_name:
            messagebox.showwarning("Aviso", "Selecione uma tabela.")
            return

        # 🔹 Verifica se a tabela existe no banco de dados
        if not self.table_exists(table_name):
            messagebox.showerror("Erro", f"A tabela '{table_name}' não existe no banco de dados.")
            return

        try:
            # 🔹 Monta a query base
            base_query = f'SELECT * FROM "{table_name}"'
            filters, params = [], {}

            # 🔹 Obtém metadados das colunas
            columns = {col["name"]: col["type"] for col in inspect(self.engine).get_columns(table_name)}

            # 🔹 Aplica filtros dinamicamente
            for col_name, entry in self.filter_container.column_filters.items():
                value = get_valor_idependente_entry(entry, tk, ttk)
                if value is not None and value != "":
                    filter_condition = get_filter_condition(self, col_name, columns.get(col_name, ""), value, params,self.db_type)
                    if filter_condition:
                        filters.append(filter_condition)

            # 🔹 Constrói a query final
            query_string = get_query_string(base_query, filters, max_rows, self.db_type)

            # 🔹 Log da query para depuração
            self.log_message(f"Executando query: {query_string}")
            self.log_message(f"Parâmetros da query: {params}")

            # 🔹 Carrega os dados iniciais
            self.df = pd.read_sql(text(query_string), self.engine, params=params)

            # 🔹 Caso não haja dados retornados
            if self.df.empty:
                messagebox.showinfo("Info", "Nenhum dado encontrado.")
                return

            # 🔹 Se o número de linhas retornado for igual ao limite, sugere refinar a consulta
            

            # 🔹 Atualiza a interface com os dados carregados
            self.update_table_widget(self.df, table_name)

            # 🔹 Atualiza o status
            self.status_var.set(f"Carregados {len(self.df)} de {max_rows} linhas possíveis.")
            length_df = len(self.df)
            if length_df > max_rows:
                self.log_message(f"Resultados limitados a {max_rows} linhas. Considere refinar sua consulta.", "warning")
            
            if length_df < max_rows:
                return

            unique_cols = [col for col in self.df.columns if self.df[col].is_unique]

            if unique_cols:
                campo_chave = unique_cols[0]  # Usa a primeira coluna única encontrada
            else:
                # Se não encontrou colunas únicas, pega qualquer coluna disponível
                campo_chave = self.df.columns[0]  # Usa a primeira coluna do DataFrame

            # Obtém o valor da última linha para esse campo
            valor_ultima_linha = self.df.iloc[-1][campo_chave]

            # 🔹 Inicia a busca de mais linhas em segundo plano
            threading.Thread(target=self.fetch_remaining_rows, args=(base_query, filters, max_rows,campo_chave,valor_ultima_linha), daemon=True).start()

        except Exception as e:
            self.handle_error("Erro ao carregar dados")

    def fetch_remaining_rows(self, base_query, filters, max_rows, campo_chave, valor_ultima_linha):
        """ Busca e carrega as linhas adicionais em segundo plano, no máximo 1000 registros por vez. """

        while True:
            query_string = get_query_string_threads(base_query, filters, max_rows, self.db_type.lower(), campo_chave, valor_ultima_linha)

            try:
                df = pd.read_sql(text(query_string), self.engine)
                
                if df.empty:
                    break  # Sai do loop se não houver mais dados

                # Atualiza a interface na thread principal
                self.root.after(0, self.update_ui, df)

                # Atualiza valor_ultima_linha com a última linha carregada
                if campo_chave in df.columns:
                    valor_ultima_linha = df[campo_chave].iloc[-1]
                else:
                    self.log_message(f"⚠️ Campo chave '{campo_chave}' não encontrado na resposta.", "error")
                    break  # Sai do loop se não puder continuar a paginação

                # Se o número de registros retornado for menor que max_rows, é porque chegou ao fim
                if len(df) < max_rows:
                    break

            except Exception as e:
                self.log_message(f"❌ Erro ao carregar mais linhas: {e}", "error")
                break

    
    def update_table_widget(self, df, table_name):
        """ Atualiza ou recria o widget da tabela com os novos dados. """
        if self.table_widget:
            self.table_widget.destroy()

        self.table_widget = DataFrameTable(
            master=self.table_frame,
            df=df,
            rows_per_page=15,
            column_width=100,
            edit_enabled=True, 
            delete_enabled=True, 
            engine=self.engine,
            table_name=table_name,
            on_data_change=self.on_data_changed,
            db_type=self.db_type
        )
        self.table_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def update_ui(self, df):
        """ Atualiza a tabela na thread principal """
        self.table_widget.update_table_for_search(df)
        
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
        self.status_bar.config(text=f"Dados modificados: {len(df)} linhas")
        self.log_message("Dados modificados na tabela.")