import os
import pickle

def save_columns_to_file(columns_data, ficheiro_name="tables_columns_data.pkl", log_message=None):
    """Salvar as colunas no arquivo usando Pickle (mais rápido e leve)."""
    try:
        with open(ficheiro_name, "wb") as f:
            pickle.dump(columns_data, f)
        return True
    except Exception as e:
        if log_message:
            log_message(f"Erro ao salvar colunas no arquivo: {e}", level="error")
    return False

def load_columns_from_file(ficheiro_name="tables_columns_data.pkl", log_message=None):
    """Carregar as colunas de um arquivo Pickle."""
    if os.path.exists(ficheiro_name):
        try:
            with open(ficheiro_name, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            if log_message:
                log_message(f"Erro ao carregar colunas do arquivo: {e}", level="error")
    else:
        if log_message:
            log_message(f"Arquivo {ficheiro_name} não encontrado.", level="warning")
    return None


def get_columns_by_table(table_name, ficheiro_name="tables_columns_data.pkl", log_message=None):
    """Retornar as colunas de uma tabela específica do arquivo Pickle."""
    if not os.path.exists(ficheiro_name):
        if log_message:
            log_message(f"Arquivo {ficheiro_name} não encontrado.", level="warning")
        return None

    try:
        with open(ficheiro_name, "rb") as f:
            data = pickle.load(f)  # Carrega todo o dicionário de tabelas
            
            if table_name in data:
                return data[table_name]  # Retorna as colunas da tabela encontrada
            else:
                if log_message:
                    log_message(f"Tabela {table_name} não encontrada no arquivo.", level="warning")
                return None  # Retorna None se a tabela não existir
    except Exception as e:
        if log_message:
            log_message(f"Erro ao ler o arquivo Pickle: {e}", level="error")
    return None

# Exemplo de uso:

if __name__ == "__main__":
    jsonm = {
    "tabela1": [
        {"name": "coluna1", "type": "int"},
        {"name": "coluna2", "type": "string"}
    ],
    "tabela2": [
        {"name": "coluna1", "type": "boolean"},
        {"name": "coluna2", "type": "float"}
    ]
    }

        # Salvar os dados usando Pickle
    save_columns_to_file(jsonm, "tables_columns_data.pkl", log_message=lambda m, level: print(f"{level}: {m}"))

    # Buscar as colunas da tabela "tabela1"
    columns = get_columns_by_table("tabela1", "tables_columns_data.pkl", log_message=lambda m, level: print(f"{level}: {m}"))

    if columns:
        print(f"Colunas da tabela: {columns}")
    else:
        print("Tabela não encontrada.")