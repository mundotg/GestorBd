from typing import Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from utils.logger import logger

class DatabaseManager:
    """Gerencia a conexão com diferentes bancos de dados usando SQLAlchemy"""
   
    DB_URIS = {
        "MySQL": "mysql+pymysql://{user}:{password}@{host}:{port}/{database}",
        "PostgreSQL": "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}?sslmode=require",
        "pg": "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
        "SQLite": "sqlite:///{database}",
        "SQL Server": "mssql+pyodbc:///?odbc_connect=DRIVER={{ODBC+Driver+17+for+SQL+Server}};SERVER={host},{port};DATABASE={database};UID={user};PWD={password};TrustServerCertificate=yes",
        "Oracle": "oracle+cx_oracle://{user}:{password}@{host}:{port}/?service_name={service}",
        "MariaDB": "mariadb+mariadbconnector://{user}:{password}@{host}:{port}/{database}",
    }

    @staticmethod
    def get_engine(db_type: str, config: Dict[str, Any]):
        """Cria e retorna um engine SQLAlchemy"""
        if db_type not in DatabaseManager.DB_URIS:
            logger.error(f"Tipo de banco de dados não suportado: {db_type}")    
            raise ValueError(f"Tipo de banco de dados não suportado: {db_type}")
        try:
            uri = DatabaseManager.DB_URIS[db_type].format(
                user=config.get("user", "root"),
                password=config.get("password", ""),
                host=config.get("host", "localhost"),
                port=config.get("port", DatabaseUtils.get_default_port(db_type)),
                database=config.get("database", ""),
                service=config.get("service", "xe")
            )
            logger.debug(f"Conectando a URI: {uri}")  # Debug log for the URI (be cautious with sensitive data)
            return create_engine(uri)
        except Exception as e:
            logger.error(f"Erro ao criar engine para {db_type}: {e}")
            raise

    @staticmethod
    def connect(db_type: str, config: Dict[str, Any]):
        """Estabelece uma conexão SQLAlchemy com o banco de dados e retorna uma sessão e o engine."""
        try:
            engine = DatabaseManager.get_engine(db_type, config)  # Obtém o engine
            Session = sessionmaker(bind=engine)
            session = Session()  # Cria uma sessão

            # Testa a conexão verificando se o banco responde
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))  
                logger.info(f"✅ Conexão estabelecida com sucesso para {db_type}.")
            return session, engine
        except Exception as e:
            errorTxt = str(e)
            logger.error(f"❌ Erro ao conectar ao banco {db_type}: {errorTxt}")
            if db_type == "PostgreSQL":
                if "SSL" in errorTxt:
                    return DatabaseManager.connect("pg",config)
            raise  # Re-raise the error to propagate the issue

class DatabaseUtils:
    """Classe auxiliar para obter informações sobre bancos de dados"""
    
    DEFAULT_PORTS = {
        "MySQL": 3306,
        "PostgreSQL": 5432,
        "SQLite": 0,  # Não aplicável
        "SQL Server": 1433,
        "Oracle": 1521,
        "MariaDB": 3306,
    }

    @staticmethod
    def test_connection(db_type: str, config: Dict[str, Any]) -> bool:
        """Testa a conectividade com o banco de dados fornecido."""
        try:
            session, engine = DatabaseManager.connect(db_type, config)
            # Testa a conexão
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))  
            session.close()  # Fecha corretamente
            logger.info(f"✅ Conexão bem-sucedida com {db_type}.")
            return True
        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao banco {db_type}: {e}")
            return False

    @staticmethod
    def get_default_port(db_type: str) -> int:
        """Retorna a porta padrão para o banco de dados especificado"""
        return DatabaseUtils.DEFAULT_PORTS.get(db_type, 0)
