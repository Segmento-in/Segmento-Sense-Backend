import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

class PostgresHandler:
    def __init__(self):
        print("✅ PostgreSQL Handler loaded.")

    def fetch_data(self, host, port, db, user, pw, table):
        """
        Connects to PostgreSQL and fetches the first 100 rows of a table.
        """
        try:
            safe_pw = quote_plus(pw)
            # SQLAlchemy connection string
            conn_str = f"postgresql://{user}:{safe_pw}@{host}:{port}/{db}"
            engine = create_engine(conn_str)
            
            query = f"SELECT * FROM {table} LIMIT 100"
            return pd.read_sql(query, engine)
        except Exception as e:
            print(f"❌ PostgreSQL Error: {e}")
            return pd.DataFrame()