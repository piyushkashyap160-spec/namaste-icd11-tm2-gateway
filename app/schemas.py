from typing import List, Optional
from datetime import datetime

try:
    from pydantic import BaseModel, Field, ConfigDict
    _PYDANTIC_HAS_CONFIGDICT = True
except ImportError:
    from pydantic import BaseModel, Field
    ConfigDict = None
    _PYDANTIC_HAS_CONFIGDICT = False

# Auth Schemas
class DevTokenRequest(BaseModel):
    subject: str = Field(default="emr-user-1", description="Subject / User ID")
    facility_id: str = Field(default="FAC-IN-DELHI-01", description="ABDM Facility ID")
    abha_number: Optional[str] = Field(default="91-1234-5678-9012", description="Optional ABHA number")
    scopes: List[str] = Field(
        default=["terminology:read", "mapping:read", "fhir:translate", "audit:read"],
        description="Granted scopes"
    )

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scopes: List[str]

class TokenPayload(BaseModel):
    sub: str
    facility_id: Optional[str] = None
    abha_number: Optional[str] = None
    scopes: List[str] = []
    exp: int

# Terminology Schemas
class NamasteConcept(BaseModel):
    code: str
    display: str
    definition: str
    terminology: str = "SAT-D"

class TM2Concept(BaseModel):
    id: str
    code: Optional[str] = None
    title: str
    system: str = "http://id.who.int/icd/release/11/mms"
    version: Optional[str] = None
    class_kind: Optional[str] = None
    foundation_uri: Optional[str] = None
    source: str = "who"
    entity_uri: Optional[str] = None

# Evidence Schema
class ClinicalEvidence(BaseModel):
    words: List[str] = []
    anatomy: List[str] = []
    symptoms: List[str] = []
    quality: List[str] = []
    findings: List[str] = []

# Candidate Match Schema
class CandidateMatch(BaseModel):
    tm2_id: str
    tm2_code: Optional[str] = None
    tm2_title: str
    tm2_system: Optional[str] = None
    tm2_version: Optional[str] = None
    score: float
    confidence: str # HIGH, MEDIUM, LOW, NONE
    equivalence: str = "relatedto"
    evidence: ClinicalEvidence

# Mapping Response Schema
class ConceptMappingResponse(BaseModel):
    namaste: NamasteConcept
    count: int
    matches: List[CandidateMatch]
    mapping_status: str # CANDIDATE_MAPPING / NO_CANDIDATE
    note: str = "Algorithm-generated candidate mapping. Not an official WHO or NAMASTE equivalence."

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    request_id: str
    timestamp: datetime
    subject: Optional[str] = None
    facility_id: Optional[str] = None
    endpoint: str
    namaste_code: Optional[str] = None
    selected_tm2_candidate: Optional[str] = None
    score: Optional[float] = None
    confidence: Optional[str] = None
    result: str
    notes: Optional[str] = None

    if _PYDANTIC_HAS_CONFIGDICT:
        model_config = ConfigDict(from_attributes=True)

