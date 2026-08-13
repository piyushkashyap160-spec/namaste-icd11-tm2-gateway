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
    "sense organ", "organ", "skin", "joint", "chest", "arm", "leg", "limb", "muscle", "bone", "neck", "throat"
}

# Anatomy groupings: for a query anatomy, list permitted candidate anatomy terms that are clinically
# valid supersets or anatomically-associated regions. This prevents false rejections like
# 'shoulder' (a joint) against 'joint disorders', while still blocking cross-system mismatches.
ANATOMY_COMPATIBLE_GROUPS = {
    "shoulder": {"shoulder", "joint", "muscle", "bone", "arm", "limb"},
    "eye": {"eye", "eyelid"},
    "head": {"head", "skull"},
    "bowel": {"bowel"},
    "joint": {"joint", "shoulder", "arm", "leg", "limb", "bone", "muscle"},
    "muscle": {"muscle", "joint", "shoulder", "arm", "leg"},
    "bone": {"bone", "joint", "muscle"},
}

SYMPTOM_VOCAB = {
    "burning", "pain", "inflammation", "inflammatory", "fever",
    "cough", "headache", "swelling", "churned", "sensation", "discomfort"
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

# Tiered symptom families.
#
# EXACT_SYNONYMS: clinically established synonyms (e.g. pyrexia = fever).
#   Matches here count as a strong clinical agreement, equivalent to an exact match.
#
# RELATED_SYMPTOMS: sensory/quality relatives that share a clinical domain but
#   are NOT equivalent (e.g. burning ≠ inflammation, burning ≠ pain as diseases).
#   Matches here yield only weak/partial evidence and CANNOT on their own
#   produce HIGH confidence.  They do, however, prevent Rule B from hard-rejecting
#   a candidate that is otherwise anatomically consistent.
#
# IMPORTANT: burning is NOT a synonym of inflammation or pain.
# Burning is a sensory quality; pain is a nociceptive symptom; inflammation
# is a pathological process.  They are related concepts, not equivalents.

EXACT_SYNONYMS: Dict[str, Set[str]] = {
    "burning":      {"burning"},
    "pain":         {"pain", "ache"},
    "inflammation": {"inflammation", "inflammatory"},
    "fever":        {"fever", "pyrexia"},
    "headache":     {"headache", "cephalalgia", "migraine"},
    "cough":        {"cough", "coughing"},
    "swelling":     {"swelling", "oedema", "edema"},
}

RELATED_SYMPTOMS: Dict[str, Set[str]] = {
    # burning → pain and heat are related sensory qualities; inflammation is related pathology
    "burning":      {"pain", "sensation", "discomfort", "heat", "inflammation"},
    # pain → burning and discomfort are related but not equivalent
    "pain":         {"burning", "discomfort", "sensation"},
    # inflammation → swelling and redness are related signs but not the symptom itself
    "inflammation": {"swelling", "redness", "burning"},
    "fever":        {"temperature", "elevated temperature"},
    "headache":     set(),
    "cough":        set(),
    "swelling":     {"inflammation"},
}

# Backward-compat alias: flat family = synonyms ∪ related (for Rule B)
CLINICAL_SYMPTOM_FAMILIES: Dict[str, Set[str]] = {
    k: EXACT_SYNONYMS.get(k, {k}) | RELATED_SYMPTOMS.get(k, set())
    for k in set(list(EXACT_SYNONYMS) + list(RELATED_SYMPTOMS))
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
    # We allow anatomically-compatible regions (e.g. shoulder -> joint/muscle accepted)
    if query_feat["anatomy"]:
        for query_anat in query_feat["anatomy"]:
            if cand_feat["anatomy"]:
                compatible = ANATOMY_COMPATIBLE_GROUPS.get(query_anat, {query_anat})
                if not cand_feat["anatomy"].intersection(compatible):
                    return True, f"Anatomy conflict: query specifies {query_anat} but candidate specifies {sorted(cand_feat['anatomy'])}"

    # Rule B: Symptom guard
    #
    # Rejection hierarchy (most to least restrictive):
    #   1. If query has an unmatched "churned" sensation → always reject (no clinical analog)
    #   2. If candidate has an INCOMPATIBLE quality that directly contradicts the query symptom
    #      (e.g. query=burning, candidate has only "frozen") → reject unless anatomy matches exactly
    #      AND another symptom/quality in the candidate is at least a related concept.
    #   3. If NO symptom evidence at all (exact, synonym, related, or quality), AND anatomy is
    #      also absent → reject.
    #
    # Anatomy-compatible match keeps a candidate ALIVE (not rejected) but NEVER substitutes
    # for symptom evidence in scoring or confidence.
    if query_feat["symptoms"]:
        # Categorise matches
        exact_symp_match  = bool(query_feat["symptoms"].intersection(cand_feat["symptoms"]))
        exact_qual_match  = bool(query_feat["symptoms"].intersection(cand_feat["quality"]))

        synonym_match = False
        for q_sym in query_feat["symptoms"]:
            synonyms = EXACT_SYNONYMS.get(q_sym, {q_sym})
            if synonyms.intersection(cand_feat["symptoms"]) or synonyms.intersection(cand_feat["quality"]):
                synonym_match = True
                break

        related_match = False
        for q_sym in query_feat["symptoms"]:
            related = RELATED_SYMPTOMS.get(q_sym, set())
            if related.intersection(cand_feat["symptoms"]) or related.intersection(cand_feat["quality"]):
                related_match = True
                break

        # Hard guard: "churned" sensation has no TM2 equivalent — always reject
        unmatched_churned = bool(query_feat["symptoms"].intersection({"churned"}))
        if unmatched_churned:
            return True, "Churned sensation has no valid TM2 clinical analog"

        # Anatomy coverage
        anatomy_exact_match = bool(
            query_feat["anatomy"] and query_feat["anatomy"].intersection(cand_feat["anatomy"])
        )
        anatomy_compatible_match = False
        for q_anat in query_feat["anatomy"]:
            compatible = ANATOMY_COMPATIBLE_GROUPS.get(q_anat, {q_anat})
            if cand_feat["anatomy"].intersection(compatible):
                anatomy_compatible_match = True
                break
        anatomy_covered = anatomy_exact_match or anatomy_compatible_match

        # Incompatibility check: candidate has a quality that DIRECTLY conflicts with
        # the query symptom (e.g. burning vs frozen).  Only reject if anatomy also
        # doesn't match exactly or there is no related symptom evidence at all.
        conflicting_qualities = {
            "burning": {"frozen", "cold", "icy"},
            "fever":   {"frozen", "cold"},
        }
        has_conflict = False
        for q_sym in query_feat["symptoms"]:
            conflicts = conflicting_qualities.get(q_sym, set())
            if conflicts.intersection(cand_feat["quality"]):
                # Conflict found — only hard-reject when anatomy doesn't help AND
                # there is no related symptom at all
                if not anatomy_exact_match:
                    has_conflict = True
                break

        any_symptom_evidence = (
            exact_symp_match or exact_qual_match or synonym_match or related_match
        )

        if has_conflict and not any_symptom_evidence:
            return (
                True,
                f"Symptom conflict: query={sorted(query_feat['symptoms'])} "
                f"incompatible with candidate quality={sorted(cand_feat['quality'])}",
            )

        # Final gate: if there is neither symptom evidence NOR anatomy coverage → reject
        if not any_symptom_evidence and not anatomy_covered:
            return (
                True,
                f"No symptom evidence and no anatomy coverage: "
                f"query_symptoms={sorted(query_feat['symptoms'])} "
                f"cand_symptoms={sorted(cand_feat['symptoms'])}",
            )

    # Rule C: Explicit clinical object absent
    # Only apply when query anatomy is NOT matched - anatomy match already validates the site
    if query_feat["objects"]:
        matched_objects = query_feat["objects"].intersection(cand_feat["objects"])
        anatomy_covered = False
        for q_anat in query_feat["anatomy"]:
            compatible = ANATOMY_COMPATIBLE_GROUPS.get(q_anat, {q_anat})
            if cand_feat["anatomy"].intersection(compatible):
                anatomy_covered = True
                break
        # Only reject on object mismatch when anatomy isn't covered
        if not matched_objects and not anatomy_covered:
            return True, f"Explicit clinical object {query_feat['objects']} absent from candidate {cand_feat['objects']}"

    # Rule D: Generic queries must not map to overly specific diseases with extra non-requested specific qualities
    query_is_pure_generic = bool(query_feat["anatomy"]) and bool(query_feat["generic"]) and not query_feat["symptoms"] and not query_feat["quality"]
    if query_is_pure_generic:
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

    Scoring philosophy:
    - Exact anatomy match:       10 pts
    - Compatible anatomy match:   4 pts  (partial — shoulder→joint)
    - Exact symptom match:       12 pts
    - Exact quality match:        8 pts
    - Synonym symptom match:      7 pts  (e.g. pain≈ache)
    - Related symptom match:      3 pts  (e.g. burning→inflammation, weak signal)
    - Exact object match:        12 pts
    - Meaningful word overlap:    2 pts each
    - Exact anatomy set bonus:    6 pts  (sets are identical)
    - Exact symptom set bonus:    8 pts  (sets are identical)
    - Exact object set bonus:     6 pts
    - Strong combined bonus:     10 pts  (exact anatomy AND exact symptom/quality)

    Note: anatomy-compatible match alone CANNOT produce a strong score.
    Note: a related-symptom match alone contributes only 3 pts — far from HIGH threshold.
    """
    score = 0.0

    anat_overlap = len(query_feat["anatomy"].intersection(cand_feat["anatomy"]))
    symp_overlap = len(query_feat["symptoms"].intersection(cand_feat["symptoms"]))
    qual_overlap = len(query_feat["quality"].intersection(cand_feat["quality"]))
    find_overlap = len(query_feat["findings"].intersection(cand_feat["findings"]))
    obj_overlap  = len(query_feat["objects"].intersection(cand_feat["objects"]))
    func_overlap = len(query_feat["functional"].intersection(cand_feat["functional"]))

    # Anatomy-compatible (partial) match when exact anatomy is absent
    anat_compatible_overlap = 0
    if query_feat["anatomy"] and not anat_overlap:
        for q_anat in query_feat["anatomy"]:
            compatible = ANATOMY_COMPATIBLE_GROUPS.get(q_anat, {q_anat})
            if cand_feat["anatomy"].intersection(compatible):
                anat_compatible_overlap += 1

    # Symptom synonym match (strong — same clinical meaning)
    synonym_symp_overlap = 0
    if query_feat["symptoms"] and not symp_overlap:
        for q_sym in query_feat["symptoms"]:
            synonyms = EXACT_SYNONYMS.get(q_sym, {q_sym})
            if (synonyms - {q_sym}).intersection(cand_feat["symptoms"]) or \
               (synonyms - {q_sym}).intersection(cand_feat["quality"]):
                synonym_symp_overlap += 1

    # Symptom related match (weak — related concept, not equivalent)
    related_symp_overlap = 0
    if query_feat["symptoms"] and not symp_overlap and not synonym_symp_overlap:
        for q_sym in query_feat["symptoms"]:
            related = RELATED_SYMPTOMS.get(q_sym, set())
            if related.intersection(cand_feat["symptoms"]) or related.intersection(cand_feat["quality"]):
                related_symp_overlap += 1

    # ── Base scoring ──────────────────────────────────────────────────────────
    if anat_overlap > 0:
        score += 10.0
    elif anat_compatible_overlap > 0:
        score += 4.0          # Partial — compatible anatomy, not exact

    if symp_overlap > 0:
        score += 12.0
    elif synonym_symp_overlap > 0:
        score += 7.0          # Synonym — strong but not exact
    elif related_symp_overlap > 0:
        score += 3.0          # Related — weak signal only

    if qual_overlap > 0:
        score += 8.0
    if find_overlap > 0:
        score += 6.0
    if obj_overlap > 0:
        score += 12.0
    if func_overlap > 0:
        score += 10.0

    # Meaningful word overlap (token-level, minus stopwords)
    meaningful_query = query_feat["all_words"] - GENERIC_VOCAB - TEMPORAL_CONTEXT_VOCAB
    meaningful_cand  = cand_feat["all_words"]  - GENERIC_VOCAB - TEMPORAL_CONTEXT_VOCAB
    word_overlap = len(meaningful_query.intersection(meaningful_cand))
    score += word_overlap * 2.0

    # ── Exact-set agreement bonuses ───────────────────────────────────────────
    if query_feat["anatomy"] and query_feat["anatomy"] == cand_feat["anatomy"]:
        score += 6.0
    if query_feat["symptoms"] and query_feat["symptoms"] == cand_feat["symptoms"]:
        score += 8.0
    if query_feat["objects"] and query_feat["objects"] == cand_feat["objects"]:
        score += 6.0

    # Strong combined bonus: exact anatomy AND exact symptom/quality agreement
    # (requires real clinical agreement — compatible anatomy alone does NOT trigger this)
    if anat_overlap > 0 and (symp_overlap > 0 or qual_overlap > 0):
        score += 10.0

    return score


def determine_confidence(
    score: float,
    query_feat: Dict[str, Set[str]],
    cand_feat: Dict[str, Set[str]],
) -> str:
    """
    Confidence calibration — conservative by design.

    HIGH:   Requires exact anatomy match AND (exact symptom OR exact quality) match.
            Score threshold ≥ 40.  A broad symptom-family match is insufficient.
    MEDIUM: Requires exact anatomy match AND synonym-level symptom agreement,
            OR exact symptom with at least compatible anatomy.
            Score threshold ≥ 22.
    LOW:    Anatomy-only match (symptom absent from candidate), or related-symptom
            only, or compatible (non-exact) anatomy with synonym symptom.
            Score threshold ≥ 12.
    NONE:   Below threshold — not included in results.

    Key rules:
    - Anatomy-compatible match (shoulder→joint) alone → caps at LOW
    - Anatomy exact + symptom absent (e.g. SP15 Frozen shoulder for burning) → LOW
    - Related symptom only (burning→inflammation) → caps at LOW
    - Synonym symptom + exact anatomy → MEDIUM
    - Exact symptom + exact anatomy → HIGH (if score ≥ 40)
    """
    # Anatomy agreement tier
    exact_anat = (
        bool(query_feat["anatomy"].intersection(cand_feat["anatomy"]))
        if query_feat["anatomy"] else True
    )
    compatible_anat = False
    if not exact_anat and query_feat["anatomy"]:
        for q_anat in query_feat["anatomy"]:
            compat = ANATOMY_COMPATIBLE_GROUPS.get(q_anat, {q_anat})
            if cand_feat["anatomy"].intersection(compat):
                compatible_anat = True
                break

    # Symptom agreement tier
    # NOTE: object overlap (e.g. shoulder in query AND candidate) validates the clinical
    # SITE but is NOT evidence of symptom equivalence.  It must not elevate confidence
    # to MEDIUM/HIGH on its own.
    exact_symp = bool(
        query_feat["symptoms"].intersection(cand_feat["symptoms"]) or
        query_feat["quality"].intersection(cand_feat["quality"])
        # objects intentionally excluded from exact_symp
    )
    # Site match: query and candidate share an explicit anatomical object (e.g. shoulder)
    exact_site = bool(query_feat["objects"].intersection(cand_feat["objects"]))

    synonym_symp = False
    if not exact_symp:
        for q_sym in query_feat["symptoms"]:
            synonyms = EXACT_SYNONYMS.get(q_sym, {q_sym})
            if (synonyms - {q_sym}).intersection(cand_feat["symptoms"]) or \
               (synonyms - {q_sym}).intersection(cand_feat["quality"]):
                synonym_symp = True
                break

    related_symp = False
    if not exact_symp and not synonym_symp:
        for q_sym in query_feat["symptoms"]:
            related = RELATED_SYMPTOMS.get(q_sym, set())
            if related.intersection(cand_feat["symptoms"]) or related.intersection(cand_feat["quality"]):
                related_symp = True
                break

    # ── Confidence ladder ─────────────────────────────────────────────────────
    # HIGH: exact anatomy AND exact symptom/quality evidence, score ≥ 40
    # Object (site) overlap alone is NOT sufficient for HIGH.
    if score >= 40.0 and exact_anat and exact_symp:
        return "HIGH"

    # MEDIUM: exact anatomy + synonym symptom (strong synonym, not broad family)
    if score >= 22.0 and exact_anat and synonym_symp:
        return "MEDIUM"
    # MEDIUM: exact symptom evidence + at least compatible anatomy
    if score >= 22.0 and exact_symp and (exact_anat or compatible_anat):
        return "MEDIUM"

    # LOW: anatomy coverage (exact or compatible) with any symptom signal, OR anatomy-only
    # This includes the clinically defensible-but-uncertain cases such as:
    #   - exact anatomy + symptom absent from candidate (different phenotype)
    #   - compatible anatomy + synonym symptom
    #   - related symptom only (weak signal)
    if score >= 12.0 and (exact_anat or compatible_anat):
        return "LOW"
    if score >= 12.0 and related_symp:
        return "LOW"

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
                tm2_code=cand.code,
                tm2_title=cand.title,
                tm2_system=cand.system,
                tm2_version=cand.version,
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
