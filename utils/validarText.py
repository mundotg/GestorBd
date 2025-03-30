def validar_numero(text):
    """Permite apenas números inteiros ou decimais com ponto."""
    if text == "":
        return True  # Permite o campo vazio
    try:
        float(text)  # Tenta converter para float
        return True
    except ValueError:
        return False  # Bloqueia caracteres inválidos
def validar_numero_inteiro(text):
    """Permite apenas números inteiros ou decimais com ponto."""
    if text == "":
        return True  # Permite o campo vazio
    try:
        int(text)  # Tenta converter para float
        return True
    except ValueError:
        return False  # Bloqueia caracteres inválidos
def validar_numero_float(s, allow_float=False):
    if allow_float:
        return s.replace(".", "", 1).isdigit()
    return s.isdigit()

def _fetch_enum_values(self, columns,text,traceback):
    """Fetch enum values from the database if possible."""
    try:
        for col in columns:
            col_type = str(col["type"]).lower()
            col_name = col["name"]
            
            if "enum" in col_type or self.db_type in ("mysql", "mariadb", "sqlite", "sqlserver"):
                if self.db_type == "postgresql":
                    query = text(f"""
                        SELECT enum_range(NULL::{self.table_name}_{col_name}_enum)
                    """)
                
                elif self.db_type in ("mysql", "mariadb"):
                    query = text(f"""
                        SHOW COLUMNS FROM {self.table_name} LIKE '{col_name}'
                    """)
                
                elif self.db_type == "sqlserver":
                    query = text(f"""
                        SELECT COLUMN_NAME, CHECK_CLAUSE 
                        FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS 
                        WHERE CONSTRAINT_NAME = '{self.table_name}_{col_name}_chk'
                    """)
                
                elif self.db_type == "sqlite":
                    query = text(f"""
                        PRAGMA table_info({self.table_name})
                    """)
                    
                with self.engine.connect() as conn:
                    result = conn.execute(query).fetchall()
                    
                    if self.db_type == "postgresql" and result:
                        self.enum_values[col_name] = list(result[0])
                    
                    elif self.db_type in ("mysql", "mariadb") and result:
                        enum_values = result[0][1]
                        enum_values = enum_values.replace("enum(", "").replace(")", "").replace("'", "").split(",")
                        self.enum_values[col_name] = enum_values
                    
                    elif self.db_type == "sqlserver" and result:
                        check_clause = result[0][1]
                        self.enum_values[col_name] = [v.strip().replace("'", "") for v in check_clause.split("IN (")[1].replace(")", "").split(",")]
                    
                    elif self.db_type == "sqlite" and result:
                        # SQLite doesn't support ENUM, so using CHECK constraints
                        for row in result:
                            if row[1] == col_name and "CHECK" in row[5]:
                                values = row[5].split("IN (")[1].replace(")", "").replace("'", "").split(",")
                                self.enum_values[col_name] = [v.strip() for v in values]
    except Exception:
        self.log_message(f"Erro ao obter valores de enum: {traceback.format_exc()}", level="warning")

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

    elif db_type in ["mssql", "SQL Server"]:  # Microsoft SQL Server
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
        filtros.append(f"{campo_chave} > {valor_ultima_linha}")  # Evita repetir registros

    if filtros:
        query_string += f" WHERE {' AND '.join(filtros)}"

    # Ordenação e Limite
    if db_type in ["mysql", "sqlite", "postgresql"]:
        query_string += f" ORDER BY {campo_chave} ASC LIMIT {max_rows}"

    elif db_type in ["mssql", "SQL Server"]:
        query_string += f" ORDER BY {campo_chave} ASC OFFSET 0 ROWS FETCH NEXT {max_rows} ROWS ONLY"

    elif db_type == "oracle":
        query_string = f"""
            SELECT * FROM (
                SELECT a.*, ROWNUM rnum FROM ({query_string} ORDER BY {campo_chave} ASC) a 
                WHERE ROWNUM <= {max_rows}
            ) WHERE rnum > {valor_ultima_linha if valor_ultima_linha else 0}
        """

    return query_string

