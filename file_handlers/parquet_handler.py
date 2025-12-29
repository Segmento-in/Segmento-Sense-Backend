import io
import pandas as pd

class ParquetHandler:
    def __init__(self):
        self.available = False
        try:
            import pyarrow.parquet as pq
            self.available = True
            print("✅ Parquet Handler loaded.")
        except ImportError:
            print("❌ PyArrow not found. Please run: pip install pyarrow")

    def convert_to_dataframe(self, file_bytes: bytes) -> pd.DataFrame:
        """
        Reads Parquet bytes and converts them to a Pandas DataFrame.
        """
        if not self.available:
            return pd.DataFrame()

        try:
            return pd.read_parquet(io.BytesIO(file_bytes))
        except Exception as e:
            print(f"⚠️ Parquet Read Error: {e}")
            return pd.DataFrame()