import json
import pandas as pd
import io

class JsonHandler:
    def __init__(self):
        print("✅ JSON Handler loaded.")

    def read_file(self, file_obj) -> pd.DataFrame:
        """
        Reads a JSON file object (or Streamlit UploadedFile) and flattens it.
        """
        try:
            # Handle Streamlit UploadedFile (bytes) vs standard file path
            if hasattr(file_obj, "getvalue"):
                content = file_obj.getvalue()
                data = json.loads(content.decode('utf-8'))
            else:
                data = json.load(file_obj)
            
            # Recursive function to flatten nested JSONs
            def flatten(x, name=''):
                if type(x) is dict:
                    out = {}
                    for a in x: out.update(flatten(x[a], name + a + '_'))
                    return out
                elif type(x) is list:
                    return {f"{name}list": str(x)}
                else: return {name[:-1]: x}
            
            # Normalize to DataFrame
            if isinstance(data, list): 
                return pd.DataFrame([flatten(x) for x in data])
            
            return pd.DataFrame([flatten(data)])

        except Exception as e:
            print(f"❌ JSON Read Error: {e}")
            return pd.DataFrame()