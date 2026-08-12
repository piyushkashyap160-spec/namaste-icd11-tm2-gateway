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


def test_sat_d_8_burning_in_shoulder():
    response = get_mapping_for_concept("SAT-D.8")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.count > 0
    top_match = response.matches[0]
    assert top_match.tm2_id == "1564853364"
    assert "Burning sensation of shoulder" in top_match.tm2_title
    assert top_match.confidence == "HIGH"

def test_sat_d_51_loose_stools_temporal_modifier():
    response = get_mapping_for_concept("SAT-D.51")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.count > 0
    top_match = response.matches[0]
    assert top_match.tm2_id == "4482910384"
    assert "Loose stool" in top_match.tm2_title
    # Verify temporal 'sudden' did not reject valid match

def test_generic_eye_disease_query():
    response = get_mapping_for_concept("SAT-D.12")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    top_match = response.matches[0]
    # Expect broad category Eye disorders (TM2)
    assert top_match.tm2_id == "1249767098"

def test_eye_inflammation_not_bowel():
    response = get_mapping_for_concept("SAT-D.14")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    top_match = response.matches[0]
    assert top_match.tm2_id == "1874623910"
    # Ensure bowel candidate (3301928472) is not returned
    match_ids = [m.tm2_id for m in response.matches]
    assert "3301928472" not in match_ids

def test_functional_query_returns_no_candidate():
    response = get_mapping_for_concept("SAT-D.60")
    assert response.mapping_status == "NO_CANDIDATE"
    assert response.count == 0
    assert len(response.matches) == 0

def test_unmatched_shoulder_churning_returns_no_candidate():
    response = get_mapping_for_concept("SAT-D.99")
    assert response.mapping_status == "NO_CANDIDATE"
    assert response.count == 0
    # Must NOT force match Frozen shoulder disorder
    match_ids = [m.tm2_id for m in response.matches]
    assert "2201948271" not in match_ids


def test_arm_token_does_not_match_warmth():
    response = get_mapping_for_concept("arm")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    match_ids = [m.tm2_id for m in response.matches]
    assert "6666666666" in match_ids
    assert all("warmth" not in m.tm2_title.lower() for m in response.matches)


def test_legitimate_phrase_matching_eye_disorders():
    response = get_mapping_for_concept("eye disorders")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.matches[0].tm2_id == "1249767098"


def test_symptom_matching_burning_is_consistent():
    response = get_mapping_for_concept("burning eye")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.matches[0].tm2_id == "7777777777"
    assert "burning" in response.matches[0].tm2_title.lower()
    assert "warmth" not in response.matches[0].tm2_title.lower()


def test_anatomy_matching_should_not_return_bowel_for_eye_inflammation():
    response = get_mapping_for_concept("inflammation of eyes")
    assert response.mapping_status == "CANDIDATE_MAPPING"
    assert response.matches[0].tm2_id == "1874623910"
    assert "3301928472" not in [m.tm2_id for m in response.matches]


def test_no_candidate_for_unmatched_hard_rejection():
    response = get_mapping_for_concept("burning bowel")
    assert response.mapping_status == "NO_CANDIDATE"


def test_evidence_generation_includes_matching_words():
    response = get_mapping_for_concept("burning shoulder")
    evidence = response.matches[0].evidence
    assert "burning" in evidence.words
    assert "shoulder" in evidence.anatomy or "shoulder" in evidence.words
