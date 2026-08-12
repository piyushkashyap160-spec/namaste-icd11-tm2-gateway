from fastapi.testclient import TestClient
from app.main import app
from app.security import mint_dev_token

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_unauthorized_access():
    response = client.get("/api/namaste/concepts")
    assert response.status_code == 401

def test_authorized_namaste_concepts():
    token = mint_dev_token(scopes=["terminology:read"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/namaste/concepts", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_concept_mapping_api():
    token = mint_dev_token(scopes=["mapping:read", "audit:read"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/namaste/concept/SAT-D.8/mapping", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["namaste"]["code"] == "SAT-D.8"
    assert data["mapping_status"] == "CANDIDATE_MAPPING"
    assert len(data["matches"]) > 0

def test_fhir_translate_api():
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

def test_audit_logs_api():
    token = mint_dev_token(scopes=["audit:read"])
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/audit/logs", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
