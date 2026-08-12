import json
from pathlib import Path
from typing import List, Optional
from app.schemas import NamasteConcept

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "namaste.json"

_namaste_cache: Optional[List[NamasteConcept]] = None

def get_namaste_concepts() -> List[NamasteConcept]:
    global _namaste_cache
    if _namaste_cache is None:
        if not DATA_PATH.exists():
            return []
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            _namaste_cache = [NamasteConcept(**item) for item in raw_data]
    return _namaste_cache

def get_namaste_concept_by_code(code: str) -> Optional[NamasteConcept]:
    concepts = get_namaste_concepts()
    code_upper = code.strip().upper()
    for concept in concepts:
        if concept.code.upper() == code_upper:
            return concept
    return None
