import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

class MysqlHandler:
    def __init__(self):
        print("✅ MySQL Handler loaded.")

    def fetch_data(self, host, port, db, user, pw, table):
        """
        Connects to MySQL and fetches the first 100 rows of a table.
        """
        try:
            safe_pw = quote_plus(pw)
            # Uses mysql+pymysql driver
            conn_str = f"mysql+pymysql://{user}:{safe_pw}@{host}:{port}/{db}"
            engine = create_engine(conn_str)
            
            query = f"SELECT * FROM {table} LIMIT 100"
            return pd.read_sql(query, engine)
        except Exception as e:
            print(f"❌ MySQL Error: {e}")
            return pd.DataFrame()