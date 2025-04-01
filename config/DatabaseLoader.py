from datetime import datetime
import pandas as pd
from tkinter import messagebox
from sqlalchemy import UUID, Boolean, Date, DateTime, Numeric

DATA_TYPE_FORMATS = {
        "timestamp": "%Y-%m-%d %H:%M:%S",
        "datetime": "%Y-%m-%d %H:%M",
        "date": "%Y-%m-%d",
        "time": "%H:%M:%S",
    }
options = ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle", "MongoDB", "MariaDB"]
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

def parse_date(date_value, col_type_str):
    # Formatos de data permitidos
    DATA_TYPE_FORMATS = {
        "timestamp": "%Y-%m-%d %H:%M:%S",
        "datetime": "%Y-%m-%d %H:%M",
        "date": "%Y-%m-%d",
        "time": "%H:%M:%S",
    }
    
    # Define o formato esperado conforme o tipo da coluna
    fmt = DATA_TYPE_FORMATS.get(col_type_str, "%Y-%m-%d %H:%M:%S")
    
    # Lista de formatos alternativos para tentar
    formatos_alternativos = [
        fmt,  
        "%Y-%m-%d",  # ✅ Suporte a datas já nesse formato
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%m/%d/%y %H",
        "%m/%d/%y"
    ]
    
    # Testa cada formato até encontrar um válido
    for formato in formatos_alternativos:
        try:
            data_convertida = datetime.strptime(date_value, formato)
            
            # Retorna a data formatada no mesmo estilo de entrada
            return data_convertida.strftime(formato)
        except ValueError:
            continue  # Tenta o próximo formato
    
    # Se nenhum formato for válido, gera erro
    raise ValueError(f"Formato inválido para '{date_value}'. Formatos permitidos: {', '.join(formatos_alternativos)}")


def get_filter_condition(self, col_name, col_type, value, params, db_type="postgres"):
    """
    Retorna a condição SQL correta para a coluna com base no tipo de dado e no banco de dados.
    """
    try:
        value = value.strip()
        if value == "":
            raise ValueError(f"Valor inválido para '{col_name}': campo não pode estar vazio.")

        col_type_str = str(col_type).lower()

        # 🔹 Suporte para Enum
        if self.enum_values.get(col_name) not in [None, "", []]:
            params[col_name] = value
            return f"{col_name} = :{col_name}"

        # 🔹 Suporte para UUID
        if "uuid" in col_type_str:
            value = str(UUID(value))  # Valida UUID
            params[col_name] = value
            return f"{col_name} = :{col_name}"

        # 🔹 Suporte para Números (Integer, Numeric)
        if "numeric" in col_type_str or "integer" in col_type_str or isinstance(col_type, Numeric):
            params[col_name] = float(value)
            return f"{col_name} = :{col_name}"

        # 🔹 Suporte para Booleanos
        if "boolean" in col_type_str or isinstance(col_type, Boolean):
            boolean_map = {"true": True, "1": True, "yes": True, "sim": True, 
                           "false": False, "0": False, "no": False, "não": False}
            if value.lower() not in boolean_map:
                raise ValueError(f"Valor inválido para booleano na coluna '{col_name}'.")
            params[col_name] = boolean_map[value.lower()]
            return f"{col_name} = :{col_name}"

        # 🔹 Suporte para Datas e Timestamps
        if "date" in col_type_str or "timestamp" in col_type_str or isinstance(col_type, (Date, DateTime)) or col_type_str == "time":
            db_type_lower = db_type.lower()
            if db_type_lower in ["postgresql", "postgres"]:
                condition = f"CAST({col_name} AS TEXT) LIKE :{col_name}"
            elif db_type_lower in ["mysql", "sql server"]:
                condition = f"CONVERT({col_name}, CHAR) LIKE :{col_name}"
            elif db_type_lower == "sqlite":
                condition = f"{col_name} LIKE :{col_name}"  # No SQLite, colunas de data já são strings
            else:
                params[col_name] = value
                return f"{col_name} = :{col_name}"

            params[col_name] = f"%{value}%"
            return condition

        # 🔹 Suporte para JSON (convertendo para texto)
        if "json" in col_type_str:
            params[col_name] = f"%{value}%"
            if db_type_lower in ["postgresql", "postgres"]:
                return f"{col_name}::TEXT LIKE :{col_name}"  # JSONB no PostgreSQL
            return f"CAST({col_name} AS TEXT) LIKE :{col_name}"

        # 🔹 Suporte para Strings (text, char, varchar)
        if "text" in col_type_str or "char" in col_type_str or "varchar" in col_type_str:
            params[col_name] = f"%{value}%"
            return f"{col_name} LIKE :{col_name}"

        raise TypeError(f"Tipo de coluna '{col_type}' não suportado para filtros.")

    except (ValueError, TypeError) as e:
        raise ValueError(f"Erro ao processar '{col_name}': {e}")
