import re
import json
import pandas as pd
import fitz  # PyMuPDF
import nltk
import io
import os
import pickle
import base64
from typing import Dict, List, Any
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from bs4 import BeautifulSoup 

# --- IMPORT CLASSIFIERS ---
from classifier_manager.spacy_model import PiiSpacyAnalyzer
from classifier_manager.presidio_model import PiiPresidioAnalyzer
from classifier_manager.gliner_model import PiiGlinerAnalyzer
from classifier_manager.inspector import ModelInspector

# --- IMPORT FILE HANDLERS ---
from file_handlers.ocr_engine import OcrEngine
from file_handlers.avro_handler import AvroHandler
from file_handlers.parquet_handler import ParquetHandler
from file_handlers.json_handler import JsonHandler
from file_handlers.pdf_handler import PdfHandler

# --- IMPORT CONNECTORS ---
from connectors.postgres_handler import PostgresHandler
from connectors.mysql_handler import MysqlHandler
from connectors.gmail_handler import GmailHandler
from connectors.drive_handler import DriveHandler
from connectors.aws_s3_handler import S3Handler
from connectors.azure_handler import AzureBlobHandler
from connectors.gcp_storage_handler import GcpStorageHandler
from connectors.slack_handler import SlackHandler           # <--- NEW
from connectors.confluence_handler import ConfluenceHandler # <--- NEW

# --- DEPENDENCY CHECKS ---
try:
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("Google Libraries not installed.")
try:
    import pymongo
    MONGO_AVAILABLE = True
except: MONGO_AVAILABLE = False
try:
    import boto3
    AWS_AVAILABLE = True
except: AWS_AVAILABLE = False
try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except: AZURE_AVAILABLE = False
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except: GCS_AVAILABLE = False

# NLTK Setup
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')
    nltk.download('punkt_tab')

