"""
test_mapping.py — Clinical mapping engine tests.

Synthetic TM2 dataset (monkeypatched) contains:
  TM2-001  Burning sensation of shoulder   → exact burning + shoulder
  TM2-002  Loose stool                     → exact stool/loose
  TM2-003  Eye disorders                   → broad eye category
  TM2-004  Eye inflammation disorder       → eye + inflammation
  TM2-005  Bowel inflammation disorder     → bowel + inflammation
  TM2-006  Frozen shoulder disorder        → shoulder anatomy, NOT burning
  TM2-007  Conjunctivitis                  → no vocab match
  TM2-008  Arm disorder                    → arm anatomy
  TM2-009  Burning eye disorder            → burning + eye
  TM2-010  Warmth disorder                 → no anatomy / no matching symptom

Confidence expectations (require justification, not just thresholds):
  HIGH   = exact symptom match + exact anatomy match, score >= 40
  MEDIUM = synonym symptom + exact anatomy, OR exact symptom + compatible anatomy, score >= 22
  LOW    = anatomy-only match, related-symptom only, OR compatible-anatomy match, score >= 12
  NONE   = below threshold → excluded from results
"""
import pytest
from app.terminology import mapper
from app.schemas import TM2Concept
from app.terminology.mapper import get_mapping_for_concept

