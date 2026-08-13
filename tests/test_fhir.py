import asyncio
import json
import pytest
from app.fhir.resources import FHIRParameters, FHIRParameter, FHIRCoding
from app.fhir.translate import process_fhir_translate
from app.terminology import tm2
from app.terminology.tm2 import warm_tm2_cache

@pytest.fixture(autouse=True)
def init_tm2_cache(monkeypatch, tmp_path):
    original_cache = tm2._tm2_cache
    original_source = tm2._tm2_source

    fallback_payload = [
        {
            "id": "1564853364",
            "code": "SA01",
            "title": "Burning sensation of shoulder",
            "system": "http://id.who.int/icd/release/11/mms",
            "version": "2026-01"
        }
    ]
    fallback_path = tmp_path / "tm2.json"
    fallback_path.write_text(json.dumps(fallback_payload), encoding="utf-8")

    def raising_get_who_client():
        raise ConnectionError("simulated WHO outage")

    monkeypatch.setattr(tm2, "DATA_PATH", fallback_path)
    monkeypatch.setattr(tm2, "WHO_CACHE_PATH", tmp_path / "non_existent_who_cache.json")
    monkeypatch.setattr(tm2, "_get_who_client", raising_get_who_client)
    tm2.clear_tm2_cache()
    asyncio.run(warm_tm2_cache())
    yield
    tm2._tm2_cache = original_cache
    tm2._tm2_source = original_source


def test_fhir_translate_sat_d_8():
    req_params = FHIRParameters(
        resourceType="Parameters",
        parameter=[
            FHIRParameter(
                name="code",
                valueCoding=FHIRCoding(
                    system="http://namaste.gov.in/sat-d",
                    code="SAT-D.8",
                    display="aMsadAhaH"
                )
            )
        ]
    )

    res = process_fhir_translate(req_params)
    assert res.resourceType == "Parameters"
    
    result_param = next(p for p in res.parameter if p.name == "result")
    assert result_param.valueBoolean is True

    match_param = next(p for p in res.parameter if p.name == "match")
    concept_part = next(part for part in match_param.part if part.name == "concept")
    assert concept_part.valueCoding.system == "http://id.who.int/icd/release/11/mms"
    assert concept_part.valueCoding.version == "2026-01"
    assert concept_part.valueCoding.code == "SA01"
    assert concept_part.valueCoding.display == "Burning sensation of shoulder"

def test_fhir_translate_no_candidate():
    req_params = FHIRParameters(
        resourceType="Parameters",
        parameter=[
            FHIRParameter(
                name="code",
                valueCoding=FHIRCoding(
                    system="http://namaste.gov.in/sat-d",
                    code="SAT-D.60",
                    display="tvagrotra"
                )
            )
        ]
    )

    res = process_fhir_translate(req_params)
    result_param = next(p for p in res.parameter if p.name == "result")
    assert result_param.valueBoolean is False

def test_fhir_translate_missing_code():
    req_params = FHIRParameters(resourceType="Parameters", parameter=[])
    res = process_fhir_translate(req_params)
    result_param = next(p for p in res.parameter if p.name == "result")
    assert result_param.valueBoolean is False
