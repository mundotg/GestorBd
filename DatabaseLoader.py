import datetime
import pandas as pd
from tkinter import messagebox

from sqlalchemy import UUID, Boolean, Date, DateTime, Numeric

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
def get_filter_condition(self, col_name, col_type, value, params):
    """
    Retorna a condição SQL correta para a coluna com base no tipo de dado.
    """
    col_type = str(col_type).lower()

    try:
        if "uuid" in col_type:  # Se for UUID, faz comparação exata
            value = str(UUID(value))  # Valida se é um UUID válido
            params[col_name] = value
            return f"{col_name} = :{col_name}"

        elif "numeric" in col_type or "integer" in col_type or isinstance(col_type, Numeric):
            value = float(value)  # Tenta converter para número
            params[col_name] = value
            return f"{col_name} = :{col_name}"

        elif "boolean" in col_type or isinstance(col_type, Boolean):
            if value.lower() in ["true", "1", "yes", "sim"]:
                params[col_name] = True
            elif value.lower() in ["false", "0", "no", "não"]:
                params[col_name] = False
            else:
                raise ValueError("Valor inválido para booleano. Use 'true' ou 'false'.")
            return f"{col_name} = :{col_name}"

        elif "date" in col_type or "timestamp" in col_type or isinstance(col_type, (Date, DateTime)):
            try:
                if ">" in value or "<" in value:  # Permite filtros como ">2024-01-01"
                    op, date_value = value[:1], value[1:].strip()
                    date_parsed = datetime.strptime(date_value, "%Y-%m-%d")
                    params[col_name] = date_parsed
                    return f"{col_name} {op}= :{col_name}"
                else:
                    date_parsed = datetime.strptime(value, "%Y-%m-%d")
                    params[col_name] = date_parsed
                    return f"{col_name} = :{col_name}"
            except ValueError:
                raise ValueError("Formato de data inválido. Use 'YYYY-MM-DD'.")

        else:  # Outros tipos (texto, JSON, etc.)
            params[col_name] = f"%{value}%"
            return f"{col_name}::TEXT LIKE :{col_name}"

    except ValueError as e:
        raise ValueError(f"Erro ao processar {col_name}: {e}")