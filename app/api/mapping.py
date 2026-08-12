from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.schemas import ConceptMappingResponse, TokenPayload
from app.security import require_scope
from app.database import get_db
from app.terminology.mapper import get_mapping_for_concept
from app.audit.logger import record_audit_log

router = APIRouter(prefix="/api/namaste", tags=["Candidate Terminology Mapping"])

@router.get("/concept/{code}/mapping", response_model=ConceptMappingResponse)
def get_concept_candidate_mapping(
    code: str,
    db: Session = Depends(get_db),
    auth: TokenPayload = Depends(require_scope("mapping:read"))
):
    """
    Perform safe candidate terminology mapping from NAMASTE concept code (or search phrase)
    to candidate ICD-11 TM2 concepts with clinical feature scoring and evidence.
    """
    mapping_res = get_mapping_for_concept(code)

    top_cand = mapping_res.matches[0] if mapping_res.matches else None
    
    # Audit log recording
    record_audit_log(
        db=db,
        endpoint=f"/api/namaste/concept/{code}/mapping",
        subject=auth.sub,
        facility_id=auth.facility_id,
        namaste_code=mapping_res.namaste.code,
        selected_tm2_candidate=top_cand.tm2_id if top_cand else None,
        score=top_cand.score if top_cand else 0.0,
        confidence=top_cand.confidence if top_cand else "NONE",
        result=mapping_res.mapping_status,
        notes=f"Candidate count: {mapping_res.count}"
    )

    return mapping_res