class RegexClassifier:
    def __init__(self):
        self.colors = {
            "EMAIL": "#8ef", "FIRST_NAME": "#af9", "LAST_NAME": "#af9",
            "PHONE": "#faa", "SSN": "#fca", "CREDIT_CARD": "#fea",
            "LOCATION": "#dcf", "ORG": "#ffecb3", "DEFAULT": "#e0e0e0"
        }
        
        self.patterns: Dict[str, str] = {
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "PHONE": r"\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b",
            "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
            "CREDIT_CARD": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "AADHAAR_IND": r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b",
            "PAN_IND": r"\b[A-Z]{5}\d{4}[A-Z]{1}\b",
        }

        # 1. Classifiers
        self.spacy_analyzer = PiiSpacyAnalyzer()
        self.presidio_analyzer = PiiPresidioAnalyzer()
        self.gliner_analyzer = PiiGlinerAnalyzer()
        self.inspector = ModelInspector()
        
        # 2. File Handlers
        self.ocr_engine = OcrEngine()
        self.avro_handler = AvroHandler()
        self.parquet_handler = ParquetHandler()
        self.json_handler = JsonHandler()
        self.pdf_handler = PdfHandler(self.ocr_engine)

        # 3. Connectors
        self.pg_handler = PostgresHandler()
        self.mysql_handler = MysqlHandler()
        self.gmail_handler = GmailHandler()
        self.drive_handler = DriveHandler()
        self.s3_handler = S3Handler()
        self.azure_handler = AzureBlobHandler()
        self.gcp_handler = GcpStorageHandler()
        self.slack_handler = SlackHandler()           # <--- Init
        self.confluence_handler = ConfluenceHandler() # <--- Init

    def list_patterns(self): return self.patterns
    def add_pattern(self, n, r): self.patterns[n.upper()] = r
    def remove_pattern(self, n): self.patterns.pop(n.upper(), None)

    # --- CORE ANALYSIS ---
    def scan_with_regex(self, text: str) -> List[dict]:
        matches = []
        for label, regex in self.patterns.items():
            for m in re.finditer(regex, text):
                matches.append({"label": label, "text": m.group(), "start": m.start(), "end": m.end(), "source": "Regex"})
        return matches

    def scan_with_nltk(self, text: str) -> List[dict]:
        detections = []
        try:
            for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(text))):
                if hasattr(chunk, 'label') and chunk.label() in ['PERSON', 'GPE']:
                    val = " ".join(c[0] for c in chunk)
                    start = text.find(val)
                    if start != -1:
                        detections.append({
                            "label": "LOCATION" if chunk.label() == 'GPE' else "FIRST_NAME",
                            "text": val, "start": start, "end": start+len(val), "source": "NLTK"
                        })
        except: pass 
        return detections

    def analyze_text_hybrid(self, text: str) -> List[dict]:
        if not text: return []
        all_matches = []
        all_matches.extend(self.scan_with_regex(text))
        all_matches.extend(self.scan_with_nltk(text))
        all_matches.extend(self.spacy_analyzer.scan(text))
        all_matches.extend(self.presidio_analyzer.scan(text))
        all_matches.extend(self.gliner_analyzer.scan(text))
        
        all_matches.sort(key=lambda x: x['start'])
        unique = []
        if not all_matches: return []
        curr = all_matches[0]
        for next_m in all_matches[1:]:
            if next_m['start'] < curr['end']:
                if len(next_m['text']) > len(curr['text']):
                    curr = next_m
            else:
                unique.append(curr)
                curr = next_m
        unique.append(curr)
        return unique

    def run_full_inspection(self, text: str):
        return self.inspector.compare_models(
            self.scan_with_regex(text),
            self.scan_with_nltk(text),
            self.spacy_analyzer.scan(text),
            self.presidio_analyzer.scan(text),
            self.gliner_analyzer.scan(text)
        )

    # --- WRAPPERS FOR UI ---
    def get_json_data(self, file_obj) -> pd.DataFrame:
        return self.json_handler.read_file(file_obj)

    def get_pdf_page_text(self, file_bytes, page_num):
        return self.pdf_handler.get_page_text(file_bytes, page_num)

    def get_pdf_total_pages(self, file_bytes) -> int:
        return self.pdf_handler.get_total_pages(file_bytes)

    def get_labeled_pdf_image(self, file_bytes, page_num):
        text = self.get_pdf_page_text(file_bytes, page_num)
        matches = self.analyze_text_hybrid(text)
        return self.pdf_handler.render_labeled_image(file_bytes, page_num, matches, self.colors)

    def get_avro_data(self, file_bytes) -> pd.DataFrame:
        return self.avro_handler.convert_to_dataframe(file_bytes)
    
    def get_parquet_data(self, file_bytes) -> pd.DataFrame:
        return self.parquet_handler.convert_to_dataframe(file_bytes)
        
    def get_ocr_text_from_image(self, file_bytes) -> str:
        return self.ocr_engine.extract_text(file_bytes)

    def get_pii_counts_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        text = " ".join(df.astype(str).values.flatten())
        matches = self.analyze_text_hybrid(str(text))
        if not matches: return pd.DataFrame(columns=["PII Type", "Count"])
        counts = {}
        for m in matches: counts[m['label']] = counts.get(m['label'], 0) + 1
        return pd.DataFrame(list(counts.items()), columns=["PII Type", "Count"])
    
    def get_pii_counts(self, text: str) -> pd.DataFrame:
        matches = self.analyze_text_hybrid(str(text))
        if not matches: return pd.DataFrame(columns=["PII Type", "Count"])
        counts = {}
        for m in matches: counts[m['label']] = counts.get(m['label'], 0) + 1
        return pd.DataFrame(list(counts.items()), columns=["PII Type", "Count"])

    def mask_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        def mask_text(text):
            text = str(text)
            matches = self.analyze_text_hybrid(text)
            matches.sort(key=lambda x: x['start'], reverse=True)
            for m in matches:
                if "***" not in text[m['start']:m['end']]:
                    text = text[:m['start']] + "******" + text[m['end']:]
            return text
        return df.map(lambda x: mask_text(x) if isinstance(x, (str, int, float)) else x)

    def scan_dataframe_with_html(self, df: pd.DataFrame) -> pd.DataFrame:
        def highlight(text):
            text = str(text)
            matches = self.analyze_text_hybrid(text)
            matches.sort(key=lambda x: x['start'], reverse=True)
            for m in matches:
                if "<span" in text[m['start']:m['end']]: continue
                color = self.colors.get(m['label'], self.colors["DEFAULT"])
                replacement = f'<span style="background:{color}; padding:2px; border-radius:4px;">{m["text"]}</span>'
                text = text[:m['start']] + replacement + text[m['end']:]
            return text
        return df.map(lambda x: highlight(x) if isinstance(x, str) else x)

    def get_data_schema(self, df):
        return pd.DataFrame({"Column": df.columns, "Type": df.dtypes.astype(str)})

    # --- CONNECTOR WRAPPERS ---
    def get_postgres_data(self, host, port, db, user, pw, table):
        return self.pg_handler.fetch_data(host, port, db, user, pw, table)

    def get_mysql_data(self, host, port, db, user, pw, table):
        return self.mysql_handler.fetch_data(host, port, db, user, pw, table)

    def get_gmail_data(self, credentials_file, num_emails=10) -> pd.DataFrame:
        return self.gmail_handler.fetch_emails(credentials_file, num_emails)

    def get_google_drive_files(self, credentials_dict):
        return self.drive_handler.list_files(credentials_dict)

    def download_drive_file(self, file_id, mime_type, credentials_dict):
        return self.drive_handler.download_file(file_id, mime_type, credentials_dict)

    def get_s3_buckets(self, a, s, r): return self.s3_handler.get_buckets(a, s, r)
    def get_s3_files(self, a, s, r, b): return self.s3_handler.get_files(a, s, r, b)
    def download_s3_file(self, a, s, r, b, k): return self.s3_handler.download_file(a, s, r, b, k)
    
    def get_azure_containers(self, c): return self.azure_handler.get_containers(c)
    def get_azure_blobs(self, c, n): return self.azure_handler.get_blobs(c, n)
    def download_azure_blob(self, c, n, b): return self.azure_handler.download_blob(c, n, b)

    def get_gcs_buckets(self, c): return self.gcp_handler.get_buckets(c)
    def get_gcs_files(self, c, b): return self.gcp_handler.get_files(c, b)
    def download_gcs_file(self, c, b, n): return self.gcp_handler.download_file(c, b, n)

    # --- NEW WRAPPERS FOR SLACK & CONFLUENCE ---
    def get_slack_messages(self, token, channel_id):
        return self.slack_handler.fetch_messages(token, channel_id)

    def get_confluence_page(self, url, username, token, page_id):
        return self.confluence_handler.fetch_page_content(url, username, token, page_id)

    # --- MONGO (Still here) ---
    def get_mongodb_data(self, host, port, db, user, pw, collection):
        if not MONGO_AVAILABLE: return pd.DataFrame()
        try:
            if user and pw: uri = f"mongodb://{quote_plus(user)}:{quote_plus(pw)}@{host}:{port}/"
            else: uri = f"mongodb://{host}:{port}/"
            client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
            cursor = client[db][collection].find().limit(100)
            data = list(cursor)
            if not data: return pd.DataFrame()
            for d in data: d['_id'] = str(d.get('_id', ''))
            return pd.json_normalize(data)
        except: return pd.DataFrame()