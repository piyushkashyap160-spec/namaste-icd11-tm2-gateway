from typing import List, Dict, Set, Tuple, Optional
import logging
from app.schemas import (
    NamasteConcept,
    TM2Concept,
    ClinicalEvidence,
    CandidateMatch,
    ConceptMappingResponse
)
from app.terminology.normalizer import normalize_text, tokenize_and_normalize
from app.terminology.namaste import get_namaste_concepts, get_namaste_concept_by_code
from app.terminology.tm2 import get_tm2_concepts

logger = logging.getLogger(__name__)

# Clinical Knowledge Dictionaries for Semantic Extraction
ANATOMY_VOCAB = {
    "shoulder", "eye", "eyelid", "skull", "head", "bowel",
    "sense organ", "organ", "skin", "joint", "chest", "arm", "leg"
}

SYMPTOM_VOCAB = {
    "burning", "pain", "inflammation", "inflammatory", "fever",
    "cough", "headache", "swelling", "churned"
}

QUALITY_VOCAB = {
    "burning", "loose", "dry", "bloodshot", "hard", "frozen", "acute", "chronic"
}

OBJECT_VOCAB = {
    "stool", "stools", "eye", "shoulder", "eyelid", "bowel", "organ", "skull"
}

TEMPORAL_CONTEXT_VOCAB = {
    "sudden", "onset", "akasmAt", "continuous", "feeling", "as", "if",
    "churned", "vat", "vyatha", "pattern", "sensation", "disorder", "disease"
}

GENERIC_VOCAB = {
    "disease", "diseases", "disorder", "disorders", "condition", "problem", "syndrome", "illness"
}

FUNCTIONAL_VOCAB = {
    "functioning", "proper functioning", "function", "healthy state", "sense organs"
}


def _match_vocab_terms(vocab: Set[str], tokens: Set[str], norm_text: str) -> Set[str]:
    """
    Match vocabulary terms against normalized text.

    Single-word terms are matched against the token set (exact word
    match), not as a substring of the whole text -- this avoids false
    positives like "arm" matching inside "warmth" or "alarming".

    Multi-word phrases (e.g. "sense organ") cannot be a single token,
    so they are matched as a substring of the normalized text instead.
    """
    matches: Set[str] = set()
    for term in vocab:
        if " " in term:
            if term in norm_text:
                matches.add(term)
        else:
            if term in tokens:
                matches.add(term)
    return matches


def extract_clinical_features(text: str) -> Dict[str, Set[str]]:
    """
    Extract semantic categories from normalized clinical text.
    Categories: anatomy, symptoms, quality, findings, clinical_objects, temporal, functional, generic
    """
    norm_text = normalize_text(text)
    tokens = set(norm_text.split())
    
    features = {
        "anatomy": set(),
        "symptoms": set(),
        "quality": set(),
        "findings": set(),
        "objects": set(),
        "temporal": set(),
        "functional": set(),
        "generic": set(),
        "all_words": tokens
    }

    # Match Multi-word or Single-word features (token-based for single words)
    features["anatomy"] = _match_vocab_terms(ANATOMY_VOCAB, tokens, norm_text)
    features["symptoms"] = _match_vocab_terms(SYMPTOM_VOCAB, tokens, norm_text)
    features["quality"] = _match_vocab_terms(QUALITY_VOCAB, tokens, norm_text)

    for obj in OBJECT_VOCAB:
        if obj in tokens or (obj + "s") in tokens:
            features["objects"].add(obj.rstrip("s"))

    for temp in TEMPORAL_CONTEXT_VOCAB:
        if temp in norm_text:
            features["temporal"].add(temp)

    for func in FUNCTIONAL_VOCAB:
        if func in norm_text:
            features["functional"].add(func)

    for gen in GENERIC_VOCAB:
        if gen in norm_text:
            features["generic"].add(gen)

    # Special findings detection
    if "swelling" in norm_text:
        features["findings"].add("swelling")
    if "elevated body temperature" in norm_text or "fever" in norm_text:
        features["findings"].add("elevated temperature")

    return features

