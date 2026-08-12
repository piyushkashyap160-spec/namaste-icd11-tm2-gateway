from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas import NamasteConcept, TM2Concept, TokenPayload
from app.security import require_scope
from app.terminology.namaste import get_namaste_concepts, get_namaste_concept_by_code
from app.terminology.tm2 import get_tm2_concepts, get_tm2_concept_by_id

router = APIRouter(prefix="/api", tags=["Terminology Services"])

@router.get("/namaste/concepts", response_model=List[NamasteConcept])
def list_namaste_concepts(
    auth: TokenPayload = Depends(require_scope("terminology:read"))
):
    """
    Retrieve full catalog of supported Ayush NAMASTE concepts.
    """
    return get_namaste_concepts()

@router.get("/namaste/concept/{code}", response_model=NamasteConcept)
def get_namaste_concept(
    code: str,
    auth: TokenPayload = Depends(require_scope("terminology:read"))
):
    """
    Lookup a specific NAMASTE concept by code (e.g. SAT-D.8).
    """
    concept = get_namaste_concept_by_code(code)
    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NAMASTE concept with code '{code}' not found."
        )
    return concept

@router.get("/tm2/concepts", response_model=List[TM2Concept])
def list_tm2_concepts(
    auth: TokenPayload = Depends(require_scope("terminology:read"))
):
    """
    Retrieve ICD-11 Traditional Medicine Module 2 concept catalog.
    """
    return get_tm2_concepts()
