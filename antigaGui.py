from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import pandas as pd
from sqlalchemy import text
from antigoFrame import DataFrameTable

class DataAnalysisGUI:
    def __init__(self, root, connection, engine, db_type, current_profile, database_var, dark_mode, connection_status, config_manager):
        self.root = root
        self.connection = connection
        self.engine = engine
        self.db_type = db_type
        self.dark_mode = dark_mode
        self.current_profile = current_profile
        self.database_var = database_var
        self.connection_status = connection_status
        self.config_manager = config_manager
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

    def save_table(self, table_name: str) -> None:
        """
        Salva a tabela carregada em um arquivo CSV e armazena seus metadados.

        :param table_name: Nome da tabela a ser salva.
        """
        if table_name not in self.loaded_tables:
            messagebox.showerror("Erro", f"Nenhuma tabela carregada com o nome '{table_name}' para salvar.")
            return

        df = self.loaded_tables[table_name]

        try:
            # Salva em Excel e CSV
            self.config_manager.table_manager.save_table_to_excel(df, table_name)
            self.config_manager.table_manager.save_table_metadata(df, table_name)

            messagebox.showinfo("Sucesso", f"Tabela '{table_name}' salva com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar a tabela '{table_name}': {e}")

    def get_table(self, table_name: str) -> None:
        """
        Carrega uma tabela salva anteriormente.

        :param table_name: Nome da tabela a ser carregada.
        """
        profile_path = Path(f"tabelas_salvas/{self.current_profile}")
        csv_path = profile_path / f"{table_name}.csv"

        if not csv_path.exists():
            messagebox.showerror("Erro", f"Tabela '{table_name}' não encontrada no perfil '{self.current_profile}'.")
            return

        try:
            df = pd.read_csv(csv_path)
            self.loaded_tables[table_name] = df

            # Atualiza a interface
            self.loaded_tables_combo.configure(values=list(self.loaded_tables.keys()))
            self.show_table(table_name, df)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar a tabela '{table_name}': {e}")

    def load_data(self, event=None):
        """Carrega os dados da tabela digitada."""
        table_name = self.table_entry.get().strip()
        if not table_name:
            messagebox.showerror("Erro", "Digite um nome de tabela válido.")
            return

        if table_name in self.loaded_tables:
            messagebox.showinfo("Info", f"Tabela '{table_name}' já carregada anteriormente.")
            return

        if not self.connection or not self.engine:
            messagebox.showerror("Erro", "Conexão com o banco de dados não encontrada.")
            return

        try:
            query = text(f"SELECT * FROM {table_name}")
            df = pd.read_sql(query, self.engine)
            self.loaded_tables[table_name] = df
            self.loaded_tables_combo.configure(values=list(self.loaded_tables.keys()))
            self.show_table(table_name, df)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar os dados: {e}")

    def show_table(self, table_name, df):
        """Abre uma nova janela para exibir os dados da tabela."""
        table_window = tk.Toplevel(self.root)
        table_window.title(f"Tabela: {table_name}")
        app= DataFrameTable(table_window, df)
        app.pack(expand=True, fill="both", padx=10, pady=10)
        

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
                self.show_table(f"Duplicados - {selected_table}", duplicates)
            else:
                messagebox.showinfo("Info", f"Nenhum registro duplicado encontrado na tabela '{selected_table}'.")
        else:
            messagebox.showerror("Erro", "Nenhuma tabela carregada ou selecionada.")


def open_gui_gestaodb(parent, connection, engine, db_type, current_profile, database_var, dark_mode, connection_status, config_manager):
    """Abre a interface de gestão da base de dados em uma nova janela."""
    new_window = Toplevel(parent)
    return DataAnalysisGUI(new_window, connection, engine, db_type, current_profile, database_var, dark_mode, connection_status, config_manager)