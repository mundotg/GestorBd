from datetime import datetime
import json
import traceback
import uuid
from sqlalchemy import text

from config.salavarInfoAllColumn import get_columns_by_table, save_columns_to_file

def validar_numero(valor, allow_float=False):
    if valor == "":
        return True 
    try:
        if allow_float:
            float(valor)  # Permite números decimais
        else:
            int(valor)  # Apenas inteiros
        return True
    except ValueError:
        return False


def validar_numero_float(s, allow_float=False):
    if allow_float:
        return s.replace(".", "", 1).isdigit()
    return s.isdigit()

def _fetch_enum_values(self, columns, text, traceback):
    """Obtém valores ENUM do banco de dados, se disponíveis."""
    
    try:
        self.enum_values = get_columns_by_table(self.db_type+self.database_name+self.table_name, "tables_columns_enum.pkl", log_message=self.log_message)
        if not hasattr(self, "enum_values") or self.enum_values is None:
            self.enum_values = {}
        else:
             self.log_message(f"Valores ENUM obtidos caregado do ficheiro: {self.enum_values}", level="info")
             return
        # Verifica se a tabela contém colunas ENUM
        for col in columns:
            
            col_name = col["name"]
            col_type = str(col["type"]).lower()
            query = None
            # print(f"col_name={col_name} col_type={col_type} self.table_name={self.table_name} self.db_type={self.db_type}")
            if self.db_type == "postgresql":
                query = text(f"""
                    SELECT e.enumlabel 
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    WHERE t.typname = '{col_name}';
                """)

            elif self.db_type in ("mysql", "mariadb"):
                query = text(f"SHOW COLUMNS FROM {self.table_name} LIKE '{col_name}'")

            elif self.db_type in ("mssql", "sql server"):
                query = text(f"""
                    SELECT definition 
                    FROM sys.check_constraints con
                    JOIN sys.columns col ON con.parent_object_id = col.object_id
                    JOIN sys.tables tab ON col.object_id = tab.object_id
                    WHERE tab.name = '{self.table_name}' 
                    AND col.name = '{col_name}' 
                    AND con.definition LIKE 'IN (%)';
                """)

            elif self.db_type == "sqlite":
                query = text(f"PRAGMA table_info({self.table_name})")
            elif self.db_type == "oracle":
                # Verifica CHECK CONSTRAINTS
                query = text(f"""
                    SELECT con.search_condition 
                    FROM user_constraints con
                    JOIN user_cons_columns col ON con.constraint_name = col.constraint_name
                    WHERE con.constraint_type = 'C'
                    AND col.table_name = '{self.table_name.upper()}'
                    AND col.column_name = '{col_name.upper()}';
                """)

            if query is not None:
                with self.engine.connect() as conn:
                    result = conn.execute(query).fetchall()
                    if result:
                        if self.db_type == "postgresql":
                            self.enum_values[col_name] = [row[0] for row in result]

                        elif self.db_type in ("mysql", "mariadb"):
                            enum_text = result[0][1]
                            if "enum(" in enum_text:
                                self.enum_values[col_name] = enum_text.replace("enum(", "").replace(")", "").replace("'", "").split(",")

                        elif self.db_type in ("mssql", "sql server"):
                            check_clause = result[0][0]
                            if "IN (" in check_clause:
                                self.enum_values[col_name] = [v.strip().replace("'", "") for v in check_clause.split("IN (")[1].replace(")", "").split(",")]

                        elif self.db_type == "sqlite":
                            for row in result:
                                if row[1] == col_name and "CHECK" in row[5]:
                                    values = row[5].split("IN (")[1].replace(")", "").replace("'", "").split(",")
                                    self.enum_values[col_name] = [v.strip() for v in values]
                        elif self.db_type == "oracle":
                            check_clause = result[0]
                            if "IN (" in check_clause:
                                self.enum_values[col_name] = [
                                    v.strip().replace("'", "") for v in check_clause.split("IN (")[1].replace(")", "").split(",")
                                ]
        if save_columns_to_file({self.db_type+self.database_name+self.table_name: self.enum_values}, "tables_columns_enum.pkl", log_message=self.log_message):
            self.log_message(f"Valores ENUM obtidos: {self.enum_values}", level="info")

    except Exception as e:
        self.log_message(f"Erro ao obter valores de enum:{e} {traceback.format_exc()}", level="warning")

def convert_values(updated_values,np):
    """Converte valores para tipos compatíveis com bancos de dados."""
    for col, value in updated_values.items():
        if isinstance(value, (np.integer, np.int_)):
            updated_values[col] = int(value)
        elif isinstance(value, (np.floating, np.float_)):
            updated_values[col] = float(value)
        elif isinstance(value, np.bool_):
            updated_values[col] = bool(value)
        elif isinstance(value, (np.ndarray, list)):
            updated_values[col] = str(value)
    return updated_values


