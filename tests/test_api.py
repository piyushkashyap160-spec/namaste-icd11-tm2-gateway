"""
Integration tests for the API endpoints.

These tests use the TestClient which triggers the startup event / lifespan
of the FastAPI app. The TM2 cache is pre-seeded via direct patching so no live
WHO traversal is needed during testing.
"""
import asyncio
import json
import pathlib
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import mint_dev_token
from app.terminology import tm2
from app.terminology.tm2 import warm_tm2_cache


SYNTHETIC_TM2 = [
    {
        "id": "1564853364",
        "code": "SA01",
        "title": "Burning sensation of shoulder",
        "system": "http://id.who.int/icd/release/11/mms",
        "version": "2026-01",
        "class_kind": "category",
        "source": "who",
    }
]


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """
    Integration test client with pre-seeded TM2 cache.
    Uses a module-scoped temp directory so the cache file persists across all tests.
    Direct attribute patching (instead of monkeypatch) allows module scope.
    """
    tmp = tmp_path_factory.mktemp("api_test_cache")
    cache_path = tmp / "who_tm2_cache.json"
    local_path = tmp / "tm2.json"
    cache_path.write_text(json.dumps(SYNTHETIC_TM2), encoding="utf-8")
    local_path.write_text(json.dumps(SYNTHETIC_TM2), encoding="utf-8")

    # Save originals
    original_who_cache = tm2.WHO_CACHE_PATH
    original_data_path = tm2.DATA_PATH

    # Patch
    tm2.WHO_CACHE_PATH = cache_path
    tm2.DATA_PATH = local_path

    # Clear and re-seed cache synchronously
    tm2.clear_tm2_cache()
    asyncio.run(warm_tm2_cache())

    with TestClient(app) as c:
        yield c

    # Restore
    tm2.WHO_CACHE_PATH = original_who_cache
    tm2.DATA_PATH = original_data_path
    tm2.clear_tm2_cache()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_unauthorized_access(client):
    response = client.get("/api/namaste/concepts")
    assert response.status_code == 401


def test_authorized_namaste_concepts(client):
    token = mint_dev_token(scopes=["terminology:read"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/namaste/concepts", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_concept_mapping_api(client):
    token = mint_dev_token(scopes=["mapping:read", "audit:read"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/namaste/concept/SAT-D.8/mapping", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["namaste"]["code"] == "SAT-D.8"
    assert data["mapping_status"] == "CANDIDATE_MAPPING"
    assert len(data["matches"]) > 0


def test_fhir_translate_api(client):
    token = mint_dev_token(scopes=["fhir:translate"])
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "resourceType": "Parameters",
        "parameter": [
            {
                "name": "code",
                "valueCoding": {
                    "system": "http://namaste.gov.in/sat-d",
                    "code": "SAT-D.8",
                    "display": "aMsadAhaH"
                }
            }
        ]
    }
    response = client.post("/fhir/$translate", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Parameters"
    assert data["parameter"][0]["valueBoolean"] is True


def test_audit_logs_api(client):
    token = mint_dev_token(scopes=["audit:read"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/audit/logs", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
