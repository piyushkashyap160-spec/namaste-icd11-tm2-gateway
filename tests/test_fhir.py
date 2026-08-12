from app.fhir.resources import FHIRParameters, FHIRParameter, FHIRCoding
from app.fhir.translate import process_fhir_translate

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
    assert concept_part.valueCoding.code == "1564853364"
    assert "Burning sensation of shoulder" in concept_part.valueCoding.display

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
