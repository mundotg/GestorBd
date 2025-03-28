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
        print("textCom:", entry)
        return entry.get().strip()

    elif isinstance(entry,( tk.Checkbutton,ttk.Checkbutton)):
        var_name = entry.cget("variable")  # Obtém o nome da variável associada
        if var_name:
            try:
                var_widget = entry.master.nametowidget(var_name)
                print("checkbox:", str(var_widget.get()).strip())
                return str(var_widget.get()).strip()
            except Exception as e:
                print("Erro ao acessar variável do Checkbutton:", e)
                return ""

    elif isinstance(entry, tk.Text):
        print("textArea:", entry)
        return entry.get("1.0", tk.END).rstrip("\n").strip()

    print("nada:", entry)
    return ""
