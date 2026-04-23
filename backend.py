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

# --- IMPORT CLASSIFIERS (Always-On) ---
from classifier_manager.spacy_model import PiiSpacyAnalyzer
from classifier_manager.presidio_model import PiiPresidioAnalyzer
from classifier_manager.gliner_model import PiiGlinerAnalyzer
from classifier_manager.deberta_model import PiiDebertaAnalyzer
from classifier_manager.inspector import ModelInspector
from classifier_manager.regex_scanner import RegexScanner

# --- IMPORT CLASSIFIERS (Lazy-Loaded on demand) ---
from classifier_manager.pasteproof_model import PiiPasteproofAnalyzer
from classifier_manager.piiranha_model import PiiPiiranhaAnalyzer
from classifier_manager.nvidia_gliner_model import PiiNvidiaGlinerAnalyzer
from classifier_manager.mmbert_model import PiiMmbertAnalyzer

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
from connectors.slack_handler import SlackHandler          
from connectors.confluence_handler import ConfluenceHandler
from connectors.mongo_handler import MongoHandler          

# --- DEPENDENCY CHECKS ---
try:
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("Google Libraries not installed.")

# Optional dependency checks
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
    """
    Main Orchestrator Class.
    This acts as the central controller for all PII detection operations.
    """
    # -----------------------------------------------------------------------
    # MODEL REGISTRY: Maps user-facing key -> (instance, always_on flag)
    # always_on=True  -> loaded at startup, always runs
    # always_on=False -> lazy-loaded only when user enables the toggle
    # -----------------------------------------------------------------------
    _MODEL_CLASSES = {
        "regex":         None,          # handled inline, not a class instance
        "nltk":          None,          # handled inline, not a class instance
        "spacy":         PiiSpacyAnalyzer,
        "presidio":      PiiPresidioAnalyzer,
        "gliner":        PiiGlinerAnalyzer,
        "deberta":       PiiDebertaAnalyzer,
        "pasteproof":    PiiPasteproofAnalyzer,
        "piiranha":      PiiPiiranhaAnalyzer,
        "nvidia_gliner": PiiNvidiaGlinerAnalyzer,
        "mmbert":        PiiMmbertAnalyzer,
    }

    # Models that load at startup (core ensemble, low memory)
    _ALWAYS_ON = {"regex", "nltk", "spacy", "presidio", "gliner", "deberta"}

    def __init__(self):
        # 1. Always-On Classifiers (loaded at boot)
        self.regex_scanner    = RegexScanner()
        self.spacy_analyzer   = PiiSpacyAnalyzer()
        self.presidio_analyzer= PiiPresidioAnalyzer()
        self.gliner_analyzer  = PiiGlinerAnalyzer()
        self.deberta_analyzer = PiiDebertaAnalyzer()
        self.inspector        = ModelInspector()

        # 2. Lazy-Load Registry: key -> instance (populated on first use)
        self._lazy_models: Dict[str, Any] = {}
        self._lazy_classes = {
            "pasteproof":    PiiPasteproofAnalyzer,
            "piiranha":      PiiPiiranhaAnalyzer,
            "nvidia_gliner": PiiNvidiaGlinerAnalyzer,
            "mmbert":        PiiMmbertAnalyzer,
        }
        
        # 2. File Handlers
        self.ocr_engine = OcrEngine()
        self.avro_handler = AvroHandler()
        self.parquet_handler = ParquetHandler()
        self.json_handler = JsonHandler()
        self.pdf_handler = PdfHandler(self.ocr_engine)

        # 3. Connectors
        self.pg_handler = PostgresHandler()
        self.mysql_handler = MysqlHandler()
        self.mongo_handler = MongoHandler()
        self.gmail_handler = GmailHandler()
        self.drive_handler = DriveHandler()
        self.s3_handler = S3Handler()
        self.azure_handler = AzureBlobHandler()
        self.gcp_handler = GcpStorageHandler()
        self.slack_handler = SlackHandler()
        self.confluence_handler = ConfluenceHandler()

        # Shortcuts for UI colors
        self.colors = self.regex_scanner.colors

    # --- PATTERN MANAGEMENT PROXY ---
    def list_patterns(self): return self.regex_scanner.patterns
    def add_pattern(self, n, r): self.regex_scanner.add_pattern(n, r)
    def remove_pattern(self, n): self.regex_scanner.remove_pattern(n)

    # --- CORE ANALYSIS ---
    def scan_with_regex(self, text: str) -> List[dict]:
        return self.regex_scanner.scan(text)

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

    def _get_lazy_model(self, key: str):
        """Instantiate and load a lazy model on first access. Returns instance or None."""
        if key not in self._lazy_classes:
            return None
        if key not in self._lazy_models:
            instance = self._lazy_classes[key]()
            loaded = instance.load()
            if not loaded:
                return None
            self._lazy_models[key] = instance
        return self._lazy_models[key]

    def analyze_text_hybrid(self, text: str, selected_models: List[str] = None) -> List[dict]:
        """
        Run PII detection using only the models specified in `selected_models`.
        If `selected_models` is None or empty, the full always-on ensemble runs.
        """
        if not text:
            return []

        # Default: run all always-on models
        if not selected_models:
            selected_models = list(self._ALWAYS_ON)

        all_matches = []

        # --- Always-On models (no lazy loading needed) ---
        if "regex"    in selected_models: all_matches.extend(self.regex_scanner.scan(text))
        if "nltk"     in selected_models: all_matches.extend(self.scan_with_nltk(text))
        if "spacy"    in selected_models: all_matches.extend(self.spacy_analyzer.scan(text))
        if "presidio" in selected_models: all_matches.extend(self.presidio_analyzer.scan(text))
        if "gliner"   in selected_models: all_matches.extend(self.gliner_analyzer.scan(text))
        if "deberta"  in selected_models: all_matches.extend(self.deberta_analyzer.scan(text))

        # --- Lazy-loaded models (instantiated on first use) ---
        for lazy_key in ["pasteproof", "piiranha", "nvidia_gliner", "mmbert"]:
            if lazy_key in selected_models:
                model = self._get_lazy_model(lazy_key)
                if model:
                    all_matches.extend(model.scan(text))

        # Sort and Deduplicate by span overlap (keep longest match)
        all_matches.sort(key=lambda x: x['start'])
        unique = []
        if not all_matches:
            return []
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

    def run_full_inspection(self, text: str, selected_models: List[str] = None):
        """
        Builds a per-model match dictionary dynamically, so the Inspector table
        automatically reflects exactly which models were activated.
        """
        if not selected_models:
            selected_models = list(self._ALWAYS_ON)

        model_results: Dict[str, list] = {}

        if "regex"    in selected_models: model_results["🛠️ Regex"]    = self.regex_scanner.scan(text)
        if "nltk"     in selected_models: model_results["🧠 NLTK"]     = self.scan_with_nltk(text)
        if "spacy"    in selected_models: model_results["🤖 SpaCy"]    = self.spacy_analyzer.scan(text)
        if "presidio" in selected_models: model_results["🛡️ Presidio"] = self.presidio_analyzer.scan(text)
        if "gliner"   in selected_models: model_results["🦅 GLiNER"]   = self.gliner_analyzer.scan(text)
        if "deberta"  in selected_models: model_results["🚀 DeBERTa"]  = self.deberta_analyzer.scan(text)

        for lazy_key, label in [("pasteproof", "📋 Pasteproof"), ("piiranha", "🐟 Piiranha"),
                                 ("nvidia_gliner", "⚡ NVIDIA-GLiNER"), ("mmbert", "🌐 mmbert32k")]:
            if lazy_key in selected_models:
                m = self._get_lazy_model(lazy_key)
                if m:
                    model_results[label] = m.scan(text)

        return self.inspector.compare_models_dynamic(model_results)

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

    def get_pii_counts_dataframe(self, df: pd.DataFrame, selected_models: List[str] = None) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["PII Type", "Count"])
        
        # Sample at most 100 rows to prevent massive string flattening
        sample_size = min(100, len(df))
        df_sample = df.sample(n=sample_size, random_state=42) if sample_size > 0 else df
        
        # Select only object/string columns to avoid useless numbers
        str_cols = df_sample.select_dtypes(include=['object', 'string'])
        if str_cols.empty:
            return pd.DataFrame(columns=["PII Type", "Count"])
            
        # Truncate to a safe maximum limit (approx 50k chars) to prevent Transformer OOM
        text = " ".join(str_cols.fillna("").astype(str).values.flatten())
        return self.get_pii_counts(text[:50000], selected_models)
    
    def get_pii_counts(self, text: str, selected_models: List[str] = None) -> pd.DataFrame:
        matches = self.analyze_text_hybrid(str(text), selected_models)
        if not matches: return pd.DataFrame(columns=["PII Type", "Count"])
        counts = {}
        for m in matches: counts[m['label']] = counts.get(m['label'], 0) + 1
        return pd.DataFrame(list(counts.items()), columns=["PII Type", "Count"])

    def mask_dataframe(self, df: pd.DataFrame, selected_models: List[str] = None) -> pd.DataFrame:
        df_masked = df.copy().astype(str)
        
        def mask_text(text):
            if pd.isna(text) or text == "nan" or text == "None": return ""
            if not text.strip(): return text
            try:
                matches = self.analyze_text_hybrid(text, selected_models)
                if not matches: return text
                matches.sort(key=lambda x: x['start'], reverse=True)
                for m in matches:
                    if "***" not in text[m['start']:m['end']]:
                        text = text[:m['start']] + "******" + text[m['end']:]
                return text
            except Exception as e:
                print(f"Masking error: {e}")
                return text
        
        # Process all columns to catch numeric PII (like phone numbers)
        for col in df_masked.columns:
            unique_vals = df_masked[col].unique()
            masked_map = {val: mask_text(val) for val in unique_vals}
            df_masked[col] = df_masked[col].map(masked_map)
                
        return df_masked

    def scan_dataframe_with_html(self, df: pd.DataFrame, selected_models: List[str] = None) -> pd.DataFrame:
        df_scanned = df.copy().astype(str)
        
        def highlight(text):
            if pd.isna(text) or text == "nan" or text == "None": return ""
            if not text.strip(): return text
            try:
                matches = self.analyze_text_hybrid(text, selected_models)
                if not matches: return text
                matches.sort(key=lambda x: x['start'], reverse=True)
                for m in matches:
                    if "<span" in text[m['start']:m['end']]: continue
                    color = self.colors.get(m['label'], self.colors["DEFAULT"])
                    replacement = f'<span style="background:{color}; padding:2px; border-radius:4px;">{m["text"]}</span>'
                    text = text[:m['start']] + replacement + text[m['end']:]
                return text
            except Exception as e:
                print(f"Highlight error: {e}")
                return text
                
        # Process all columns to catch numeric PII (like phone numbers)
        for col in df_scanned.columns:
            unique_vals = df_scanned[col].unique()
            highlight_map = {val: highlight(val) for val in unique_vals}
            df_scanned[col] = df_scanned[col].map(highlight_map)
                
        return df_scanned

    def get_data_schema(self, df):
        return pd.DataFrame({"Column": df.columns, "Type": df.dtypes.astype(str)})

    # --- CONNECTOR WRAPPERS ---
    def get_postgres_data(self, host, port, db, user, pw, table):
        return self.pg_handler.fetch_data(host, port, db, user, pw, table)

    def get_mysql_data(self, host, port, db, user, pw, table):
        return self.mysql_handler.fetch_data(host, port, db, user, pw, table)

    def get_mongodb_data(self, host, port, db, user, pw, collection):
        return self.mongo_handler.fetch_data(host, port, db, user, pw, collection)

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

    # --- ENTERPRISE WRAPPERS ---
    def get_slack_messages(self, token, channel_id):
        return self.slack_handler.fetch_messages(token, channel_id)

    def get_confluence_page(self, url, username, token, page_id):
        return self.confluence_handler.fetch_page_content(url, username, token, page_id)