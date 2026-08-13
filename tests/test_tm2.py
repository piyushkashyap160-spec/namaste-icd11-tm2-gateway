"""
Unit tests for app.terminology.tm2.

These tests mock the WHO client entirely via app.terminology.tm2._get_who_client
and never touch the live WHO API. A small synthetic hierarchy is used instead
of the real ~650-entity TM2 tree, specifically including:

  - a plain block -> category chain
  - a category with no code (must be excluded)
  - a block with no code (must be excluded)
  - a leaf referenced from two different parents (multi-parent dedup)
  - a block with a real {id}/other and {id}/unspecified residual pair

This suite exists specifically to lock down the residual-URI fix (the
".../mms/other" 404 regression encountered during development) so a future
change to _entity_id() or _walk_tm2_entity() cannot silently reintroduce it.
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict
from unittest.mock import patch

import pytest

from app.terminology import tm2


RELEASE = tm2.WHO_RELEASE

CHAPTER_26 = tm2.WHO_CHAPTER_26_ID
MODULE_II = tm2.WHO_MODULE_II_ID
DISORDERS_ROOT = tm2.WHO_TM2_DISORDERS_ID
PATTERNS_ROOT = tm2.WHO_TM2_PATTERNS_ID

BLOCK_A = "9000000001"          # block, no code -> not codable, traversed
CATEGORY_A = "9000000002"       # category, has code -> codable
BLOCK_NO_CODE_LEAF = "9000000003"  # block, no code, no children -> excluded
RESIDUAL_PARENT = "9000000004"  # block with /other and /unspecified children
SHARED_LEAF = "9000000005"      # category, referenced from both TM2 roots


def _title(value: str):
    return {"@language": "en", "@value": value}


def _uri(entity_id: str) -> str:
    return f"http://id.who.int/icd/release/11/{RELEASE}/mms/{entity_id}"


def _build_entities() -> Dict[str, dict]:
    return {
        CHAPTER_26: {
            "@id": _uri(CHAPTER_26),
            "code": "26",
            "title": _title("Supplementary Chapter Traditional Medicine Conditions"),
            "classKind": "chapter",
            "child": [_uri(MODULE_II)],
        },
        MODULE_II: {
            "@id": _uri(MODULE_II),
            "title": _title("Module II"),
            "classKind": "block",
            "parent": [_uri(CHAPTER_26)],
            "child": [_uri(DISORDERS_ROOT), _uri(PATTERNS_ROOT)],
        },
        DISORDERS_ROOT: {
            "@id": _uri(DISORDERS_ROOT),
            "title": _title("Traditional medicine disorders (TM2)"),
            "classKind": "block",
            "child": [
                _uri(BLOCK_A),
                _uri(RESIDUAL_PARENT),
                _uri(SHARED_LEAF),
            ],
        },
        PATTERNS_ROOT: {
            "@id": _uri(PATTERNS_ROOT),
            "title": _title("Traditional medicine patterns (TM2)"),
            "classKind": "block",
            "child": [_uri(SHARED_LEAF)],
        },
        BLOCK_A: {
            "@id": _uri(BLOCK_A),
            "title": _title("A structural grouping block"),
            "classKind": "block",
            "child": [_uri(CATEGORY_A), _uri(BLOCK_NO_CODE_LEAF)],
        },
        CATEGORY_A: {
            "@id": _uri(CATEGORY_A),
            "code": "SA01",
            "title": _title("Some disorder (TM2)"),
            "classKind": "category",
            "source": "http://id.who.int/icd/entity/9000000002",
            "child": [],
        },
        BLOCK_NO_CODE_LEAF: {
            "@id": _uri(BLOCK_NO_CODE_LEAF),
            "title": _title("A leaf block with no code"),
            "classKind": "block",
            "child": [],
        },
        RESIDUAL_PARENT: {
            "@id": _uri(RESIDUAL_PARENT),
            "title": _title("Some grouping with residuals (TM2)"),
            "classKind": "block",
            "child": [
                f"{_uri(RESIDUAL_PARENT)}/other",
                f"{_uri(RESIDUAL_PARENT)}/unspecified",
            ],
        },
        f"{RESIDUAL_PARENT}/other": {
            "@id": f"{_uri(RESIDUAL_PARENT)}/other",
            "code": "SX0Y",
            "title": _title("Other specified grouping with residuals (TM2)"),
            "classKind": "category",
            "child": [],
        },
        f"{RESIDUAL_PARENT}/unspecified": {
            "@id": f"{_uri(RESIDUAL_PARENT)}/unspecified",
            "code": "SX0Z",
            "title": _title("Grouping with residuals (TM2), unspecified"),
            "classKind": "category",
            "child": [],
        },
        SHARED_LEAF: {
            "@id": _uri(SHARED_LEAF),
            "code": "SM99",
            "title": _title("Shared multi-parented disorder (TM2)"),
            "classKind": "category",
            "source": "http://id.who.int/icd/entity/9000000005",
            "child": [],
        },
    }


class FakeWHOClient:
    """Minimal stand-in for who_icd_client, driven by a path->entity dict."""

    def __init__(self, entities: Dict[str, dict]):
        self.entities = entities
        self.calls: list[str] = []

    def get(self, path: str) -> dict:
        self.calls.append(path)
        entity_id = path.rstrip("/").split("/mms/", 1)[-1]
        try:
            return self.entities[entity_id]
        except KeyError as exc:
            raise KeyError(f"FakeWHOClient has no entity for path {path!r}") from exc


@pytest.fixture(autouse=True)
def reset_tm2_cache(tmp_path, monkeypatch):
    """Every test starts and ends with a clean module-level cache and isolated cache path."""
    monkeypatch.setattr(tm2, "WHO_CACHE_PATH", tmp_path / "test_who_cache.json")
    tm2.clear_tm2_cache()
    yield
    tm2.clear_tm2_cache()


@pytest.fixture
def fake_client():
    return FakeWHOClient(_build_entities())


def patched_client(client):
    return patch.object(tm2, "_get_who_client", return_value=client)


# ---------------------------------------------------------------------------
# 1-3. Entity ID / URI parsing: normal, /other, /unspecified
# ---------------------------------------------------------------------------

def test_entity_id_parses_normal_numeric_uri():
    assert tm2._entity_id(_uri(CATEGORY_A)) == CATEGORY_A


def test_entity_id_parses_other_residual_uri():
    uri = f"{_uri(RESIDUAL_PARENT)}/other"
    assert tm2._entity_id(uri) == f"{RESIDUAL_PARENT}/other"


def test_entity_id_parses_unspecified_residual_uri():
    uri = f"{_uri(RESIDUAL_PARENT)}/unspecified"
    assert tm2._entity_id(uri) == f"{RESIDUAL_PARENT}/unspecified"


def test_entity_id_does_not_collapse_residual_to_bare_word():
    """
    Regression guard: this is exactly the bug that produced the
    '.../mms/other' 404. A residual URI must never resolve to just
    "other" or "unspecified" on their own.
    """
    uri = f"{_uri(RESIDUAL_PARENT)}/other"
    result = tm2._entity_id(uri)
    assert result != "other"
    assert "/" in result


def test_entity_id_handles_non_string_input():
    assert tm2._entity_id(None) == ""
    assert tm2._entity_id(123) == ""
    assert tm2._entity_id({"@id": "not-a-plain-string"}) == ""


# ---------------------------------------------------------------------------
# 6. Title normalization
# ---------------------------------------------------------------------------

def test_title_value_unwraps_language_tagged_dict():
    assert tm2._title_value(_title("Stomatitis disorder (TM2)")) == "Stomatitis disorder (TM2)"


def test_title_value_handles_plain_string():
    assert tm2._title_value("Already a string") == "Already a string"


def test_title_value_handles_none():
    assert tm2._title_value(None) == ""


def test_title_value_handles_missing_value_key():
    assert tm2._title_value({"@language": "en"}) == ""


# ---------------------------------------------------------------------------
# 4-5. classKind/category filtering, coded vs non-coded
# ---------------------------------------------------------------------------

def test_walk_includes_category_with_code(fake_client):
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(fake_client, CATEGORY_A, concepts, visited)
    assert len(concepts) == 1
    assert concepts[0].id == CATEGORY_A
    assert concepts[0].code == "SA01"
    assert concepts[0].class_kind == "category"


def test_walk_excludes_block_regardless_of_code_absence(fake_client):
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(fake_client, BLOCK_NO_CODE_LEAF, concepts, visited)
    assert concepts == []


def test_walk_excludes_structural_block_itself_but_traverses_into_it(fake_client):
    """BLOCK_A has classKind=block (no code) but its child CATEGORY_A is codable."""
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(fake_client, BLOCK_A, concepts, visited)
    ids = {c.id for c in concepts}
    assert BLOCK_A not in ids
    assert CATEGORY_A in ids
    assert BLOCK_NO_CODE_LEAF not in ids


# ---------------------------------------------------------------------------
# 7-8. Entity URI vs Foundation/source URI, release/version
# ---------------------------------------------------------------------------

def test_walk_preserves_entity_uri_and_foundation_uri_separately(fake_client):
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(fake_client, CATEGORY_A, concepts, visited)
    concept = concepts[0]
    assert concept.entity_uri == _uri(CATEGORY_A)
    assert concept.foundation_uri == "http://id.who.int/icd/entity/9000000002"
    assert concept.entity_uri != concept.foundation_uri


def test_walk_sets_foundation_uri_none_when_source_absent(fake_client):
    """
    Residual categories are not part of the Foundation, so a missing
    'source' field must not crash or synthesize a fake value.
    """
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(
        fake_client, f"{RESIDUAL_PARENT}/other", concepts, visited
    )
    assert concepts[0].foundation_uri is None


def test_walk_sets_canonical_system_and_release_version(fake_client):
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(fake_client, CATEGORY_A, concepts, visited)
    concept = concepts[0]
    assert concept.system == tm2.WHO_MMS_SYSTEM
    assert concept.system == "http://id.who.int/icd/release/11/mms"
    assert concept.version == RELEASE


# ---------------------------------------------------------------------------
# 10-11. Recursive traversal, multi-parent / duplicate references
# ---------------------------------------------------------------------------

def test_walk_recurses_into_nested_blocks(fake_client):
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(fake_client, DISORDERS_ROOT, concepts, visited)
    ids = {c.id for c in concepts}
    assert CATEGORY_A in ids
    assert f"{RESIDUAL_PARENT}/other" in ids
    assert f"{RESIDUAL_PARENT}/unspecified" in ids


def test_walk_does_not_refetch_already_visited_entity(fake_client):
    """Visiting the same entity twice must not trigger a second HTTP call."""
    concepts = []
    visited = set()
    tm2._walk_tm2_entity(fake_client, CATEGORY_A, concepts, visited)
    call_count_after_first = len(fake_client.calls)

    tm2._walk_tm2_entity(fake_client, CATEGORY_A, concepts, visited)
    assert len(fake_client.calls) == call_count_after_first
    assert len([c for c in concepts if c.id == CATEGORY_A]) == 1


def test_load_tm2_from_who_dedupes_multiparented_leaf(fake_client):
    with patched_client(fake_client):
        result = tm2.load_tm2_from_who()
    shared = [c for c in result if c.id == SHARED_LEAF]
    assert len(shared) == 1


# ---------------------------------------------------------------------------
# 9. Deduplication (full load, not just the shared-leaf case above)
# ---------------------------------------------------------------------------

def test_load_tm2_from_who_returns_no_duplicate_ids(fake_client):
    with patched_client(fake_client):
        result = tm2.load_tm2_from_who()
    ids = [c.id for c in result]
    assert len(ids) == len(set(ids))


def test_load_tm2_from_who_excludes_non_codable_entities(fake_client):
    with patched_client(fake_client):
        result = tm2.load_tm2_from_who()
    ids = {c.id for c in result}
    assert BLOCK_A not in ids
    assert BLOCK_NO_CODE_LEAF not in ids
    assert MODULE_II not in ids
    assert DISORDERS_ROOT not in ids
    assert PATTERNS_ROOT not in ids


def test_load_tm2_from_who_structural_validation_failure_raises():
    """
    _validate_module_ii_structure() checks Module II's own @id and its
    parent/child relationships -- it does not independently re-fetch or
    re-check Chapter 26's own 'code' field, so the failure here must be
    something the function actually inspects: Module II's @id not
    matching the ID it was requested by.
    """
    broken_entities = _build_entities()
    broken_entities[MODULE_II] = {
        **broken_entities[MODULE_II],
        "@id": _uri("999999999"),  # WHO returns a different entity than requested
    }
    broken_client = FakeWHOClient(broken_entities)

    with patched_client(broken_client):
        with pytest.raises(tm2.TM2StructuralValidationError):
            tm2.load_tm2_from_who()


def test_load_tm2_from_who_raises_when_module_ii_missing_a_root():
    broken_entities = _build_entities()
    broken_entities[MODULE_II] = {
        **broken_entities[MODULE_II],
        "child": [_uri(DISORDERS_ROOT)],
    }
    broken_client = FakeWHOClient(broken_entities)

    with patched_client(broken_client):
        with pytest.raises(tm2.TM2StructuralValidationError):
            tm2.load_tm2_from_who()


# ---------------------------------------------------------------------------
# 12. Complete-cache-only assignment (no partial WHO cache on failure)
# ---------------------------------------------------------------------------

def test_load_tm2_from_who_raises_on_zero_codable_concepts():
    entities = _build_entities()
    entities[DISORDERS_ROOT] = {**entities[DISORDERS_ROOT], "child": []}
    entities[PATTERNS_ROOT] = {**entities[PATTERNS_ROOT], "child": []}
    client = FakeWHOClient(entities)

    with patched_client(client):
        with pytest.raises(tm2.TM2StructuralValidationError):
            tm2.load_tm2_from_who()


def test_warm_tm2_cache_does_not_install_cache_on_who_failure(fake_client):
    def raising_get(path):
        raise ConnectionError("simulated WHO outage")

    fake_client.get = raising_get

    with patched_client(fake_client):
        with patch.object(tm2, "_load_tm2_from_local", return_value=[]):
            with pytest.raises(RuntimeError):
                asyncio.run(tm2.warm_tm2_cache())

    assert tm2._tm2_cache is None
    assert tm2.get_tm2_source() == "unavailable"


# ---------------------------------------------------------------------------
# 13-14. WHO failure -> local fallback, invalid fallback handling
# ---------------------------------------------------------------------------

def _local_fallback_payload():
    return [
        {"id": "LOCAL001", "code": "L001", "title": "Local fallback disorder"},
        {"id": "LOCAL002", "code": "L002", "title": "Local fallback pattern"},
    ]


def test_warm_tm2_cache_falls_back_to_local_on_who_exception(fake_client, tmp_path, monkeypatch):
    fallback_path = tmp_path / "tm2.json"
    fallback_path.write_text(json.dumps(_local_fallback_payload()), encoding="utf-8")
    monkeypatch.setattr(tm2, "DATA_PATH", fallback_path)

    def raising_get(path):
        raise ConnectionError("simulated WHO outage")

    fake_client.get = raising_get

    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    assert tm2.get_tm2_source() == "local-fallback"
    concepts = tm2.get_tm2_concepts()
    assert len(concepts) == 2
    assert all(c.source == "local-fallback" for c in concepts)


def test_warm_tm2_cache_raises_when_who_fails_and_fallback_file_missing(
    fake_client, tmp_path, monkeypatch
):
    missing_path = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(tm2, "DATA_PATH", missing_path)

    def raising_get(path):
        raise ConnectionError("simulated WHO outage")

    fake_client.get = raising_get

    with patched_client(fake_client):
        with pytest.raises(RuntimeError):
            asyncio.run(tm2.warm_tm2_cache())

    assert tm2._tm2_cache is None
    assert tm2.get_tm2_source() == "unavailable"


def test_warm_tm2_cache_raises_when_fallback_file_is_not_a_json_list(
    fake_client, tmp_path, monkeypatch
):
    bad_path = tmp_path / "tm2.json"
    bad_path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    monkeypatch.setattr(tm2, "DATA_PATH", bad_path)

    def raising_get(path):
        raise ConnectionError("simulated WHO outage")

    fake_client.get = raising_get

    with patched_client(fake_client):
        with pytest.raises(RuntimeError):
            asyncio.run(tm2.warm_tm2_cache())

    assert tm2._tm2_cache is None


def test_warm_tm2_cache_raises_when_fallback_yields_zero_concepts(
    fake_client, tmp_path, monkeypatch
):
    empty_path = tmp_path / "tm2.json"
    empty_path.write_text(json.dumps([]), encoding="utf-8")
    monkeypatch.setattr(tm2, "DATA_PATH", empty_path)

    def raising_get(path):
        raise ConnectionError("simulated WHO outage")

    fake_client.get = raising_get

    with patched_client(fake_client):
        with pytest.raises(RuntimeError):
            asyncio.run(tm2.warm_tm2_cache())

    assert tm2._tm2_cache is None
    assert tm2.get_tm2_source() == "unavailable"


# ---------------------------------------------------------------------------
# 15. Provenance: WHO vs local-fallback
# ---------------------------------------------------------------------------

def test_warm_tm2_cache_success_marks_source_who(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    assert tm2.get_tm2_source() == "who"
    concepts = tm2.get_tm2_concepts()
    assert len(concepts) > 0
    assert all(c.source == "who" for c in concepts)


def test_warm_tm2_cache_fallback_marks_source_local_fallback(
    fake_client, tmp_path, monkeypatch
):
    fallback_path = tmp_path / "tm2.json"
    fallback_path.write_text(json.dumps(_local_fallback_payload()), encoding="utf-8")
    monkeypatch.setattr(tm2, "DATA_PATH", fallback_path)

    def raising_get(path):
        raise ConnectionError("simulated WHO outage")

    fake_client.get = raising_get

    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    assert tm2.get_tm2_source() == "local-fallback"


# ---------------------------------------------------------------------------
# 16. Cache behavior (clear_tm2_cache, uninitialized state)
# ---------------------------------------------------------------------------

def test_get_tm2_concepts_raises_before_cache_is_warmed():
    with pytest.raises(RuntimeError):
        tm2.get_tm2_concepts()


def test_clear_tm2_cache_resets_state(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())
    assert tm2.get_tm2_source() == "who"

    tm2.clear_tm2_cache()

    assert tm2.get_tm2_source() == "uninitialized"
    with pytest.raises(RuntimeError):
        tm2.get_tm2_concepts()


def test_warmed_cache_does_not_trigger_further_who_calls(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    call_count_after_warm = len(fake_client.calls)

    tm2.get_tm2_concepts()
    tm2.get_tm2_concept_by_id(CATEGORY_A)
    tm2.get_tm2_concept_by_code("SA01")

    assert len(fake_client.calls) == call_count_after_warm


# ---------------------------------------------------------------------------
# 17-19. get_tm2_concepts(), get_tm2_concept_by_id(), get_tm2_concept_by_code()
# ---------------------------------------------------------------------------

def test_get_tm2_concepts_returns_list_after_warm(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    result = tm2.get_tm2_concepts()
    assert isinstance(result, list)
    assert not asyncio.iscoroutine(result)
    assert len(result) > 0


def test_get_tm2_concept_by_id_finds_existing_concept(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    concept = tm2.get_tm2_concept_by_id(CATEGORY_A)
    assert concept is not None
    assert concept.code == "SA01"


def test_get_tm2_concept_by_id_finds_residual_by_compound_id(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    concept = tm2.get_tm2_concept_by_id(f"{RESIDUAL_PARENT}/other")
    assert concept is not None
    assert concept.code == "SX0Y"


def test_get_tm2_concept_by_id_returns_none_for_unknown_id(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    assert tm2.get_tm2_concept_by_id("does-not-exist") is None


def test_get_tm2_concept_by_code_finds_existing_concept(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    concept = tm2.get_tm2_concept_by_code("sa01")
    assert concept is not None
    assert concept.id == CATEGORY_A


def test_get_tm2_concept_by_code_returns_none_for_unknown_code(fake_client):
    with patched_client(fake_client):
        asyncio.run(tm2.warm_tm2_cache())

    assert tm2.get_tm2_concept_by_code("ZZ99") is None


# ---------------------------------------------------------------------------
# Structural validation (Chapter 26 -> Module II -> both TM2 roots)
# ---------------------------------------------------------------------------

def test_validate_module_ii_structure_passes_for_correct_hierarchy(fake_client):
    tm2._validate_module_ii_structure(fake_client)


def test_validate_module_ii_structure_fails_when_parent_is_wrong():
    entities = _build_entities()
    entities[MODULE_II] = {**entities[MODULE_II], "parent": ["http://id.who.int/icd/release/11/2026-01/mms/999999999"]}
    client = FakeWHOClient(entities)

    with pytest.raises(tm2.TM2StructuralValidationError):
        tm2._validate_module_ii_structure(client)
