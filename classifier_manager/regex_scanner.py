import re
from typing import Dict, List

class RegexScanner:
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

    def add_pattern(self, name, regex):
        self.patterns[name.upper()] = regex

    def remove_pattern(self, name):
        self.patterns.pop(name.upper(), None)

    def scan(self, text: str) -> List[dict]:
        """
        Scans text using defined Regex patterns.
        """
        matches = []
        for label, regex in self.patterns.items():
            try:
                for m in re.finditer(regex, text):
                    matches.append({
                        "label": label,
                        "text": m.group(),
                        "start": m.start(),
                        "end": m.end(),
                        "source": "Regex"
                    })
            except re.error:
                continue # Skip invalid user-defined regex
        return matches