def apply_hard_rejection_rules(
    query_text: str,
    query_feat: Dict[str, Set[str]],
    candidate: TM2Concept,
    cand_feat: Dict[str, Set[str]]
) -> Tuple[bool, str]:
    """
    Apply hard rejection rules to guarantee clinical safety.
    Returns (is_rejected, reason).
    """
    # Rule E: Functional query protection
    if query_feat["functional"] and not cand_feat["functional"]:
        return True, "Functional query must not map to ordinary disease concept"

    # Rule A: Explicit anatomy conflict
    # E.g. Query has shoulder, candidate has eye/bowel but not shoulder
    if query_feat["anatomy"]:
        for query_anat in query_feat["anatomy"]:
            if cand_feat["anatomy"] and query_anat not in cand_feat["anatomy"]:
                return True, f"Anatomy conflict: query specifies {query_anat} but candidate specifies {cand_feat['anatomy']}"

    # Rule B: Explicit symptom absent from candidate
    # E.g. "burning shoulder" must not map to candidate lacking burning (like Frozen shoulder)
    #
    # Applies uniformly to any symptom in SYMPTOM_VOCAB, not just a
    # hardcoded subset -- a query naming any specific symptom that the
    # candidate shares none of is rejected the same way regardless of
    # which symptom word was used.
    if query_feat["symptoms"]:
        matched_symptoms = query_feat["symptoms"].intersection(cand_feat["symptoms"])
        if not matched_symptoms:
            return True, f"Explicit query symptom {query_feat['symptoms']} missing in candidate {cand_feat['symptoms']}"

    # Rule C: Explicit clinical object absent
    if query_feat["objects"]:
        matched_objects = query_feat["objects"].intersection(cand_feat["objects"])
        # E.g. "loose stools" (object: stool) must not map to "eyelid"
        if not matched_objects:
            return True, f"Explicit clinical object {query_feat['objects']} absent from candidate {cand_feat['objects']}"

    # Rule D: Generic queries must not map to overly specific diseases with extra non-requested specific qualities
    # E.g. Query "eye diseases" (generic) vs Candidate "Dry eye disorder" or "Conjunctivitis"
    query_is_pure_generic = bool(query_feat["anatomy"]) and bool(query_feat["generic"]) and not query_feat["symptoms"] and not query_feat["quality"]
    if query_is_pure_generic:
        # Candidate has specific extra qualities like "dry", "bloodshot", etc.
        # Checked directly against the candidate's own detected quality
        # tags, not a set artificially forced non-empty.
        if cand_feat["quality"] and "eye disorders" not in candidate.title.lower():
            return True, "Generic query preferred broad category concept over specific sub-disease"

    return False, ""

def score_candidate(
    query_feat: Dict[str, Set[str]],
    candidate: TM2Concept,
    cand_feat: Dict[str, Set[str]]
) -> float:
    """
    Deterministic scoring engine based on clinical feature overlap.
    """
    score = 0.0

    anat_overlap = len(query_feat["anatomy"].intersection(cand_feat["anatomy"]))
    symp_overlap = len(query_feat["symptoms"].intersection(cand_feat["symptoms"]))
    qual_overlap = len(query_feat["quality"].intersection(cand_feat["quality"]))
    find_overlap = len(query_feat["findings"].intersection(cand_feat["findings"]))
    obj_overlap = len(query_feat["objects"].intersection(cand_feat["objects"]))
    func_overlap = len(query_feat["functional"].intersection(cand_feat["functional"]))

    # Base category scoring
    if anat_overlap > 0:
        score += 10.0
    if symp_overlap > 0:
        score += 12.0
    if qual_overlap > 0:
        score += 8.0
    if find_overlap > 0:
        score += 6.0
    if obj_overlap > 0:
        score += 12.0
    if func_overlap > 0:
        score += 10.0

    # General meaningful word overlap (excluding generic filler words)
    meaningful_query_words = query_feat["all_words"] - GENERIC_VOCAB - TEMPORAL_CONTEXT_VOCAB
    meaningful_cand_words = cand_feat["all_words"] - GENERIC_VOCAB - TEMPORAL_CONTEXT_VOCAB
    word_overlap = len(meaningful_query_words.intersection(meaningful_cand_words))
    score += (word_overlap * 2.0)

    # Exact agreement bonuses
    if query_feat["anatomy"] and query_feat["anatomy"] == cand_feat["anatomy"]:
        score += 8.0
    if query_feat["symptoms"] and query_feat["symptoms"] == cand_feat["symptoms"]:
        score += 10.0
    if query_feat["objects"] and query_feat["objects"] == cand_feat["objects"]:
        score += 8.0

    # Strong anatomy + symptom agreement bonus
    if anat_overlap > 0 and (symp_overlap > 0 or qual_overlap > 0):
        score += 10.0

    return score

