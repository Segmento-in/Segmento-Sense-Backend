import os
import torch
from transformers import pipeline

class PiiMmbertAnalyzer:
    """
    Wraps llm-semantic-router/mmbert32k-pii-detector-merged.
    A large-context (32k token window) BERT-based PII detector.
    Best suited for long unstructured documents (PDFs, emails, contracts).
    Loaded on demand via the Lazy-Loading model registry.
    """
    MODEL_ID = "llm-semantic-router/mmbert32k-pii-detector-merged"

    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.device = 0 if torch.cuda.is_available() else -1

        self.label_mapping = {
            "PER":       "FIRST_NAME",
            "PERSON":    "FIRST_NAME",
            "ORG":       "ORG",
            "LOC":       "LOCATION",
            "GPE":       "LOCATION",
            "EMAIL":     "EMAIL",
            "PHONE":     "PHONE",
            "SSN":       "SSN",
            "CC":        "CREDIT_CARD",
            "IP":        "IP_ADDRESS",
            "URL":       "URL",
            "DATE":      "DATE_TIME",
            "ADDRESS":   "LOCATION",
        }

    def load(self):
        """Lazily load the model into RAM. Called only when a user activates it."""
        if self.model_loaded:
            return True
        try:
            hf_token = os.getenv("HF_TOKEN")
            print(f"[LAZY LOAD] Loading mmbert32k model on device: {'GPU' if self.device == 0 else 'CPU'}...")
            self.pipe = pipeline(
                "token-classification",
                model=self.MODEL_ID,
                device=self.device,
                token=hf_token,
                aggregation_strategy="simple",
            )
            self.model_loaded = True
            print(f"[OK] mmbert32k model '{self.MODEL_ID}' loaded successfully.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load mmbert32k model: {e}")
            self.model_loaded = False
            return False

    def scan(self, text: str) -> list:
        if not self.model_loaded or not text or not text.strip():
            return []

        # This model supports a very long context; still cap at 8000 chars for safety
        text = text[:8000]

        try:
            results = self.pipe(text)
            detections = []
            for entity in results:
                raw_label = entity.get("entity_group", entity.get("entity", "UNKNOWN")).upper()
                mapped_label = self.label_mapping.get(raw_label, "DEFAULT")
                if mapped_label == "DEFAULT":
                    continue
                detections.append({
                    "text":   entity["word"].strip(),
                    "label":  mapped_label,
                    "start":  entity["start"],
                    "end":    entity["end"],
                    "score":  float(entity["score"]),
                    "source": "mmbert32k",
                })
            return detections
        except Exception as e:
            print(f"[WARN] mmbert32k scan error: {e}")
            return []
