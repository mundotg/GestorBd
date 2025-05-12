from typing import Dict
import pandas as pd
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from config.salavarInfoAllColumn import (get_columns_by_table, save_columns_to_file)
from typing import Dict

from utils.validarText import convert_values

def _get_foreign_keys(self) -> Dict[str, str]:
    """Obtém as chaves estrangeiras da tabela usando o SQLAlchemy Inspector."""
    # Tenta obter os dados do cache
    foreign_keys = get_columns_by_table(
        self.table_name,
        "tables_columns_foreign_key_relationship.pkl",
        log_message=self.log_message
    )
    if foreign_keys:
        return foreign_keys

    inspector = inspect(self.engine)
    foreign_keys: Dict[str, str] = {}

    # Coleta as chaves estrangeiras diretamente do banco
    for fk in inspector.get_foreign_keys(self.table_name):
        referred_table = fk.get('referred_table')
        for column in fk.get('constrained_columns', []):
            foreign_keys[column] = referred_table

    # Salva em cache se encontrou chaves estrangeiras
    if foreign_keys:
        saved = save_columns_to_file(
            {self.table_name: foreign_keys},
            "tables_columns_foreign_key_relationship.pkl",
            log_message=self.log_message
        )
        if saved:
            self.log_message("Chaves estrangeiras salvas com sucesso.", "info")

    return foreign_keys

def _get_foreign_keys2(self) -> Dict[str, Dict[str, str]]:
    """
    Obtém as chaves estrangeiras de uma ou mais tabelas usando o SQLAlchemy Inspector.
    Suporta uma única tabela (str) ou múltiplas tabelas (list[str]).
    
    Retorna:
        Dict[str, Dict[str, str]]: Um dicionário onde a chave é o nome da tabela,
        e o valor é outro dicionário com {coluna: tabela_referenciada}.
    """
    try:
        inspector = inspect(self.engine)

        # Normaliza para lista de tabelas
        table_names = [self.table_name] if isinstance(self.table_name, str) else self.table_name

        # Dicionário para armazenar todas as chaves estrangeiras encontradas
        all_foreign_keys: Dict[str, Dict[str, str]] = {}

        # Tentando carregar os dados do cache para as chaves estrangeiras
        name_tabela = "".join(table_names)
        print(f"Nome da tabela: {self.table_name}")
        foreign_keys_cached = get_columns_by_table(name_tabela, "tables_columns_foreign_key_relationship.pkl", log_message=self.log_message)
        if foreign_keys_cached:
            return foreign_keys_cached
        
        # Itera sobre todas as tabelas fornecidas
        for table in table_names:
            foreign_keys: Dict[str, str] = {}

            # Verifica se há cache para a tabela atual
            foreign_keys_in_cached = get_columns_by_table(table, "tables_columns_foreign_key_relationship.pkl", log_message=self.log_message)

            # Obtém as colunas existentes na tabela
            existing_columns = {col['name'] for col in self.column_info}
            
            # Se já houver chaves estrangeiras em cache, faz a comparação com as colunas existentes
            if foreign_keys_in_cached:
                for column, referred_table in foreign_keys_in_cached.items():
                    if column in existing_columns:
                        foreign_keys[column] = referred_table

            # Verifica as chaves estrangeiras usando o SQLAlchemy Inspector
            try:
                for fk in inspector.get_foreign_keys(table):
                    referred_table = fk.get('referred_table')

                    # Itera sobre as colunas e trata a possibilidade de alias (tabela.coluna)
                    for column in fk.get('constrained_columns', []):
                        if column in existing_columns:  # Adiciona apenas se a coluna existir na tabela
                            # Caso a coluna esteja no formato "tabela.coluna", separamos o nome da tabela
                            table_name, column_name = (column.split('.', 1) if '.' in column else (None, column))
                            foreign_keys[column_name] = referred_table  # Armazena o nome real da coluna

            except SQLAlchemyError as e:
                self.log_message(f"Erro ao obter chaves estrangeiras para a tabela {table}: {str(e)}", "error")
                continue  # Continua para a próxima tabela, se houver erro

            # Se encontrou chaves estrangeiras, armazena no dicionário geral
            if foreign_keys:
                all_foreign_keys[table] = foreign_keys

        # Se encontrou chaves estrangeiras, salva em cache
        if all_foreign_keys:
            saved = save_columns_to_file(all_foreign_keys, "tables_columns_foreign_key_relationship.pkl", log_message=self.log_message)
            if saved:
                self.log_message("Chaves estrangeiras salvas com sucesso.", "info")

        return all_foreign_keys

    except SQLAlchemyError as e:
        self.log_message(f"Erro ao obter chaves estrangeiras: {str(e)}", "error")
        return {}  # Retorna um dicionário vazio em caso de erro
    except Exception as e:
        self.log_message(f"Erro inesperado ao obter chaves estrangeiras: {str(e)}", "error")
        return {}  # Retorna um dicionário vazio em caso de erro inesperado



