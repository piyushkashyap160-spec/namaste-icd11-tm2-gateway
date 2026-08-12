from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.fhir.resources import FHIRParameters
from app.fhir.translate import process_fhir_translate
from app.security import require_scope
from app.schemas import TokenPayload
from app.database import get_db
from app.audit.logger import record_audit_log

router = APIRouter(tags=["FHIR R4 Interoperability Services"])

@router.post("/fhir/$translate", response_model=FHIRParameters)
def fhir_translate_endpoint(
    parameters: FHIRParameters,
    db: Session = Depends(get_db),
    auth: TokenPayload = Depends(require_scope("fhir:translate"))
):
    """
    FHIR R4 $translate implementation.
    Accepts FHIR Parameters resource, evaluates candidate mapping,
    and returns FHIR Parameters containing translation result and disclaimer.
    """
    response = process_fhir_translate(parameters)
    
    # Extract code and match details for audit log
    input_code = None
    for p in parameters.parameter:
        if p.valueCoding and p.valueCoding.code:
            input_code = p.valueCoding.code
            break
        elif p.valueCode:
            input_code = p.valueCode
            break

    result_param = next((p for p in response.parameter if p.name == "result"), None)
    is_success = result_param.valueBoolean if result_param else False

    selected_tm2 = None
    if is_success:
        match_param = next((p for p in response.parameter if p.name == "match"), None)
        if match_param and match_param.part:
            concept_part = next((part for part in match_param.part if part.name == "concept"), None)
            if concept_part and concept_part.valueCoding:
                selected_tm2 = concept_part.valueCoding.code

    record_audit_log(
        db=db,
        endpoint="/fhir/$translate",
        subject=auth.sub,
        facility_id=auth.facility_id,
        namaste_code=input_code,
        selected_tm2_candidate=selected_tm2,
        result="SUCCESS" if is_success else "NO_MATCH",
        notes="FHIR R4 $translate request processed"
    )

    return response