def _map_column_type(col_type: str):
    """Mapeia o tipo da coluna para a função de conversão correspondente."""
    col_type = col_type.lower()

    if any(t in col_type for t in [
        "int", "integer", "smallint", "bigint", "tinyint", "serial", "bigserial", "number"
    ]):
        return int
   
    if any(t in col_type for t in [
        "float", "real", "double", "double precision", "decimal", "numeric"
    ]): 
        return float
    
    elif any(t in col_type for t in ["bool", "bit", "boolean"]):
        return lambda x: x.lower() in ("true", "1", "yes", "t", "on") if x is not None else None  # Converte para booleano
    
    elif "timestamp" in col_type:
        return lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S") if x else None  # Converte para datetime
    
    elif "uuid" in col_type:
        return lambda x: uuid.UUID(x) if x else None  # Converte para UUID, tratando nulos
    
    elif any(t in col_type for t in ["json", "jsonb"]):
        return lambda x: json.loads(x) if isinstance(x, str) and x.strip() else None  # Converte para JSON
    
    elif any(t in col_type for t in ["blob", "binary"]):
        return lambda x: bytes(x, "utf-8") if x is not None else None  # Converte para binário
    
    else:
        return str  # Se não for reconhecido, trata como string

# 75a9c7cd-0a07-4798-aac0-c771b7a51b03
def _convert_column_type(column_types, updated_values):
    # """Converte os valores com base no mapeamento de tipos."""
    # print("Column types:", column_types)
    # print("Updated values:", updated_values)
    converted = updated_values.copy()
    for col, value in updated_values.items():
        if value:  # Apenas processa se o valor existir
            if column_types[col] == uuid.UUID:
                try:
                    converted[col] = uuid.UUID(str(value))  # Garante um UUID válido
                except ValueError:
                    raise ValueError(f"O valor '{value}' em '{col}' não é um UUID válido!")
            elif column_types[col] == json.loads:  # Caso seja JSON
                try:
                    converted[col] = json.loads(value) if value.strip() else {}  # Converte apenas se não estiver vazio
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Erro ao converter {col}: {e}")
                    converted[col] = None  # Evita crash e mantém um valor válido
           
            else:
                converted[col] = column_types[col](value)  # Conversão normal
        else:
            converted[col] = None  # Mantém `None` para valores vazios
    return converted

def _convert_column_type_for_string(column_types, updated_values):
    """Converte os valores com base no mapeamento de tipos e retorna como string ou 'NULL'."""
    converted = updated_values.copy()
    
    for col, value in updated_values.items():

        if value is not None and value != "":
            try:
                if column_types[col] in [int, float, bool]:  # Mantém números e booleanos sem aspas
                    converted[col] = f"{column_types[col](value)}"
                else:
                    converted[col] = f"'{column_types[col](value)}'"
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                print(f"Erro ao converter {col}: {e}")
                converted[col] = "NULL"  # Evita crash e mantém um valor válido
        else:
            converted[col] = "NULL"  # Mantém `NULL` sem aspas para valores vazios
    
    return converted

def _convert_column_type_for_string_one(column_types,col, value):
    """Converte os valores com base no mapeamento de tipos e retorna como string ou 'NULL'."""
    if value is not None and value != "":
        try:
            if column_types[col] in [int, float, bool]:  # Mantém números e booleanos sem aspas
                return f"{column_types[col](value)}"
            else:
                return f"'{column_types[col](value)}'"
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            print(f"Erro ao converter {col}: {e}")
            return "NULL"  # Evita crash e mantém um valor válido
    else:
        return "NULL"  # Mantém `NULL` sem aspas para valores vazios




def get_valor_idependente_entry(entry, tk, ttk):
    """Retorna o valor de um widget, independente do seu tipo."""
    
    if isinstance(entry, (tk.Entry, ttk.Combobox, ttk.Spinbox)):
        return entry.get().strip()

    elif isinstance(entry,( tk.Checkbutton,ttk.Checkbutton)):
        var_name = entry.cget("variable")  # Obtém o nome da variável associada
        if var_name:
            try:
                var_widget = entry.master.nametowidget(var_name)
                return str(var_widget.get()).strip()
            except Exception as e:
                print("Erro ao acessar variável do Checkbutton:", e)
                return ""

    elif isinstance(entry, tk.Text):
        return entry.get("1.0", tk.END).rstrip("\n").strip()
    print("Não entrou em nada:", entry, "Tipo:", type(entry))
    if entry is None:
        print("é none")
    return ""
