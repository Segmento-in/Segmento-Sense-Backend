import pandas as pd
from urllib.parse import quote_plus

class MongoHandler:
    def __init__(self):
        try:
            import pymongo
            self.pymongo = pymongo
            print("✅ MongoDB Handler loaded.")
        except ImportError:
            self.pymongo = None
            print("❌ PyMongo not installed.")

    def fetch_data(self, host, port, db, user, pw, collection):
        if not self.pymongo:
            return pd.DataFrame()
        
        try:
            if user and pw:
                safe_user = quote_plus(user)
                safe_pw = quote_plus(pw)
                uri = f"mongodb://{safe_user}:{safe_pw}@{host}:{port}/"
            else:
                uri = f"mongodb://{host}:{port}/"
            
            client = self.pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            # Check connection
            client.server_info() 
            
            cursor = client[db][collection].find().limit(100)
            data = list(cursor)
            
            if not data:
                return pd.DataFrame()
            
            # Normalize ObjectIds to strings
            for d in data:
                if '_id' in d:
                    d['_id'] = str(d['_id'])
            
            return pd.json_normalize(data)
            
        except Exception as e:
            print(f"❌ Mongo Error: {e}")
            return pd.DataFrame()