import re
import unicodedata
from typing import List, Set

PLURAL_MAP = {
    "eyes": "eye",
    "stools": "stool",
    "disorders": "disorder",
    "sensations": "sensation",
    "organs": "organ",
    "pains": "pain",
}

SYNONYM_MAP = {
    "burning sensation": "burning",
    "inflammatory": "inflammation",
    "loose stools": "loose stool",
}

def normalize_text(text: str) -> str:
    """
    Standardize clinical input text:
    - Lowercase
    - Unicode NFD normalization
    - Strip punctuation
    - Whitespace collapse
    - Plural reduction
    - Standardize safe synonyms
    """
    if not text:
        return ""
    
    # Unicode NFD normalize & lowercase
    normalized = unicodedata.normalize("NFD", text).lower()
    
    # Strip non-alphanumeric except whitespace
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    
    # Collapse whitespace
    words = normalized.split()
    
    # Plural reduction per word
    cleaned_words = [PLURAL_MAP.get(w, w) for w in words]
    res_text = " ".join(cleaned_words)
    
    # Standardize safe phrase synonyms
    for phrase, replacement in SYNONYM_MAP.items():
        res_text = re.sub(r'\b' + re.escape(phrase) + r'\b', replacement, res_text)
        
    return res_text.strip()

def tokenize_and_normalize(text: str) -> Set[str]:
    """
    Returns normalized token set for keyword matching.
    """
    norm = normalize_text(text)
    return set(norm.split())