def _tabela_existe(self, tabela_referenciada):
    """
    Verifica se a tabela existe no banco de dados.
    """
    inspector = inspect(self.engine)
    if tabela_referenciada not in inspector.get_table_names():
        self.log_message(f"Tabela '{tabela_referenciada}' não encontrada no banco de dados", level="error")
        return False
    return True


def _obter_campo_primary_key(self, tabela_referenciada):
    """
    Retorna o nome do campo de chave primária para a tabela especificada.
    """
    inspector = inspect(self.engine)
    pk_columns = inspector.get_pk_constraint(tabela_referenciada).get('constrained_columns', [])
    
    if not pk_columns:
        self.log_message(f"Chave primária não encontrada para a tabela '{tabela_referenciada}'", level="warning")
        return 'id'  # Usa o campo fornecido ou 'id' como padrão
    
    return pk_columns[0]  # Retorna a primeira coluna da PK

def _preparar_consulta(self, tabela_referenciada, campo_primary_key,valor_chave):
    """
    Prepara a consulta para o banco de dados, dependendo do tipo de banco.
    Se a consulta é apenas para uma chave estrangeira, não precisa de LIMIT.
    """
    from sqlalchemy import text
    valor_sql = convert_values(valor_chave)
    print(f"Valor chave: {valor_sql}")
    # Ajuste para bancos que não precisam de LIMIT
    if self.db_type in ['mysql', 'sqlite']:
        query = text(f"SELECT * FROM `{tabela_referenciada}` WHERE `{campo_primary_key}` = :record_id")
        params = {"record_id": valor_sql}
    elif self.db_type == 'postgresql':
        query = text(f'SELECT * FROM "{tabela_referenciada}" WHERE "{campo_primary_key}" = :record_id')
        params = {"record_id": valor_sql}
    elif self.db_type == 'oracle':
        query = text(f'SELECT * FROM "{tabela_referenciada}" WHERE "{campo_primary_key}" = :record_id')
        params = {"record_id": valor_sql}
    elif self.db_type in ['mssql', 'sql server']:
        query = text(f"SELECT * FROM [{tabela_referenciada}] WHERE [{campo_primary_key}] = :record_id")
        params = {"record_id": valor_sql}
    else:
        raise ValueError(f"Tipo de banco de dados '{valor_chave}' não suportado")

    return query, params




def _executar_consulta(self, query, params, tabela_referenciada, campo_primary_key):
    """
    Executa a consulta e processa os resultados.
    """
    try:
        # Exibe a consulta e os parâmetros de debug
        self.log_message(f"Executando consulta: {query} com parâmetros: {params}", level="debug")
        print(f"parâmetros: {params}")
        
        with self.engine.connect() as conn:
            # Executa a consulta
            result = conn.execute(query, params)
            
            # Verifique o número de linhas retornadas
            rows = result.fetchall()
            self.log_message(f"Número de linhas retornadas: {len(rows)}", level="debug")
            
            # Cria um DataFrame a partir dos resultados
            df = pd.DataFrame(rows)
            
            # Se o DataFrame estiver vazio, registre uma mensagem de debug
            if df.empty:
                self.log_message(f"Nenhum registro encontrado na tabela '{tabela_referenciada}' com {campo_primary_key}={self.record_id}", level="info")
                return None, None
            
            # Exibe o DataFrame de debug
            self.log_message(f"DataFrame obtido: {df.head()}", level="debug")
            
            # Tenta definir as colunas com as chaves do resultado
            df.columns = result.keys()  # Definir os nomes das colunas
            
            return conn, df
    except Exception as e:
        # Em caso de erro, loga o erro completo
        self.log_message(f"Erro ao executar a consulta: {str(e)}", level="error")
        raise

        
        
        


def _obter_column_types(self, tabela_referenciada):
    """
    Obtém os tipos de coluna da tabela relacionada.
    """
    columns = get_columns_by_table(f'{self.db_type}{self.database_name}{tabela_referenciada}', "tables_columns_data.pkl", log_message=self.log_message)
    if not columns:
        inspector = inspect(self.engine)
        columns = inspector.get_columns(tabela_referenciada, schema=None)
        for column in columns:
            column['table'] = self.table_name
        save_columns_to_file({f'{self.db_type}{self.database_name}{tabela_referenciada}': columns}, "tables_columns_data.pkl", log_message=self.log_message)
    return columns



def _obter_enum_values(self, conn, tabela_referenciada):
    """
    Obtém os valores de enumeração de uma tabela no PostgreSQL.
    """
    enum_values = {}
    if self.db_type == 'postgresql':
        from sqlalchemy import text
        enum_query = text("""
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typname = :enum_type
        """)
        enum_params = {"enum_type": "nome_do_tipo_enum"}  # Substitua pelo nome do tipo ENUM desejado
        enum_result = conn.execute(enum_query, enum_params)
        enum_values = {row['enumlabel'] for row in enum_result.fetchall()}
    return enum_values

