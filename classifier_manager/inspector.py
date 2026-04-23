import pandas as pd
from typing import Dict, List

class ModelInspector:
    def __init__(self):
        pass

    def compare_models_dynamic(self, model_results: Dict[str, List[dict]]) -> pd.DataFrame:
        """
        Dynamically compares N model match lists and computes per-model accuracy
        against the union of all detected PII across every active model.

        Args:
            model_results: A dict mapping a human-readable model label (e.g. "🤖 SpaCy")
                           to that model's list of match dicts returned by .scan().

        Returns:
            A pandas DataFrame sorted by Accuracy descending.
        """
        if not model_results:
            return pd.DataFrame()

        # ---------------------------------------------------------------
        # Step 1: Build a master set of all unique PII spans found by any model.
        # Key: (start, end, text) to uniquely identify a span.
        # ---------------------------------------------------------------
        all_detections: Dict[tuple, dict] = {}

        def add_to_master(matches: List[dict]) -> set:
            found_set = set()
            for m in matches:
                key = (m["start"], m["end"], m["text"])
                if key not in all_detections:
                    all_detections[key] = {"text": m["text"], "label": m["label"]}
                found_set.add(key)
            return found_set

        # Build per-model found sets and the global union simultaneously
        per_model_sets: Dict[str, set] = {}
        for model_label, matches in model_results.items():
            per_model_sets[model_label] = add_to_master(matches)

        total_unique_pii = set(all_detections.keys())
        total_count = len(total_unique_pii) if total_unique_pii else 1

        # ---------------------------------------------------------------
        # Step 2: Compute Missed PII (anything found by other models but not this one)
        # ---------------------------------------------------------------
        def fmt(item_set: set) -> str:
            items = [all_detections[k]["text"] for k in item_set]
            display = items[:5]
            res = ", ".join(display)
            if len(items) > 5:
                res += f", (+{len(items) - 5} more)"
            return res if res else "None"

        # ---------------------------------------------------------------
        # Step 3: Build the stats rows
        # ---------------------------------------------------------------
        stats = []
        for model_label, found_set in per_model_sets.items():
            missed_set = total_unique_pii - found_set
            stats.append({
                "Model":         model_label,
                "Detected PII":  fmt(found_set),
                "Missed PII":    fmt(missed_set),
                "Accuracy":      len(found_set) / total_count,
                "Count":         len(found_set),
            })

        return pd.DataFrame(stats).sort_values(by="Accuracy", ascending=False)

    # -----------------------------------------------------------------------
    # Backward-compatible shim — keeps old callers working without crashing.
    # -----------------------------------------------------------------------
    def compare_models(self, regex_matches, nltk_matches, spacy_matches,
                       presidio_matches, gliner_matches, deberta_matches):
        """Legacy 6-model wrapper — delegates to compare_models_dynamic."""
        return self.compare_models_dynamic({
            "🛠️ Regex":    regex_matches,
            "🧠 NLTK":     nltk_matches,
            "🤖 SpaCy":    spacy_matches,
            "🛡️ Presidio": presidio_matches,
            "🦅 GLiNER":   gliner_matches,
            "🚀 DeBERTa":  deberta_matches,
        })