def get_query_string(base_query, filters=None, max_rows=1000, db_type="mysql", offset=None) -> str:
    """
    Gera uma query SQL ajustada para diferentes bancos de dados, incluindo filtros, limite e paginação.
    
    Args:
        base_query (str): Query base (ex: 'SELECT * FROM tabela').
        filters (list, optional): Lista de condições de filtro. Exemplo: ["idade > 30", "cidade = 'SP'"].
        max_rows (int): Número máximo de linhas a serem retornadas.
        db_type (str): Tipo de banco de dados ('mysql', 'sqlite', 'postgresql', 'mssql', 'oracle').
        offset (int, optional): Número de linhas a serem ignoradas para paginação.

    Returns:
        str: Query SQL final formatada.
    """
    query_string = base_query

    # Adiciona filtros, se houver
    if filters:
        query_string += f" WHERE {' AND '.join(filters)}"

    # Ajusta o limite e offset conforme o tipo de banco de dados
    if db_type in ["mysql", "sqlite", "postgresql"]:
        query_string += f" LIMIT {max_rows}"
        if offset is not None:
            query_string += f" OFFSET {offset}"

    elif db_type in ["mssql", "sql server"]:  # Microsoft SQL Server
        # SQL Server usa uma sintaxe diferente para LIMIT e OFFSET
        query_string = f"{query_string} ORDER BY (SELECT NULL) OFFSET {offset or 0} ROWS FETCH NEXT {max_rows} ROWS ONLY"

    elif db_type == "oracle":
        if offset is not None:
            query_string = f"""
                SELECT * FROM (
                    SELECT a.*, ROWNUM rnum FROM ({query_string}) a 
                    WHERE ROWNUM <= {offset + max_rows}
                ) WHERE rnum > {offset}
            """
        else:
            query_string = f"SELECT * FROM ({query_string}) WHERE ROWNUM <= {max_rows}"

    return query_string

def quote_identifier(db_type, identifier):
    if db_type in ['postgresql', 'oracle']:
        return f'"{identifier}"'  # Aspas duplas para PostgreSQL e Oracle
    elif db_type == 'mssql' or db_type == 'sql server':
        return f"[{identifier}]"  # Colchetes para MSSQL
    elif db_type == 'mysql':
        return f"`{identifier}`"  # Backticks no MySQL
    else:
        return identifier  # Padrão sem aspas

def get_query_string_threads(base_query, filters=None, max_rows=1000, db_type="mysql", campo_chave="id", valor_ultima_linha=None) -> str:
    """
    Gera uma query SQL ajustada para diferentes bancos de dados, incluindo filtros, limite e paginação sem OFFSET.
    
    Args:
        base_query (str): Query base (ex: 'SELECT * FROM tabela').
        filters (list, optional): Lista de condições de filtro. Exemplo: ["idade > 30", "cidade = 'SP'"].
        max_rows (int): Número máximo de linhas a serem retornadas.
        db_type (str): Tipo de banco de dados ('mysql', 'sqlite', 'postgresql', 'mssql', 'oracle').
        campo_chave (str): Nome do campo utilizado para paginação (ex: 'id').
        valor_ultima_linha (int, optional): Último valor do campo chave carregado.

    Returns:
        str: Query SQL final formatada.
    """
    query_string = base_query

    # Adiciona filtros, se houver
    filtros = filters[:] if filters else []  # Evita modificar a lista original
    if valor_ultima_linha is not None:
        if isinstance(valor_ultima_linha, (int, float)):  # Se for número, não precisa de aspas
            filtros.append(f"{campo_chave} > {valor_ultima_linha}")
        else:  # Se for string ou data, precisa de aspas simples
            filtros.append(f"{campo_chave} > '{valor_ultima_linha}'") 

    # Aplicando filtros na query
    if filters:
        # Para outros bancos de dados, não é necessário o uso de aspas duplas
        query_string += f" WHERE {' AND '.join(filters)}"

    # Ordenação e Limite
    if db_type in ["mysql", "sqlite", "postgresql"]:
        query_string += f" ORDER BY {campo_chave} ASC LIMIT {max_rows}"

    elif db_type in ["mssql", "sql server"]:
        query_string += f" ORDER BY {campo_chave} ASC OFFSET 0 ROWS FETCH NEXT {max_rows} ROWS ONLY"

    elif db_type == "oracle":
        inner_query = f"{query_string} ORDER BY {campo_chave} ASC"
        query_string = f"""
            SELECT * FROM (
                SELECT a.*, ROWNUM rnum FROM ({inner_query}) a 
                WHERE ROWNUM <= {max_rows}
            ) WHERE rnum > {valor_ultima_linha if valor_ultima_linha else 0}
        """

    return query_string


