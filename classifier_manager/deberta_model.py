import os
import torch
from transformers import pipeline

class PiiDebertaAnalyzer:
    """
    Implements the DeBERTa V3 model, widely recognized for winning the Kaggle PII Detection competition.
    It uses a token-classification pipeline to detect PII entities.
    """
    def __init__(self, model_name="lakshyakh93/deberta_finetuned_pii"):

        self.device = 0 if torch.cuda.is_available() else -1
        print(f"Loading DeBERTa Model on device: {'GPU' if self.device == 0 else 'CPU'}...")
        
        try:
            # Get HuggingFace token from environment (for private/gated models)
            hf_token = os.getenv('HF_TOKEN')
            
            # Aggregation strategy 'simple' merges B-TAG and I-TAG into a single entity automatically
            self.pipe = pipeline(
                "token-classification", 
                model=model_name, 
                device=self.device, 
                token=hf_token,  # Use 'token' parameter (use_auth_token is deprecated)
                aggregation_strategy="simple"
            )
            self.model_loaded = True
            print(f"[OK] DeBERTa model '{model_name}' loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load DeBERTa model: {e}")
            self.model_loaded = False

        # Map Kaggle/DeBERTa labels to your App's standard labels
        self.label_mapping = {
            "NAME_STUDENT": "FIRST_NAME",
            "EMAIL": "EMAIL",
            "PHONE_NUM": "PHONE",
            "STREET_ADDRESS": "LOCATION",
            "ID_NUM": "SSN",
            "USERNAME": "FIRST_NAME",
            "URL_PERSONAL": "URL",
            "PER": "FIRST_NAME",  # Generic NER label
            "LOC": "LOCATION",    # Generic NER label
            "ORG": "LOCATION"     # Mapping ORG to Location or ignore based on preference
        }

    def scan(self, text: str):
        if not self.model_loaded or not text:
            return []

        try:
            results = self.pipe(text)
            detections = []
            
            for entity in results:
                # entity looks like: {'entity_group': 'NAME_STUDENT', 'score': 0.99, 'word': 'John Doe', 'start': 0, 'end': 8}
                original_label = entity.get('entity_group', 'UNKNOWN')
                mapped_label = self.label_mapping.get(original_label, "DEFAULT")
                
                # Only include known PII types
                if mapped_label != "DEFAULT":
                    detections.append({
                        "text": entity['word'].strip(),
                        "label": mapped_label,
                        "start": entity['start'],
                        "end": entity['end'],
                        "source": "DeBERTa",
                        "score": float(entity['score'])
                    })
            return detections
            
        except Exception as e:
            print(f"DeBERTa scan error: {e}")
            return []