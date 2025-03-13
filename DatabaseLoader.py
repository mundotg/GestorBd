import pandas as pd
from tkinter import messagebox

class DatabaseLoader:
    """Classe para carregar dados do banco de dados usando Pandas"""
    
    def __init__(self, connection):
        """Inicializa com a conexão do banco"""
        self.connection = connection
        self.df = None  # DataFrame para armazenar os dados carregados

    def load_data(self, table_name: str):
        """Carrega os dados de uma tabela usando Pandas"""
        if not table_name:
            messagebox.showerror("Erro", "Digite um nome de tabela válido.")
            return

        try:
            query = f"SELECT * FROM {table_name}"
            self.df = pd.read_sql(query, self.connection)  # Carregamento usando Pandas
            messagebox.showinfo("Sucesso", f"Dados carregados da tabela: {table_name}")
            print(self.df.head())  # Exibir primeiras linhas para depuração
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar os dados: {e}")