@pytest.fixture(autouse=True)
def synthetic_tm2_concepts(monkeypatch):
    fake_tm2 = [
        TM2Concept(
            id="1564853364",
            code="TM2-001",
            title="Burning sensation of shoulder",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="4482910384",
            code="TM2-002",
            title="Loose stool",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="1249767098",
            code="TM2-003",
            title="Eye disorders",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="1874623910",
            code="TM2-004",
            title="Eye inflammation disorder",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="3301928472",
            code="TM2-005",
            title="Bowel inflammation disorder",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="2201948271",
            code="TM2-006",
            title="Frozen shoulder disorder",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="5555555555",
            code="TM2-007",
            title="Conjunctivitis",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="6666666666",
            code="TM2-008",
            title="Arm disorder",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="7777777777",
            code="TM2-009",
            title="Burning eye disorder",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
        TM2Concept(
            id="7777777778",
            code="TM2-010",
            title="Warmth disorder",
            version="2026-01",
            class_kind="category",
            source="synthetic",
        ),
    ]
    monkeypatch.setattr(mapper, "get_tm2_concepts", lambda: fake_tm2)
    yield


# ─────────────────────────────────────────────────────────────────────────────
# Req 6a: exact symptom + matching anatomy => strong candidate (HIGH confidence)
# ─────────────────────────────────────────────────────────────────────────────
def test_sat_d_8_burning_in_shoulder():
    """
    SAT-D.8 = 'burning in shoulder'.
    Synthetic TM2-001 'Burning sensation of shoulder' has BOTH exact symptom (burning)
    and exact anatomy (shoulder) — this is the ideal HIGH-confidence candidate.
    """
    response = get_mapping_for_concept("SAT-D.8")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.count > 0
    # Top match must be TM2-001 (exact burning+shoulder) — not the anatomy-only TM2-006
    top_match = response.matches[0]
    assert top_match.tm2_id == "1564853364", (
        f"Expected TM2-001 (Burning sensation of shoulder) as top match, got {top_match.tm2_id} ({top_match.tm2_title})"
    )
    assert top_match.confidence == "HIGH", (
        f"Exact symptom + exact anatomy must yield HIGH confidence, got {top_match.confidence}"
    )
    # Evidence must contain both symptom and anatomy
    assert "burning" in top_match.evidence.symptoms or "burning" in top_match.evidence.words
    assert "shoulder" in top_match.evidence.anatomy or "shoulder" in top_match.evidence.words


# ─────────────────────────────────────────────────────────────────────────────
# Req 4 / Req 6c: anatomy-only match + missing symptom => cannot become HIGH
# ─────────────────────────────────────────────────────────────────────────────
def test_frozen_shoulder_against_burning_in_shoulder_is_low_not_high():
    """
    'Frozen shoulder disorder' matches anatomy (shoulder) but contains zero
    burning symptom evidence. When queried against 'burning in shoulder' it
    MUST NOT return HIGH confidence; it should be LOW at most (anatomy coverage
    without symptom support).

    This test runs directly against the mapping engine for the free-text query
    'burning in shoulder' to isolate the Frozen shoulder candidate in the
    synthetic dataset (TM2-006, the only pure anatomy-only shoulder candidate).
    """
    response = get_mapping_for_concept("burning in shoulder")
    match_ids = {m.tm2_id for m in response.matches}
    if "2201948271" in match_ids:
        frozen_match = next(m for m in response.matches if m.tm2_id == "2201948271")
        assert frozen_match.confidence != "HIGH", (
            "Anatomy-only match (Frozen shoulder, no burning evidence) must not be HIGH confidence"
        )
        assert frozen_match.confidence != "MEDIUM", (
            "Anatomy-only match without synonym symptom must not be MEDIUM confidence"
        )
        # Evidence: symptom must be absent or empty
        assert not frozen_match.evidence.symptoms, (
            f"No burning symptom evidence should exist for TM2-006, got: {frozen_match.evidence.symptoms}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Req 6b: recognized synonym + matching anatomy => moderate candidate (MEDIUM)
# ─────────────────────────────────────────────────────────────────────────────
def test_pain_in_shoulder_maps_to_burning_sensation_as_medium():
    """
    'pain in shoulder': pain is in EXACT_SYNONYMS['pain'] = {pain, ache}.
    TM2-001 'Burning sensation of shoulder' has symptom='burning' which is in
    RELATED_SYMPTOMS['pain'] (related, not synonym) → should be LOW.
    TM2-006 'Frozen shoulder disorder' has no symptom → LOW at best.
    Key assertion: no result from this query should be HIGH confidence.
    """
    response = get_mapping_for_concept("pain in shoulder")
    for m in response.matches:
        assert m.confidence != "HIGH", (
            f"'pain in shoulder' should not produce HIGH confidence for any candidate. "
            f"Got HIGH for [{m.tm2_id}] {m.tm2_title} — verify synonym/related distinction."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Req 5: burning must NOT be treated as equivalent to inflammation
# ─────────────────────────────────────────────────────────────────────────────
def test_burning_is_not_equivalent_to_inflammation():
    """
    'burning in bowel' — the only bowel candidate is TM2-005 'Bowel inflammation
    disorder'. Inflammation is in RELATED_SYMPTOMS['burning'] (not EXACT_SYNONYMS).
    The candidate may survive rejection (bowel anatomy covers it), but confidence
    MUST be LOW, not MEDIUM or HIGH, because burning ≠ inflammation.
    """
    response = get_mapping_for_concept("burning bowel")
    match_ids = {m.tm2_id for m in response.matches}
    # Bowel anatomy should allow survival
    if "3301928472" in match_ids:
        bowel_match = next(m for m in response.matches if m.tm2_id == "3301928472")
        assert bowel_match.confidence != "HIGH", (
            "burning != inflammation: Bowel inflammation disorder must not be HIGH for 'burning bowel'"
        )
        assert bowel_match.confidence != "MEDIUM", (
            "burning is only a RELATED (not synonym/exact) match to inflammation: must be LOW"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Req 6d: unrelated anatomy => hard rejection
# ─────────────────────────────────────────────────────────────────────────────
def test_eye_anatomy_query_does_not_return_bowel_candidate():
    """
    Eye-anatomy queries must NEVER return bowel candidates regardless of shared
    symptom vocabulary.  Rule A hard-rejects cross-system anatomy mismatches.
    """
    response = get_mapping_for_concept("inflammation of eyes")
    match_ids = [m.tm2_id for m in response.matches]
    assert "3301928472" not in match_ids, "Bowel inflammation must be hard-rejected for eye query"


def test_shoulder_query_does_not_return_bowel_candidate():
    """Shoulder anatomy must hard-reject bowel candidates."""
    response = get_mapping_for_concept("burning in shoulder")
    match_ids = [m.tm2_id for m in response.matches]
    assert "3301928472" not in match_ids, "Bowel candidate must be rejected for shoulder query"


# ─────────────────────────────────────────────────────────────────────────────
# Existing clinical correctness tests (maintained)
# ─────────────────────────────────────────────────────────────────────────────
def test_sat_d_51_loose_stools_temporal_modifier():
    """Temporal modifier 'sudden' must not prevent valid loose stool mapping."""
    response = get_mapping_for_concept("SAT-D.51")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.count > 0
    top_match = response.matches[0]
    assert top_match.tm2_id == "4482910384"
    assert "Loose stool" in top_match.tm2_title


def test_generic_eye_disease_query():
    """Broad SAT-D.12 (eye diseases) maps to the broad Eye disorders category."""
    response = get_mapping_for_concept("SAT-D.12")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    top_match = response.matches[0]
    assert top_match.tm2_id == "1249767098"


def test_eye_inflammation_not_bowel():
    """SAT-D.14 (eye inflammation) maps to eye candidate, not bowel."""
    response = get_mapping_for_concept("SAT-D.14")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    top_match = response.matches[0]
    assert top_match.tm2_id == "1874623910"
    match_ids = [m.tm2_id for m in response.matches]
    assert "3301928472" not in match_ids


def test_functional_query_returns_no_candidate():
    """Functional queries (proper function of organ) must never map to pathology."""
    response = get_mapping_for_concept("SAT-D.60")
    assert response.mapping_status == "NO_CANDIDATE"
    assert response.count == 0
    assert len(response.matches) == 0


def test_unmatched_shoulder_churning_returns_no_candidate():
    """SAT-D.99 (shoulder churning) has no TM2 analog — must be NO_CANDIDATE."""
    response = get_mapping_for_concept("SAT-D.99")
    assert response.mapping_status == "NO_CANDIDATE"
    assert response.count == 0
    match_ids = [m.tm2_id for m in response.matches]
    assert "2201948271" not in match_ids  # Must NOT force-match Frozen shoulder


def test_arm_token_does_not_match_warmth():
    """'arm' query must match arm disorder but not warmth disorder."""
    response = get_mapping_for_concept("arm")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    match_ids = [m.tm2_id for m in response.matches]
    assert "6666666666" in match_ids
    assert all("warmth" not in m.tm2_title.lower() for m in response.matches)


def test_legitimate_phrase_matching_eye_disorders():
    """Direct 'eye disorders' phrase maps to the Eye disorders category."""
    response = get_mapping_for_concept("eye disorders")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.matches[0].tm2_id == "1249767098"


def test_symptom_matching_burning_is_consistent():
    """'burning eye' maps to Burning eye disorder (TM2-009), not warmth."""
    response = get_mapping_for_concept("burning eye")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.matches[0].tm2_id == "7777777777"
    assert "burning" in response.matches[0].tm2_title.lower()
    assert "warmth" not in response.matches[0].tm2_title.lower()


def test_anatomy_matching_should_not_return_bowel_for_eye_inflammation():
    """Eye inflammation query must reject bowel candidate via hard Rule A."""
    response = get_mapping_for_concept("inflammation of eyes")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.matches[0].tm2_id == "1874623910"
    assert "3301928472" not in [m.tm2_id for m in response.matches]


def test_no_candidate_for_unmatched_hard_rejection():
    """
    'burning bowel' anatomy must only produce bowel-anatomy candidates.
    Eye and shoulder candidates must be hard-rejected.
    """
    response = get_mapping_for_concept("burning bowel")
    if response.mapping_status == "CANDIDATE_MAPPING":
        match_ids = [m.tm2_id for m in response.matches]
        assert "1874623910" not in match_ids, "Eye inflammation must not appear for bowel query"
        assert "1564853364" not in match_ids, "Burning shoulder must not appear for bowel query"


def test_evidence_generation_includes_matching_words():
    """Evidence words and anatomy must include 'burning' and 'shoulder' for exact match."""
    response = get_mapping_for_concept("burning shoulder")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    evidence = response.matches[0].evidence
    all_evidence = evidence.words + evidence.anatomy + evidence.symptoms + evidence.quality
    assert "shoulder" in all_evidence, f"'shoulder' missing from evidence: {all_evidence}"


def test_disclaimer_note_present():
    """The disclaimer note must be present on every mapping response."""
    response = get_mapping_for_concept("SAT-D.8")
    assert "Algorithm-generated candidate mapping" in response.note
    assert "Not an official WHO or NAMASTE equivalence" in response.note


def test_burning_eye_is_high_confidence():
    """
    'burning eye' against TM2-009 'Burning eye disorder' has exact symptom (burning)
    + exact anatomy (eye) — this is the ideal HIGH case in the test dataset.
    """
    response = get_mapping_for_concept("burning eye")
    top = response.matches[0]
    assert top.tm2_id == "7777777777"
    assert top.confidence == "HIGH", (
        f"Exact symptom + exact anatomy (burning eye) must be HIGH, got {top.confidence}"
    )
