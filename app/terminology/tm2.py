from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional, Set

from app.schemas import TM2Concept


DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "tm2.json"
)

WHO_MMS_SYSTEM = "http://id.who.int/icd/release/11/mms"
WHO_RELEASE = os.getenv("WHO_ICD_RELEASE", "2026-01")

# Verified against the live WHO ICD-11 MMS API for release 2026-01.
WHO_CHAPTER_26_ID = os.getenv(
    "WHO_CHAPTER_26_ID",
    "718687701",
)

WHO_MODULE_II_ID = os.getenv(
    "WHO_MODULE_II_ID",
    "562274788",
)

WHO_TM2_DISORDERS_ID = os.getenv(
    "WHO_TM2_DISORDERS_ID",
    "1147241349",
)

WHO_TM2_PATTERNS_ID = os.getenv(
    "WHO_TM2_PATTERNS_ID",
    "1908537217",
)


_tm2_cache: Optional[List[TM2Concept]] = None
_tm2_source: str = "uninitialized"

_RESIDUAL_SUFFIXES = {"other", "unspecified"}


class TM2StructuralValidationError(RuntimeError):
    """Raised when the expected WHO TM2 hierarchy is not found."""


def _title_value(title: object) -> str:
    """
    Convert a WHO language-tagged title into a normal string.

    Example:
        {"@language": "en", "@value": "Stomatitis disorder (TM2)"}
    """
    if isinstance(title, dict):
        return str(title.get("@value", "")).strip()

    if title is None:
        return ""

    return str(title).strip()


def _entity_id(entity_uri: object) -> str:
    """
    Extract the WHO entity identifier from a URI.

    Ordinary entities:
        .../mms/1918241818 -> "1918241818"

    Residual categories ("other specified" / "unspecified") use a
    compound path: the parent's numeric ID followed by a literal
    "other" or "unspecified" segment. These are real, independently
    fetchable WHO entities distinct from their parent, so the compound
    form must be preserved rather than collapsed to the trailing
    segment alone.

        .../mms/1576332228/other       -> "1576332228/other"
        .../mms/1576332228/unspecified -> "1576332228/unspecified"
    """
    if not isinstance(entity_uri, str):
        return ""

    segments = entity_uri.rstrip("/").split("/")

    if not segments:
        return ""

    last = segments[-1]

    if last in _RESIDUAL_SUFFIXES and len(segments) >= 2:
        return f"{segments[-2]}/{last}"

    return last


def _entity_path(entity_id: str) -> str:
    """Build the release-specific WHO MMS entity path."""
    return (
        f"/icd/release/11/{WHO_RELEASE}/mms/{entity_id}"
    )


def _get_who_client():
    """
    Import the WHO client lazily.

    This is intentional: importing app.main must not require WHO
    credentials to exist. WHO loading happens during startup and can
    fall back to local TM2 data if credentials/network are unavailable.
    """
    from app.integrations.who_icd import who_icd_client

    return who_icd_client


def _validate_module_ii_structure(client) -> None:
    """
    Verify the WHO hierarchy before traversing it.

    Expected:

        Chapter 26
            |
        Module II
          /     \
      Disorders Patterns
    """
    module_ii = client.get(
        _entity_path(WHO_MODULE_II_ID)
    )

    module_id = _entity_id(module_ii.get("@id"))

    if module_id and module_id != WHO_MODULE_II_ID:
        raise TM2StructuralValidationError(
            "WHO Module II response returned unexpected entity ID: "
            f"{module_id}"
        )

    # Verify Module II belongs to Chapter 26.
    parent_ids = {
        _entity_id(parent)
        for parent in (module_ii.get("parent") or [])
    }

    if WHO_CHAPTER_26_ID not in parent_ids:
        raise TM2StructuralValidationError(
            "WHO Module II is not under Chapter 26. "
            f"Expected parent {WHO_CHAPTER_26_ID}; "
            f"received parents {sorted(parent_ids)}"
        )

    child_ids = {
        _entity_id(child)
        for child in (module_ii.get("child") or [])
    }

    expected_roots = {
        WHO_TM2_DISORDERS_ID,
        WHO_TM2_PATTERNS_ID,
    }

    if not expected_roots.issubset(child_ids):
        raise TM2StructuralValidationError(
            "WHO Module II does not contain both expected TM2 roots. "
            f"Expected {sorted(expected_roots)}; "
            f"received children {sorted(child_ids)}"
        )


def _walk_tm2_entity(
    client,
    entity_id: str,
    concepts: List[TM2Concept],
    visited: Set[str],
) -> None:
    """
    Recursively traverse a WHO TM2 hierarchy.

    Structural nodes such as blocks are traversed but not returned.

    Only:
        classKind == "category"
        AND non-empty code

    are exposed as codable TM2 concepts.
    """
    if not entity_id or entity_id in visited:
        return

    visited.add(entity_id)

    data = client.get(_entity_path(entity_id))

    actual_id = _entity_id(data.get("@id"))

    if actual_id and actual_id != entity_id:
        raise TM2StructuralValidationError(
            "WHO returned an unexpected entity ID. "
            f"Requested {entity_id}, received {actual_id}"
        )

    title = _title_value(data.get("title"))

    code = str(data.get("code") or "").strip()

    class_kind = str(
        data.get("classKind") or ""
    ).strip().lower()

    entity_uri = data.get("@id")

    if not isinstance(entity_uri, str) or not entity_uri:
        entity_uri = (
            f"{WHO_MMS_SYSTEM}/{entity_id}"
        )

    foundation_uri = data.get("source")

    if not isinstance(foundation_uri, str):
        foundation_uri = None

    # Only WHO category entities with an ICD code are codable concepts.
    if class_kind == "category" and code:
        concepts.append(
            TM2Concept(
                id=entity_id,
                code=code,
                title=title,
                system=WHO_MMS_SYSTEM,
                version=WHO_RELEASE,
                class_kind=class_kind,
                foundation_uri=foundation_uri,
                source="who",
                entity_uri=entity_uri,
            )
        )

    # Continue through structural nodes.
    for child_uri in data.get("child") or []:
        child_id = _entity_id(child_uri)

        if child_id:
            _walk_tm2_entity(
                client,
                child_id,
                concepts,
                visited,
            )