def determine_confidence(score: float, query_feat: Dict[str, Set[str]], cand_feat: Dict[str, Set[str]]) -> str:
    """
    Determine confidence level based on score and clinical feature agreement.
    """
    anat_agree = bool(query_feat["anatomy"].intersection(cand_feat["anatomy"])) if query_feat["anatomy"] else True
    clinical_agree = bool(
        query_feat["symptoms"].intersection(cand_feat["symptoms"]) or
        query_feat["quality"].intersection(cand_feat["quality"]) or
        query_feat["objects"].intersection(cand_feat["objects"])
    )

    if score >= 40.0 and anat_agree and clinical_agree:
        return "HIGH"
    elif score >= 25.0 and clinical_agree:
        return "MEDIUM"
    elif score >= 15.0:
        return "LOW"
    else:
        return "NONE"

def get_mapping_for_concept(concept_or_code: str) -> ConceptMappingResponse:
    """
    Main terminology mapping service function.
    Accepts either a NAMASTE code (e.g. SAT-D.8) or a free-text clinical definition.
    """
    namaste_concept = get_namaste_concept_by_code(concept_or_code)
    
    if namaste_concept:
        query_text = namaste_concept.definition
    else:
        # Build transient NamasteConcept for raw query search
        query_text = concept_or_code
        namaste_concept = NamasteConcept(
            code="CUSTOM",
            display=concept_or_code,
            definition=concept_or_code,
            terminology="SEARCH"
        )

    query_features = extract_clinical_features(query_text)
    tm2_concepts = get_tm2_concepts()
    
    matches: List[CandidateMatch] = []

    for cand in tm2_concepts:
        cand_features = extract_clinical_features(cand.title)
        
        # Check Hard Rejection Rules
        rejected, reason = apply_hard_rejection_rules(query_text, query_features, cand, cand_features)
        if rejected:
            logger.debug(f"Candidate {cand.id} ({cand.title}) rejected: {reason}")
            continue

        score = score_candidate(query_features, cand, cand_features)
        confidence = determine_confidence(score, query_features, cand_features)

        if confidence != "NONE" and score >= 15.0:
            evidence_words = list((query_features["all_words"] - GENERIC_VOCAB - TEMPORAL_CONTEXT_VOCAB).intersection(cand_features["all_words"]))
            evidence = ClinicalEvidence(
                words=sorted(evidence_words),
                anatomy=sorted(list(query_features["anatomy"].intersection(cand_features["anatomy"]))),
                symptoms=sorted(list(query_features["symptoms"].intersection(cand_features["symptoms"]))),
                quality=sorted(list(query_features["quality"].intersection(cand_features["quality"]))),
                findings=sorted(list(query_features["findings"].intersection(cand_features["findings"])))
            )

            matches.append(CandidateMatch(
                tm2_id=cand.id,
                tm2_title=cand.title,
                score=round(score, 1),
                confidence=confidence,
                equivalence="relatedto",
                evidence=evidence
            ))

    # Sort matches by score descending
    matches.sort(key=lambda m: m.score, reverse=True)

    mapping_status = "CANDIDATE_MAPPING" if len(matches) > 0 else "NO_CANDIDATE"

    return ConceptMappingResponse(
        namaste=namaste_concept,
        count=len(matches),
        matches=matches,
        mapping_status=mapping_status,
        note="Algorithm-generated candidate mapping. Not an official WHO or NAMASTE equivalence."
    )
