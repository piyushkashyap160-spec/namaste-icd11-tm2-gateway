from pydantic import BaseModel, Field
from typing import List, Optional, Any

class FHIRCoding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None
    version: Optional[str] = None

class FHIRPart(BaseModel):
    name: str
    valueCode: Optional[str] = None
    valueCoding: Optional[FHIRCoding] = None
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None

class FHIRParameter(BaseModel):
    name: str
    valueCoding: Optional[FHIRCoding] = None
    valueCode: Optional[str] = None
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    part: Optional[List[FHIRPart]] = None

class FHIRParameters(BaseModel):
    resourceType: str = "Parameters"
    parameter: List[FHIRParameter] = []
