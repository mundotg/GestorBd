import threading
import time
import tkinter as tk
from tkinter import ttk
import traceback
from typing import Any, Union
import pandas as pd
import sqlparse
from sqlalchemy import text
from DataFrameTable import DataFrameTable

class AdvancedTab:
    """Cria a aba de consultas SQL avançadas."""

    def __init__(self, notebook: ttk.Notebook, config_manager: Any, log_message: Any, database_name,
                 db_type: str, engine: Any, current_profile: str):
        self.config_manager = config_manager
        self.log_message = log_message
        self.db_type = db_type.strip().lower()
        self.engine = engine
        self.current_profile = current_profile
        self.stop_event = None
        self.thread = None
        self.databese_name = database_name
        self.frame = ttk.Frame(notebook, padding=10)
        self.sql_text = None
        self.table_widget = None
        self.status_var = tk.StringVar(value="")
        self.table_frame = ttk.Frame(self.frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_ui()

    def setup_ui(self):
        """Configura a aba de consulta SQL avançada."""
        ttk.Label(self.frame, text="Consulta SQL:").pack(pady=5)

        self.sql_text = tk.Text(self.frame, height=10, width=50)
        self.sql_text.pack(pady=5, fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=5)

        self.carregar_button = ttk.Button(button_frame, text="🔍 Executar", command=self.carregar_dados_assincrono)
        self.carregar_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 Limpar", command=self.clear_sql).pack(side=tk.LEFT, padx=5)

        ttk.Label(self.frame, textvariable=self.status_var, foreground="gray").pack(pady=5)

    def carregar_dados_assincrono(self):
        """Inicia uma thread para carregar os dados."""
        if self.stop_event and not self.stop_event.is_set():
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join()
            self.stop_event = None
            self.carregar_button.config(text="🔍 Executar", state="normal")
            self.status_var.set("Consulta cancelada.")
            return

        def carregar():
            try:
                self.carregar_button.config(text="❌ Cancelar", state="normal")
                self.status_var.set("Carregando dados...")
                self.log_message("Iniciando carregamento de dados...")
                self.load_data()
                self.status_var.set("Carregamento concluído.")
                self.log_message("✅ Carregamento concluído.")
            except Exception as e:
                self.carregar_button.config(text="🔍 Executar", state="normal")
                self.handle_error("Erro ao carregar dados", e)

        threading.Thread(target=carregar, daemon=True).start()

    def is_valid_sql(self, query: str) -> bool:
        """Valida a sintaxe SQL usando sqlparse."""
        try:
            parsed = sqlparse.parse(query)
            return bool(parsed and parsed[0].tokens)
        except Exception:
            return False

    def load_data(self, max_rows=1000):
        """Inicia a execução SQL em uma thread."""
        if self.stop_event and not self.stop_event.is_set():
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join()
            self.thread = None
            self.stop_event = None
            time.sleep(1)

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.execute_sql, args=(max_rows,), daemon=True)
        self.thread.start()
        
    def extract_tables_from_query(self, query: str):
        """Extrai as tabelas da consulta SQL usando sqlparse."""
        parsed = sqlparse.parse(query)
        tables = set()  # Usando set para garantir tabelas únicas

        for stmt in parsed:
            # Itera sobre as palavras-chave e cláusulas da consulta
            for token in stmt.tokens:
                if token.ttype is None:  # Não é um tipo simples como string ou palavra-chave
                    if token.get_real_name():  # Se o token tiver um nome real (como tabela)
                        tables.add(token.get_real_name())

        return list(tables)

    def execute_sql(self, max_rows: int):
        """Executa a consulta SQL validada."""
        query = self.sql_text.get("1.0", tk.END).strip()
        if not query:
            self.carregar_button.config(text="🔍 Executar", state="normal")
            self.status_var.set("❗ Nenhuma consulta digitada.")
            return

        if not self.is_valid_sql(query):
            self.carregar_button.config(text="🔍 Executar", state="normal")
            self.status_var.set("❗ Consulta SQL inválida.")
            return

        try:
            with self.engine.connect() as conn:
                result = conn.execution_options(stream_results=True).execute(text(query))
                df = pd.DataFrame(result.fetchmany(max_rows), columns=result.keys())
                print(df)
                tables = self.extract_tables_from_query(query)
                self.frame.after(0, lambda: self.update_table_widget(df, tables))
                if len(df) < max_rows:
                    self.carregar_button.config(text="🔍 Executar", state="normal")
                else:
                    self.log_message(f"⚠️ Apenas os primeiros {max_rows} resultados foram carregados.")
        except Exception as e:
            self.handle_error("Erro ao executar SQL", e)
            self.carregar_button.config(text="🔍 Executar", state="normal")
    def simulate_get_columns_from_df(self,df):
        simulated_columns = []

        for col in df.columns:
            column_info = {
                'name': col,
                'type': str(df[col].dtype),
                'nullable': df[col].isnull().any(),
                'default': None,            # DataFrame não tem essa info
                'primary_key': False        # DataFrame também não sabe isso
            }
            simulated_columns.append(column_info)

        return simulated_columns

    def update_table_widget(self, df: pd.DataFrame, table_name: Union[str,list]):
        """Atualiza o widget da tabela com os dados obtidos."""
        if self.table_widget:
            self.table_widget.destroy()

        self.table_widget = DataFrameTable(
            master=self.table_frame,
            databse_name=self.databese_name,
            df=df,
            rows_per_page=15,
            column_width=100,
            edit_enabled=False,
            delete_enabled=False,
            engine=self.engine,
            table_name=table_name,
            log_message=self.log_message,
            on_data_change=None,
            db_type=self.db_type,
            columns=self.simulate_get_columns_from_df(df),
            enum_values={},
        )
        self.table_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def clear_sql(self):
        """Limpa o campo de entrada SQL."""
        self.sql_text.delete("1.0", tk.END)
        self.status_var.set("")

    def handle_error(self, title: str, error: Exception):
        """Mostra erro e loga."""
        self.status_var.set(f"❌ {title}: {error}")
        self.log_message(f"{title}: {error} ({type(error).__name__})\n{traceback.format_exc()}","error")