def load_tm2_from_who() -> List[TM2Concept]:
    """
    Build the complete codable TM2 concept cache from WHO.

    WHO is treated as the authoritative source for the live dataset.
    """
    client = _get_who_client()

    _validate_module_ii_structure(client)

    concepts: List[TM2Concept] = []
    visited: Set[str] = set()

    _walk_tm2_entity(
        client,
        WHO_TM2_DISORDERS_ID,
        concepts,
        visited,
    )

    _walk_tm2_entity(
        client,
        WHO_TM2_PATTERNS_ID,
        concepts,
        visited,
    )

    # Defensive deduplication by WHO entity ID.
    unique: dict[str, TM2Concept] = {}

    for concept in concepts:
        unique[concept.id] = concept

    concepts = list(unique.values())

    concepts.sort(
        key=lambda concept: (
            concept.code or "",
            concept.id,
        )
    )

    if not concepts:
        raise TM2StructuralValidationError(
            "WHO TM2 traversal completed but returned "
            "zero codable category concepts."
        )

    return concepts


def _load_tm2_from_local() -> List[TM2Concept]:
    """
    Load the local TM2 snapshot as an offline fallback.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"TM2 fallback file not found: {DATA_PATH}"
        )

    with open(DATA_PATH, "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    if not isinstance(raw_data, list):
        raise ValueError(
            "TM2 fallback file must contain a JSON list."
        )

    concepts: List[TM2Concept] = []

    for item in raw_data:
        if not isinstance(item, dict):
            raise ValueError(
                "Each TM2 fallback entry must be a JSON object."
            )

        # Existing local data may contain only the old fields.
        # New TM2Concept fields are optional for this reason.
        concept = TM2Concept(
            **item,
            source="local-fallback",
        )

        concepts.append(concept)

    return concepts


async def warm_tm2_cache() -> None:
    """
    Populate the TM2 cache during FastAPI startup.

    WHO is attempted first.

    If the complete WHO traversal fails, the local snapshot is loaded.

    The active cache is assigned only after a complete dataset has been
    successfully constructed.
    """
    global _tm2_cache, _tm2_source

    try:
        who_concepts = load_tm2_from_who()

        # Atomic replacement only after the complete traversal succeeds.
        _tm2_cache = who_concepts
        _tm2_source = "who"

        print(
            f"[TM2] WHO cache loaded successfully: "
            f"{len(who_concepts)} concepts "
            f"(release {WHO_RELEASE})."
        )

    except Exception as who_error:
        print(
            "[TM2] WHO loading failed; using local fallback."
        )
        print(
            f"[TM2] WHO error: {type(who_error).__name__}: "
            f"{who_error}"
        )

        try:
            fallback_concepts = _load_tm2_from_local()

            if not fallback_concepts:
                raise RuntimeError(
                    "Local TM2 fallback contains zero concepts."
                )

            # Atomic replacement only after fallback validation.
            _tm2_cache = fallback_concepts
            _tm2_source = "local-fallback"

            print(
                f"[TM2] Local fallback loaded successfully: "
                f"{len(fallback_concepts)} concepts."
            )

        except Exception as fallback_error:
            # Do not silently start with an empty terminology cache.
            _tm2_cache = None
            _tm2_source = "unavailable"

            raise RuntimeError(
                "TM2 initialization failed. "
                "WHO loading failed and local fallback could not "
                "be loaded."
            ) from fallback_error


def get_tm2_concepts() -> List[TM2Concept]:
    """
    Existing synchronous terminology interface.

    Normal API requests only read the already-warmed cache.
    """
    if _tm2_cache is None:
        raise RuntimeError(
            "TM2 terminology cache is not initialized. "
            "FastAPI startup may not have completed."
        )

    return _tm2_cache


def get_tm2_concept_by_id(
    tm2_id: str,
) -> Optional[TM2Concept]:
    """
    Lookup a TM2 concept by WHO entity ID.
    """
    normalized = tm2_id.strip()

    for concept in get_tm2_concepts():
        if concept.id == normalized:
            return concept

    return None


def get_tm2_concept_by_code(
    code: str,
) -> Optional[TM2Concept]:
    """
    Lookup a TM2 concept by ICD-11 code.
    """
    normalized = code.strip().upper()

    for concept in get_tm2_concepts():
        if concept.code and concept.code.upper() == normalized:
            return concept

    return None


def get_tm2_source() -> str:
    """Return the provenance of the active TM2 cache."""
    return _tm2_source


def clear_tm2_cache() -> None:
    """
    Clear the cache.

    Primarily intended for tests.
    """
    global _tm2_cache, _tm2_source

    _tm2_cache = None
    _tm2_source = "uninitialized"
