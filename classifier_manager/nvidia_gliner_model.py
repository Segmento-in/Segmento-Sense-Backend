import os
from gliner import GLiNER

class PiiNvidiaGlinerAnalyzer:
    """
    Wraps nvidia/gliner-PII — NVIDIA's enterprise-grade GLiNER variant
    optimised for high-precision PII entity extraction.
    Loaded on demand via the Lazy-Loading model registry.
    """
    MODEL_ID = "nvidia/gliner-PII-0.1"   # exact HF repo name as of 2025

    def __init__(self):
        self.model = None
        self.model_loaded = False

        # Natural-language labels passed to GLiNER at inference time
        self.labels = [
            "person name",
            "email address",
            "phone number",
            "credit card number",
            "social security number",
            "organization",
            "location",
            "date of birth",
            "ip address",
            "passport number",
            "driver license number",
            "bank account number",
        ]

        # Map GLiNER natural-language labels → platform standard
        self.label_map = {
            "person name":          "FIRST_NAME",
            "email address":        "EMAIL",
            "phone number":         "PHONE",
            "credit card number":   "CREDIT_CARD",
            "social security number": "SSN",
            "organization":         "ORG",
            "location":             "LOCATION",
            "date of birth":        "DATE_TIME",
            "ip address":           "IP_ADDRESS",
            "passport number":      "PASSPORT",
            "driver license number":"DRIVER_LICENSE",
            "bank account number":  "BANK_ACCOUNT",
        }

    def load(self):
        """Lazily load the model into RAM. Called only when a user activates it."""
        if self.model_loaded:
            return True
        try:
            hf_token = os.getenv("HF_TOKEN")
            print(f"[LAZY LOAD] Loading NVIDIA GLiNER PII model...")
            self.model = GLiNER.from_pretrained(self.MODEL_ID, token=hf_token)
            self.model_loaded = True
            print(f"[OK] NVIDIA GLiNER PII model '{self.MODEL_ID}' loaded successfully.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load NVIDIA GLiNER PII model: {e}")
            self.model_loaded = False
            return False

    def scan(self, text: str) -> list:
        if not self.model_loaded or not text or not text.strip():
            return []

        # GLiNER handles up to ~2000 chars safely before truncation warnings
        text = text[:2000]

        try:
            entities = self.model.predict_entities(text, self.labels, threshold=0.5)
            detections = []
            for ent in entities:
                mapped_label = self.label_map.get(ent["label"], ent["label"].upper().replace(" ", "_"))
                detections.append({
                    "text":   ent["text"],
                    "label":  mapped_label,
                    "start":  ent["start"],
                    "end":    ent["end"],
                    "score":  float(ent["score"]),
                    "source": "NVIDIA-GLiNER",
                })
            return detections
        except Exception as e:
            print(f"[WARN] NVIDIA GLiNER PII scan error: {e}")
            return []