def _is_system_field(col_name: str, col_type: str, columns: list, db_type: str, table_name: str, engine, database_name, log_message) -> bool:
    """Determina se um campo é do sistema e deve ser ignorado."""
    
    table_key = db_type + database_name + table_name
    
    try:
        result = get_columns_by_table(table_key, ficheiro_name="tables_columns_system_field.pkl", log_message=log_message)
        if result is not None:
            log_message("Resultado do cache: " + str(result))
            return result

        def cache_result(value: bool):
            save_columns_to_file({table_key: value}, ficheiro_name="tables_columns_system_field.pkl", log_message=log_message)

        # Palavras-chave para identificar colunas auto-incrementáveis
        auto_increment_keywords = {
            "serial", "bigserial", "identity", "autoincrement", "uuid",
            "integer primary key", "auto_increment", "integer primary key autoincrement", 
            "sequence", "smallserial",
        }

        # Campos do sistema que sempre devem ser ignorados
        system_field_names = {"id", "created_at", "updated_at", "created_by", "updated_by"}

        # Normaliza o nome da coluna e o tipo
        col_name_lower = col_name.lower().strip()
        col_type_lower = col_type.lower().strip() if col_type else ""

        # Verifica se é um campo de sistema e auto-incrementável
        if col_name_lower in system_field_names and any(keyword in col_type_lower for keyword in auto_increment_keywords):
            cache_result(True)
            return True

        # Verificações por tipo de banco de dados
        if db_type == "sql server" and col_type_lower in {"smallint", "int", "bigint"}:
            with engine.connect() as conn:
                query = text("""
                    SELECT COLUMNPROPERTY(OBJECT_ID(:table_name), :col_name, 'IsIdentity') AS IsIdentity
                """)
                try:
                    result = conn.execute(query, {"table_name": table_name, "col_name": col_name}).fetchone()
                    cache_result(bool(result and result[0] == 1))
                    return bool(result and result[0] == 1)
                except Exception as e:
                    log_message(f"Erro ao consultar SQL Server: {e}")
                    return False

        elif db_type == "postgresql" and col_type_lower in {"smallint", "int", "bigint"}:
            with engine.connect() as conn:
                query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = :table_name AND is_identity = 'YES'
                """)
                try:
                    result = conn.execute(query, {"table_name": table_name}).fetchall()
                    cache_result(bool(result))
                    return bool(result)
                except Exception as e:
                    log_message(f"Erro ao consultar PostgreSQL: {e}")
                    return False

        elif db_type == "oracle" and col_type_lower in {"number", "int", "bigint"}:
            with engine.connect() as conn:
                query = text("""
                    SELECT column_name 
                    FROM all_tab_columns 
                    WHERE table_name = :table_name AND identity_column = 'YES'
                """)
                try:
                    result = conn.execute(query, {"table_name": table_name.upper()}).fetchall()
                    cache_result(bool(result))
                    return bool(result)
                except Exception as e:
                    log_message(f"Erro ao consultar Oracle: {e}")
                    return False

        elif db_type == "mysql" and col_type_lower in {"tinyint", "smallint", "mediumint", "int", "bigint"}:
            with engine.connect() as conn:
                query = text("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :table_name AND EXTRA LIKE '%auto_increment%'
                """)
                try:
                    result = conn.execute(query, {"table_name": table_name}).fetchall()
                    cache_result(bool(result))
                    return bool(result)
                except Exception as e:
                    log_message(f"Erro ao consultar MySQL: {e}")
                    return False

        # Se não for encontrado, salva o resultado como False
        cache_result(False)
        return False

    except Exception as e:
        log_message(f"Erro geral na função _is_system_field: {e} {traceback.format_exc()}")
        return False

def _get_placeholder(db_type, col_name, index):
    """Retorna o placeholder correto baseado no banco de dados."""
    if db_type in ["mysql", "mariadb"]:
        return "%s"  # Placeholder padrão do MySQL/MariaDB
    elif db_type in ["sqlserver", "sql server"]:
        return "?"  # Placeholder do SQL Server com PyODBC
    elif db_type == "oracle":
        return f":{index + 1}"  # Placeholders numerados no Oracle (:1, :2, :3)
    elif db_type in ["postgresql", "sqlite"]:
        return "?"  # Placeholder padrão do PostgreSQL/SQLite (psycopg2 e sqlite3)
    else:
        raise ValueError(f"Banco de dados '{db_type}' não suportado.")
    
