import threading
import time
import tkinter as tk
from tkinter import ttk
import traceback
from typing import Any, List, Union
import pandas as pd
from config.salavarInfoAllColumn import get_columns_by_table, save_columns_to_file
import sqlparse
from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML
from sqlalchemy import text
from DataFrameTable import DataFrameTable
from pygments import lex
from pygments.lexers import SqlLexer
from pygments.token import Token

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
        self.file_open = ""

        self.setup_ui()

        
    def setup_ui(self):
        """Configura a interface da aba de consulta SQL com realce de sintaxe."""
        # Título da seção
        title_label = ttk.Label(self.frame, text="Consulta SQL:")
        title_label.pack(pady=(0, 10))  # Pequeno espaço abaixo

        # Área de edição SQL
        self._create_editor_area()

        # Botões de ação
        self._create_buttons()

        # Configuração de realce e atalhos
        self._setup_tags()
        self._bind_shortcuts()

        # Status na parte inferior
        status_label = ttk.Label(self.frame, textvariable=self.status_var, foreground="gray")
        status_label.pack(pady=(10, 0))  # Espaço acima

    def _create_editor_area(self):
        """Cria o editor de SQL com barra de rolagem, ajustável ao tamanho da tabela."""
        editor_frame = ttk.Frame(self.frame)
        editor_frame.pack(fill=tk.X, padx=5, pady=(5, 10))  # Só preencher horizontalmente

        self.sql_text = tk.Text(
            editor_frame,
            font=("Courier New", 11),
            wrap=tk.WORD,
            height=8,
            undo=True
        )
        self.sql_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        scroll = ttk.Scrollbar(editor_frame, command=self.sql_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.sql_text.config(yscrollcommand=scroll.set)

        self.sql_text.bind("<KeyRelease>", self.highlight_sql)

        # ----------- Atalhos extras -----------
        self.sql_text.bind("<Control-c>", lambda event: self.sql_text.event_generate("<<Copy>>"))
        # self.sql_text.bind("<Control-v>", lambda event: self.sql_text.event_generate("<<Paste>>"))
        self.sql_text.bind("<Control-x>", lambda event: self.sql_text.event_generate("<<Cut>>"))
        self.sql_text.bind("<Control-z>", lambda event: self.sql_text.event_generate("<<Undo>>"))
        self.sql_text.bind("<Control-y>", lambda event: self.sql_text.event_generate("<<Redo>>"))
        self.sql_text.bind("<Control-s>", self.save_file)
        self.sql_text.bind("<Control-f>", self.find_text)
        # --------------------------------------

    def select_all(self, event=None):
        """Seleciona todo o texto do editor."""
        self.sql_text.tag_add("sel", "1.0", "end-1c")
        return "break"

    def save_file(self, event=None):
        """Salva o conteúdo do editor em um arquivo .sql."""
        try:
            from tkinter import filedialog
            file_path = self.file_open
            if not file_path:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".sql",
                    filetypes=[("Arquivos SQL", "*.sql"), ("Todos os arquivos", "*.*")]
                )
            if file_path:
                content = self.sql_text.get("1.0", "end-1c")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.file_open = file_path  # atualiza para uso futuro
        except Exception as e:
            self.handle_error("Erro ao salvar SQL", e)
            self.carregar_button.config(text="🔍 Executar", state="normal")

                
    def open_file(self, event=None):
        """Abre um arquivo .sql e exibe o conteúdo no editor."""
        try:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                defaultextension=".sql",
                filetypes=[("Arquivos SQL", "*.sql"), ("Todos os arquivos", "*.*")]
            )

            if file_path:
                self.file_open = file_path
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.sql_text.delete("1.0", "end")  # Limpa o editor
                    self.sql_text.insert("1.0", content)  # Insere novo conteúdo
        except Exception as e:
            self.handle_error("Erro ao executar SQL", e)
            self.carregar_button.config(text="🔍 Executar", state="normal")

    def find_text(self, event=None):
        """Busca texto dentro do editor."""
        from tkinter import  simpledialog
        search_term = simpledialog.askstring("Buscar", "Digite o texto para buscar:")
        if search_term:
            start_pos = "1.0"
            self.sql_text.tag_remove('found', '1.0', tk.END)
            while True:
                start_pos = self.sql_text.search(search_term, start_pos, nocase=1, stopindex=tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_term)}c"
                self.sql_text.tag_add('found', start_pos, end_pos)
                start_pos = end_pos
            self.sql_text.tag_config('found', background='yellow', foreground='black')
            self.highlight_sql()


        
    def _create_buttons(self):
        """Cria os botões de ação alinhados à direita no final do painel."""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=5, padx=10)

        right_container = ttk.Frame(button_frame)
        right_container.pack(side=tk.RIGHT)  # Container que vai para a direita

        # Botões
        self.carregar_button = ttk.Button(right_container, text="🔍 Executar (Ctrl+Enter)", command=self.carregar_dados_assincrono)
        limpar_button = ttk.Button(right_container, text="🧹 Limpar (Ctrl+L)", command=self.clear_sql)
        abrir_button = ttk.Button(right_container, text="📂 Abrir ficheiro salvo", command=self.open_file)

        # Posicionamento
        abrir_button.pack(side=tk.LEFT, padx=(0, 10))
        self.carregar_button.pack(side=tk.LEFT, padx=(0, 10))
        limpar_button.pack(side=tk.LEFT)




    def _setup_tags(self):
        """Define estilos para realce de sintaxe."""
        styles = {
            "keyword": "blue",
            "string": "green",
            "number": "darkorange",
            "operator": "purple",
            "comment": "gray"
        }
        for tag, color in styles.items():
            self.sql_text.tag_configure(tag, foreground=color)

    def _bind_shortcuts(self):
        """Atalhos de teclado personalizados."""
        self.sql_text.bind("<Control-Return>", lambda e: self.carregar_dados_assincrono())
        self.sql_text.bind("<Control-l>", lambda e: self.clear_sql())

    def highlight_sql(self, event=None):
        """Aplica realce de sintaxe ao conteúdo SQL."""
        content = self.sql_text.get("1.0", tk.END)
        
        for tag in ["keyword", "string", "number", "operator", "comment"]:
            self.sql_text.tag_remove(tag, "1.0", tk.END)

        token_map = {
            Token.Keyword: "keyword",
            Token.String: "string",
            Token.Number: "number",
            Token.Operator: "operator",
            Token.Comment: "comment"
        }

        # Posição inicial
        start_line = 1
        start_col = 0

        for token, value in lex(content, SqlLexer()):
            lines = value.split('\n')
            tag = next((tag_name for ttype, tag_name in token_map.items() if token in ttype), None)
            
            if tag and value.strip():  # Evita realce de espaços vazios
                start_index = f"{start_line}.{start_col}"
                if len(lines) == 1:
                    end_index = f"{start_line}.{start_col + len(value)}"
                else:
                    end_index = f"{start_line + len(lines) - 1}.{len(lines[-1])}"

                self.sql_text.tag_add(tag, start_index, end_index)

            # Atualiza posição
            if len(lines) == 1:
                start_col += len(lines[0])
            else:
                start_line += len(lines) - 1
                start_col = len(lines[-1])

                
    def carregar_dados_assincrono(self):
        """Inicia uma thread para carregar os dados."""
        if self.stop_event and not self.stop_event.is_set():
            self.stop_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join()
            self.stop_event = None
            self.carregar_button.config(text="🔍 Executar (Ctrl+Enter)", state="normal")
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
                self.carregar_button.config(text="🔍 Executar (Ctrl+Enter)", state="normal")
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
        """
        Extrai os nomes das tabelas da consulta SQL.
        Funciona para instruções SELECT simples, JOINs, etc.
        """
        import re
        # Remove comentários SQL
        query = re.sub(r'--.*?$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)

        # Procurar palavras após FROM ou JOIN
        tables = re.findall(r'\bFROM\s+([^\s,;]+)|\bJOIN\s+([^\s,;]+)', query, flags=re.IGNORECASE)

        # Extrair os nomes reais (de grupos de captura)
        flat_tables = [t for pair in tables for t in pair if t]
        
        # Remover alias (ex: "usuarios u" → "usuarios")
        table_names = [t.split()[0] for t in flat_tables]
        
        # Remover duplicatas mantendo ordem
        seen = set()
        unique_tables = [t for t in table_names if not (t in seen or seen.add(t))]

        return unique_tables


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
                # print(df)
                self.log_message(f"Consulta SQL executada com sucesso: {query}")
                tables = self.extract_tables_from_query(query)
                self.frame.after(0, lambda: self.update_table_widget(df, tables,query))
                if len(df) < max_rows:
                    self.carregar_button.config(text="🔍 Executar", state="normal")
                else:
                    self.carregar_button.config(text="🔍 Executar (Ctrl+Enter)", state="normal")
                    self.log_message(f"⚠️ Apenas os primeiros {max_rows} resultados foram carregados.")
        except Exception as e:
            self.handle_error("Erro ao executar SQL", e)
            self.carregar_button.config(text="🔍 Executar", state="normal")
            
    def simulate_get_columns_from_df(self, df,table_name):
        simulated_columns = []
        name_data= "".join(table_name)
        simulated_columns = get_columns_by_table(name_data, "tables_columns_data.pkl", log_message=self.log_message)
        if simulated_columns:
            return simulated_columns
        simulated_columns = []
        if df.empty:
            # print("DataFrame vazio detectado em simulate_get_columns_from_df.")
            return  # Ou exiba um erro amigável aqui
        for col in df.columns:
            # Verifica se o nome da coluna é algo como 'tabela.coluna', se precisar separar
            # (Aqui você pode ajustar a lógica conforme a necessidade, dependendo do formato do nome da coluna)
            table_name, column_name = (col.split('.', 1) if '.' in col else (None, col))
           
            # Cria o dicionário de informações da coluna
            column_info = {
                'name': column_name,  # Usa o nome da coluna após o possível split
                'type': str(df[col].dtype),
                'nullable': df[col].isnull().any(),
                'default': None,  # DataFrame não tem essa informação
                'primary_key': False  # DataFrame também não sabe disso
            }

            # Se a coluna tiver um nome de tabela (ou alias), adicione essa informação, se necessário
            if table_name:
                column_info['table'] = table_name  # Pode armazenar a tabela associada, se desejado

            simulated_columns.append(column_info)
        if save_columns_to_file({table_name: simulated_columns}, "tables_columns_data.pkl", log_message=self.log_message):
                    self.log_message("Metadados da tabela salvos com sucesso", "info")
        return simulated_columns


    def update_table_widget(self, df: pd.DataFrame, table_name: Union[str,list],query_string: str = None):
        """Atualiza o widget da tabela com os dados obtidos."""
        if self.table_widget:
            self.table_widget.destroy()

        self.table_widget = DataFrameTable(
            master=self.table_frame,
            databse_name=self.databese_name,
            df=df,
            rows_per_page=50,
            column_width=100,
            edit_enabled=False,
            delete_enabled=False,
            engine=self.engine,
            table_name=table_name,
            log_message=self.log_message,
            on_data_change=None,
            db_type=self.db_type,
            columns=self.simulate_get_columns_from_df(df,table_name),
            enum_values={},
            query_executed=query_string
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

