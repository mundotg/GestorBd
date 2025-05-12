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


def get_filter_condition(self, col_name, col_type, value, params, db_type="postgres",operation="" ,value_otheir_between=""):
    """
    Retorna a condição SQL correta para a coluna com base no tipo de dado e no banco de dados.
    """
    try:
        value = value.strip()
        if value == "":
            raise ValueError(f"Valor inválido para '{col_name}': campo não pode estar vazio.")

        col_type_str = str(col_type).lower()
        if db_type.lower() in ["postgresql", "postgres"]:
            col_name_escaped = f'"{col_name}"'
        else:
            col_name_escaped = col_name
            

        # 🔹 Suporte para Enum
        if self.enum_values.get(col_name) not in [None, "", []]:
            params[col_name] = value
            return f"{col_name_escaped} = :{col_name}"

        # 🔹 Suporte para UUID
        if "uuid" in col_type_str:
            value = str(UUID(value))  # Valida UUID
            params[col_name] = value
            return f"{col_name_escaped} = :{col_name}"

        # 🔹 Suporte para Números (Integer, Numeric)
        if "numeric" in col_type_str or "integer" in col_type_str or isinstance(col_type, Numeric):
            params[col_name] = float(value)
            return f"{col_name_escaped} = :{col_name}"

        # 🔹 Suporte para Booleanos
        if "boolean" in col_type_str or isinstance(col_type, Boolean):
            boolean_map = {"true": True, "1": True, "yes": True, "sim": True, 
                           "false": False, "0": False, "no": False, "não": False}
            if value.lower() not in boolean_map:
                raise ValueError(f"Valor inválido para booleano na coluna '{col_name}'.")
            params[col_name] = boolean_map[value.lower()]
            return f"{col_name_escaped} = :{col_name}"

        # 🔹 Suporte para Datas e Timestamps
        if "date" in col_type_str or "timestamp" in col_type_str or isinstance(col_type, (Date, DateTime)) or col_type_str == "time":
            db_type_lower = db_type.lower()
            if db_type_lower in ["postgresql", "postgres"]:
                condition = f"CAST({col_name_escaped} AS TEXT) LIKE :{col_name}"
            elif db_type_lower in ["mysql", "sql server"]:
                condition = f"CONVERT({col_name_escaped}, CHAR) LIKE :{col_name}"
            elif db_type_lower == "sqlite":
                condition = f"{col_name_escaped} LIKE :{col_name}"  # No SQLite, colunas de data já são strings
            else:
                params[col_name] = value
                return f"{col_name_escaped} = :{col_name}"

            params[col_name] = f"%{value}%"
            return condition

        # 🔹 Suporte para JSON (convertendo para texto)
        if "json" in col_type_str:
            params[col_name] = f"%{value}%"
            if db_type_lower in ["postgresql", "postgres"]:
                return f"{col_name_escaped}::TEXT LIKE :{col_name}"  # JSONB no PostgreSQL
            return f"CAST({col_name_escaped} AS TEXT) LIKE :{col_name}"

        # 🔹 Suporte para Strings (text, char, varchar)
        if "text" in col_type_str or "char" in col_type_str or "varchar" in col_type_str:
            params[col_name] = f"%{value}%"
            return f"{col_name_escaped} LIKE :{col_name}"

        raise TypeError(f"Tipo de coluna '{col_type}' não suportado para filtros.")

    except (ValueError, TypeError) as e:
        raise ValueError(f"Erro ao processar '{col_name}': {e}")
    
    
    
