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
    try:
        col_type_str = str(col_type).lower()

        if "uuid" in col_type_str:  # Se for UUID, faz comparação exata
            value = str(UUID(value))  # Valida se é um UUID válido
            params[col_name] = value
            return f"{col_name} = :{col_name}"

        elif "numeric" in col_type_str or "integer" in col_type_str or isinstance(col_type, Numeric):
            value = float(value)  # Tenta converter para número
            params[col_name] = value
            return f"{col_name} = :{col_name}"

        elif "boolean" in col_type_str or isinstance(col_type, Boolean):
            value = value.strip().lower()
            if value in ["true", "1", "yes", "sim"]:
                params[col_name] = True
            elif value in ["false", "0", "no", "não"]:
                params[col_name] = False
            else:
                raise ValueError(f"Valor inválido para booleano na coluna '{col_name}'. Use 'true' ou 'false'.")
            return f"{col_name} = :{col_name}"

        elif "date" in col_type_str or "timestamp" in col_type_str or isinstance(col_type, (Date, DateTime)) or col_type_str == "time":
            try:
                # Verifica operadores antes da data (ex: ">2024-01-01")
                op = None
                if value[0] in [">", "<"]:
                    if len(value) > 1 and value[1] == "=":  # Suporta >= e <=
                        op = value[:2]
                        date_value = value[2:].strip()
                    else:
                        op = value[:1]
                        date_value = value[1:].strip()
                else:
                    date_value = value.strip()

                date_parsed = datetime.strptime(date_value, "%Y-%m-%d")
                params[col_name] = date_parsed
                return f"{col_name} {op or '='} :{col_name}"

            except ValueError:
                raise ValueError(f"Formato de data inválido na coluna '{col_name}'. Use 'YYYY-MM-DD'.")

        elif "json" in col_type_str:
            params[col_name] = f"%{value}%"
            return f"CAST({col_name} AS TEXT) LIKE :{col_name}"

        elif "text" in col_type_str or "char" in col_type_str:
            params[col_name] = f"%{value}%"
            return f"{col_name} LIKE :{col_name}"

        else:
            raise TypeError(f"Tipo de coluna '{col_type}' não suportado para filtros.")

    except (ValueError, TypeError) as e:
        raise ValueError(f"Erro ao processar '{col_name}': {e}")
