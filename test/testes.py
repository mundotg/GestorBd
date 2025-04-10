import pandas as pd
from sqlalchemy import URL, create_engine
#DESKTOP-4UGL8JL\FRANCEMY
# Configuração do SQL Server
server = "localhost"
port = "1433"
database = "siga_intellectus"
username = "sa"
password = "Brasilangola@2310"
driver = "ODBC+Driver+17+for+SQL+Server"  # Verifique o driver instalado


# Criar a string de conexão ODBC
connection_string = f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;"


# Criar a URL de conexão para o SQLAlchemy
connection_url = URL.create(
   drivername= "mssql+pyodbc",
    username= username,
    password= password,
    host=server,
    port=port,
    query={"odbc_connect":connection_string}
)
print(connection_url)
print(connection_url)
# Criar o engine
engine = create_engine(connection_url)
# Criar a URL de conexão
""" conn_str = f"mssql+pyodbc://{username}:{password}@{server}:{port}/{database}?driver={driver}"

# Criar a engine SQLAlchemy
engine = create_engine(conn_str) """

# Testar a conexão
try:
    with engine.connect() as conn:
        print("✅ Conexão bem-sucedida!")
        query = "SELECT * FROM t_pais"
        df = pd.read_sql(query, engine)

        print(df.head())  # Exibir as primeiras linhas
        print(df.info())  # Exibir informações do DataFrame
except Exception as e:
    print("❌ Erro na conexão:", e)