def get_filter_condition_with_operation(self, col_name, col_type, value, params, db_type="postgres", operation="", value_otheir_between=""):
    """
    Retorna a condição SQL correta para a coluna com base no tipo de dado, operação e no banco de dados.
    """
    try:
        value = value.strip()
        if value == "" and operation not in ["Entre"]:
            raise ValueError(f"Valor inválido para '{col_name}': campo não pode estar vazio.")

        col_type_str = str(col_type).lower()
        db_type_lower = db_type.lower()
        if db_type_lower in ["postgresql", "postgres"]:
            col_name_escaped = f'"{col_name}"'
        else:
            col_name_escaped = col_name

        # 🔹 Suporte para Enum
        if self.enum_values.get(col_name) not in [None, "", []]:
            params[col_name] = value
            return f"{col_name_escaped} = :{col_name}"

        # 🔹 Suporte para UUID
        if "uuid" in col_type_str:
            params[col_name] =  str(value)
            return f"{col_name_escaped} = :{col_name}"

        # 🔹 Suporte para Booleanos
        if "boolean" in col_type_str or isinstance(col_type, Boolean):
            boolean_map = {"true": True, "1": True, "yes": True, "sim": True,
                           "false": False, "0": False, "no": False, "não": False}
            if value.lower() not in boolean_map:
                raise ValueError(f"Valor inválido para booleano na coluna '{col_name}'.")
            params[col_name] = boolean_map[value.lower()]
            return f"{col_name_escaped} = :{col_name}"

        # 🔹 Suporte para Datas/Timestamps
        is_date_type = any(t in col_type_str for t in ["date", "timestamp", "time"]) or isinstance(col_type, (Date, DateTime))
        is_number_type = any(t in col_type_str for t in ["numeric", "integer"]) or isinstance(col_type, Numeric)
        is_text_type = any(t in col_type_str for t in ["text", "char", "varchar"])

        def basic_op(field):
            op_map = {
                "=": "=",
                "!=": "!=",
                "<": "<",
                "<=": "<=",
                ">": ">",
                ">=": ">="
            }
            if operation in op_map:
                params[col_name] = float(value) if is_number_type else value
                return f"{field} {op_map[operation]} :{col_name}"
            elif operation == "Entre":
                if not value_otheir_between.strip():
                    raise ValueError(f"Valor final ausente para operação 'Entre' na coluna '{col_name}'.")
                val1 = float(value) if is_number_type else value
                val2 = float(value_otheir_between) if is_number_type else value_otheir_between
                params[f"{col_name}_min"] = val1
                params[f"{col_name}_max"] = val2
                return f"{field} BETWEEN :{col_name}_min AND :{col_name}_max"
            elif operation == "Contém" and (is_text_type or "json" in col_type_str or is_date_type):
                params[col_name] = f"%{value}%"
                return f"{field} LIKE :{col_name}"
            elif operation == "Não Contém" and (is_text_type or "json" in col_type_str or is_date_type):
                params[col_name] = f"%{value}%"
                return f"{field} NOT LIKE :{col_name}"
            elif operation == "Antes de" and is_date_type:
                params[col_name] = value
                return f"{field} < :{col_name}"
            elif operation == "Depois de" and is_date_type:
                params[col_name] = value
                return f"{field} > :{col_name}"
            else:
                raise ValueError(f"Operação '{operation}' não suportada para o tipo de dado da coluna '{col_name}'.")


        # 🔹 Conversões especiais
        if "json" in col_type_str:
            json_field = f"{col_name_escaped}::TEXT" if db_type_lower in ["postgresql", "postgres"] else f"CAST({col_name_escaped} AS TEXT)"
            return basic_op(json_field)

        if is_date_type:
            if db_type_lower in ["postgresql", "postgres"]:
                date_field = f"CAST({col_name_escaped} AS TEXT)"
            elif db_type_lower in ["mysql"]:
                date_field = f"CONVERT({col_name_escaped}, CHAR)"
            elif db_type_lower in ["mssl", "sql server"]:
                date_field = f"CONVERT(CHAR, {col_name_escaped}, 23)"  # Estilo 23 = 'YYYY-MM-DD'
            elif db_type_lower == "sqlite":
                date_field = f"{col_name_escaped} LIKE :{col_name}"  # No SQLite, colunas de data já são strings
            else:
                date_field = f"CAST({col_name_escaped} AS TEXT)" if db_type_lower in ["postgresql", "postgres"] else col_name_escaped
            return basic_op(date_field)

        if is_number_type:
            return basic_op(col_name_escaped)

        if is_text_type:
            return basic_op(col_name_escaped)

        raise TypeError(f"Tipo de coluna '{col_type}' não suportado para filtros.")

    except (ValueError, TypeError) as e:
        raise ValueError(f"Erro ao processar '{col_name}': {e}")
    



def pesquisar_in_db(engine, db_type, campo_primary_key, primary_key_value, table_name, selected_row_index, text, log_message):
    """Busca a chave primária no banco de dados se ela não estiver disponível no DataFrame."""
    try:
        with engine.connect() as conn:
            valid_db_types = ["postgres","postgresql", "sqlite", "mysql", "oracle", "mssql", "sql server"]
            db_type = db_type.lower().strip() if db_type else ""
            
            # Verificando se o tipo de banco é válido
            if not any(db in db_type for db in valid_db_types):
                log_message(f"⚠ Banco de dados `{db_type}` não suportado para esta operação.", level="error")
                return None

            # Consultas para cada banco
            queries = {
                "postgres": f'SELECT "{campo_primary_key}" FROM "{table_name}" LIMIT 1 OFFSET :offset_value',
                "postgresql":  f'SELECT "{campo_primary_key}" FROM "{table_name}" LIMIT 1 OFFSET :offset_value',
                "sqlite": f'SELECT "{campo_primary_key}" FROM "{table_name}" LIMIT 1 OFFSET :offset_value',
                "mysql": f"SELECT `{campo_primary_key}` FROM `{table_name}` LIMIT :offset_value, 1",
                "oracle": f'SELECT "{campo_primary_key}" FROM (SELECT {campo_primary_key}, ROWNUM AS rn FROM {table_name}) WHERE rn = :offset_value',
                "mssql": f"SELECT [{campo_primary_key}] FROM (SELECT [{campo_primary_key}], ROW_NUMBER() OVER (ORDER BY {campo_primary_key}) AS rn FROM [{table_name}]) AS subquery WHERE rn = :offset_value",
                "sql server": f"SELECT [{campo_primary_key}] FROM (SELECT [{campo_primary_key}], ROW_NUMBER() OVER (ORDER BY {campo_primary_key}) AS rn FROM [{table_name}]) AS subquery WHERE rn = :offset_value"
            }

            query = queries.get(db_type, None)
            if not query:
                log_message(f"⚠ Banco de dados `{db_type}` não suportado para esta operação.", level="error")
                return None

            # Executando a consulta
            result = conn.execute(text(query), {"offset_value": selected_row_index + 1}).fetchone()
            
            if result and result[0] is not None:
                primary_key_value = result[0].strip() if isinstance(result[0], str) else result[0]
                log_message(f"✅ Chave primária encontrada: {primary_key_value}")
                return primary_key_value
            else:
                log_message(f"❌ Chave primária não encontrada.", level="error")
                return None

    except Exception as e:
        log_message(f"❌ Erro ao buscar chave primária no banco: {e}", level="error")
        return None


    # 🔍 **Se ainda não encontrou, abortar**
    log_message(f"⚠ Não foi possível determinar a chave primária `{campo_primary_key}` para a linha {selected_row_index}.", level="error")
    return None  # 🔴 Retorno explícito
