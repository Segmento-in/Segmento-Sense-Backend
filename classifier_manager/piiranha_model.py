import os
import torch
from transformers import pipeline

class PiiPiiranhaAnalyzer:
    """
    Wraps iiiorg/piiranha-v1-detect-personal-information.
    Fine-tuned specifically for personal-information detection.
    Loaded on demand via the Lazy-Loading model registry.
    """
    MODEL_ID = "iiiorg/piiranha-v1-detect-personal-information"

    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.device = 0 if torch.cuda.is_available() else -1

        # Map Piiranha's B-/I- BIO-tagged labels to the platform standard
        self.label_mapping = {
            "GIVENNAME":        "FIRST_NAME",
            "SURNAME":          "LAST_NAME",
            "PERSON":           "FIRST_NAME",
            "NAME":             "FIRST_NAME",
            "EMAIL":            "EMAIL",
            "EMAILADDRESS":     "EMAIL",
            "TELEPHONENUM":     "PHONE",
            "PHONE":            "PHONE",
            "SOCIALNUM":        "SSN",
            "SSN":              "SSN",
            "CREDITCARDNUMBER": "CREDIT_CARD",
            "CREDITCARD":       "CREDIT_CARD",
            "IPADDRESS":        "IP_ADDRESS",
            "IP":               "IP_ADDRESS",
            "IDNUM":            "SSN",
            "BUILDINGNUM":      "LOCATION",
            "CITY":             "LOCATION",
            "STATE":            "LOCATION",
            "COUNTRY":          "LOCATION",
            "ZIPCODE":          "LOCATION",
            "STREET":           "LOCATION",
            "USERNAME":         "FIRST_NAME",
            "URL":              "URL",
            "DATEOFBIRTH":      "DATE_TIME",
            "AGE":              "DATE_TIME",
        }

    def load(self):
        """Lazily load the model into RAM. Called only when a user activates it."""
        if self.model_loaded:
            return True
        try:
            hf_token = os.getenv("HF_TOKEN")
            print(f"[LAZY LOAD] Loading Piiranha model on device: {'GPU' if self.device == 0 else 'CPU'}...")
            self.pipe = pipeline(
                "token-classification",
                model=self.MODEL_ID,
                device=self.device,
                token=hf_token,
                aggregation_strategy="simple",
            )
            self.model_loaded = True
            print(f"[OK] Piiranha model '{self.MODEL_ID}' loaded successfully.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load Piiranha model: {e}")
            self.model_loaded = False
            return False

    def scan(self, text: str) -> list:
        if not self.model_loaded or not text or not text.strip():
            return []

        text = text[:2000]

        try:
            results = self.pipe(text)
            detections = []
            for entity in results:
                # Strip BIO prefix (B-, I-) if present
                raw_label = entity.get("entity_group", entity.get("entity", "UNKNOWN"))
                raw_label = raw_label.upper().lstrip("BI-").strip("_")
                mapped_label = self.label_mapping.get(raw_label, "DEFAULT")
                if mapped_label == "DEFAULT":
                    continue
                detections.append({
                    "text":   entity["word"].strip(),
                    "label":  mapped_label,
                    "start":  entity["start"],
                    "end":    entity["end"],
                    "score":  float(entity["score"]),
                    "source": "Piiranha",
                })
            return detections
        except Exception as e:
            print(f"[WARN] Piiranha scan error: {e}")
            return []
