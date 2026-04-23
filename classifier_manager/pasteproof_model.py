import os
import torch
from transformers import pipeline

class PiiPasteproofAnalyzer:
    """
    Wraps joneauxedgar/pasteproof-pii-detector-v2.
    A token-classification transformer fine-tuned specifically for PII detection.
    Loaded on demand via the Lazy-Loading model registry.
    """
    MODEL_ID = "joneauxedgar/pasteproof-pii-detector-v2"

    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.device = 0 if torch.cuda.is_available() else -1

        # Map this model's output labels to the platform's standard label schema
        self.label_mapping = {
            "PER":            "FIRST_NAME",
            "PERSON":         "FIRST_NAME",
            "NAME":           "FIRST_NAME",
            "ORG":            "ORG",
            "LOC":            "LOCATION",
            "GPE":            "LOCATION",
            "EMAIL":          "EMAIL",
            "PHONE":          "PHONE",
            "PHONE_NUM":      "PHONE",
            "SSN":            "SSN",
            "CREDIT_CARD":    "CREDIT_CARD",
            "IP_ADDRESS":     "IP_ADDRESS",
            "URL":            "URL",
            "DATE":           "DATE_TIME",
            "ADDRESS":        "LOCATION",
        }

    def load(self):
        """Lazily load the model into RAM. Called only when a user activates it."""
        if self.model_loaded:
            return True
        try:
            hf_token = os.getenv("HF_TOKEN")
            print(f"[LAZY LOAD] Loading Pasteproof model on device: {'GPU' if self.device == 0 else 'CPU'}...")
            self.pipe = pipeline(
                "token-classification",
                model=self.MODEL_ID,
                device=self.device,
                token=hf_token,
                aggregation_strategy="simple",
            )
            self.model_loaded = True
            print(f"[OK] Pasteproof model '{self.MODEL_ID}' loaded successfully.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load Pasteproof model: {e}")
            self.model_loaded = False
            return False

    def scan(self, text: str) -> list:
        if not self.model_loaded or not text or not text.strip():
            return []

        # Truncate to prevent tokenizer overflow (this model handles ~512 tokens)
        text = text[:2000]

        try:
            results = self.pipe(text)
            detections = []
            for entity in results:
                original_label = entity.get("entity_group", entity.get("entity", "UNKNOWN")).upper()
                mapped_label = self.label_mapping.get(original_label, "DEFAULT")
                if mapped_label == "DEFAULT":
                    continue
                detections.append({
                    "text":   entity["word"].strip(),
                    "label":  mapped_label,
                    "start":  entity["start"],
                    "end":    entity["end"],
                    "score":  float(entity["score"]),
                    "source": "Pasteproof",
                })
            return detections
        except Exception as e:
            print(f"[WARN] Pasteproof scan error: {e}")
            return []
