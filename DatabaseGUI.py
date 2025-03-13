import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Toplevel
import pandas as pd
from sqlalchemy import text
from DataFrameTable import DataFrameTable

class DataAnalysisGUI:
    def __init__(self, root, connection, engine, db_type, current_profile, database_var, dark_mode, connection_status):
        self.root = root
        self.connection = connection
        self.engine = engine
        self.db_type = db_type
        self.dark_mode = dark_mode
        self.current_profile = current_profile
        self.database_var = database_var
        self.connection_status = connection_status
        self.loaded_tables = {}  # Dicionário para armazenar tabelas carregadas

        self.root.title("Consulta de Dados")
        self.root.geometry("700x500")
        self.root.minsize(500, 400)

        self.setup_ui()

    def setup_ui(self):
        """Configura os componentes da interface gráfica."""
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Digite o nome da tabela:").pack(pady=5)
        self.table_entry = ttk.Entry(frame)
        self.table_entry.pack(padx=10, pady=5, fill=tk.X)
        self.table_entry.bind("<Return>", self.load_data)

        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=5, fill=tk.X)

        self.load_button = ttk.Button(button_frame, text="Carregar Dados", command=self.load_data)
        self.load_button.pack(side=tk.LEFT, expand=True)

        self.save_button = ttk.Button(button_frame, text="Salvar Tabela", command=lambda: self.save_table(self.table_entry.get()))
        self.save_button.pack(side=tk.LEFT, expand=True)

        self.load_saved_button = ttk.Button(button_frame, text="Carregar Tabela Salva", command=lambda: self.get_table(self.table_entry.get()))
        self.load_saved_button.pack(side=tk.LEFT, expand=True)

        ttk.Label(frame, text="Tabelas Carregadas:").pack(pady=5)
        self.loaded_tables_combo = ttk.Combobox(frame, state="readonly")
        self.loaded_tables_combo.pack(padx=10, pady=5, fill=tk.X)
        self.loaded_tables_combo.bind("<<ComboboxSelected>>", self.show_saved_table)

        self.duplicate_button = ttk.Button(frame, text="Mostrar Duplicados", command=self.show_duplicates)
        self.duplicate_button.pack(pady=5)

        self.chat_display = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def log_message(self, message):
        """Exibe mensagens na interface."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{self.db_type}: {message}\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.yview(tk.END)

    def save_table(self, table_name):
        """Salva a tabela carregada em um arquivo CSV."""
        if table_name in self.loaded_tables:
            df = self.loaded_tables[table_name]
            df.to_csv(f"tabelas_salvas/{self.current_profile}/{table_name}.csv", index=False)
            self.log_message(f"Tabela '{table_name}' salva com sucesso.")
        else:
            messagebox.showerror("Erro", "Nenhuma tabela carregada para salvar.")

    def get_table(self, table_name):
        """Carrega uma tabela salva anteriormente."""
        try:
            df = pd.read_csv(f"tabelas_salvas/{self.current_profile}/{table_name}.csv")
            self.loaded_tables[table_name] = df
            self.loaded_tables_combo.configure(values=list(self.loaded_tables.keys()))
            self.show_table(table_name, df)
        except FileNotFoundError:
            messagebox.showerror("Erro", "Tabela salva não encontrada.")

    def load_data(self, event=None):
        """Carrega os dados da tabela digitada."""
        table_name = self.table_entry.get().strip()
        if not table_name:
            messagebox.showerror("Erro", "Digite um nome de tabela válido.")
            return

        if table_name in self.loaded_tables:
            self.log_message(f"Tabela '{table_name}' já carregada anteriormente.")
            return

        if not self.connection or not self.engine:
            messagebox.showerror("Erro", "Conexão com o banco de dados não encontrada.")
            return

        try:
            query = text(f"SELECT * FROM {table_name}")
            df = pd.read_sql(query, self.engine)
            self.loaded_tables[table_name] = df
            self.loaded_tables_combo.configure(values=list(self.loaded_tables.keys()))
            self.log_message(f"Dados carregados da tabela: {table_name}\n{df.head().to_string()}")
            self.show_table(table_name, df)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar os dados: {e}")

    def show_table(self, table_name, df):
        """Abre uma nova janela para exibir os dados da tabela."""
        table_window = tk.Toplevel(self.root)
        table_window.title(f"Tabela: {table_name}")
        DataFrameTable(table_window, df)

    def show_saved_table(self, event=None):
        """Exibe uma tabela carregada anteriormente."""
        selected_table = self.loaded_tables_combo.get()
        if selected_table in self.loaded_tables:
            self.show_table(selected_table, self.loaded_tables[selected_table])
        else:
            messagebox.showerror("Erro", "Tabela não encontrada no histórico.")

    def show_duplicates(self):
        """Exibe registros duplicados da tabela carregada."""
        selected_table = self.loaded_tables_combo.get()
        if selected_table in self.loaded_tables:
            df = self.loaded_tables[selected_table]
            duplicates = df[df.duplicated()]
            if not duplicates.empty:
                self.log_message(f"Registros duplicados encontrados na tabela '{selected_table}'.")
                self.show_table(f"Duplicados - {selected_table}", duplicates)
            else:
                self.log_message(f"Nenhum registro duplicado encontrado na tabela '{selected_table}'.")
        else:
            messagebox.showerror("Erro", "Nenhuma tabela carregada ou selecionada.")


def open_gui_gestaodb(parent, connection, engine, db_type, current_profile, database_var, dark_mode, connection_status):
    """Abre a interface de gestão da base de dados em uma nova janela."""
    new_window = Toplevel(parent)
    return DataAnalysisGUI(new_window, connection, engine, db_type, current_profile, database_var, dark_mode, connection_status)
