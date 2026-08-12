import jwt
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.config import settings
from app.schemas import TokenPayload

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

def mint_dev_token(
    subject: str = "emr-user-1",
    facility_id: str = "FAC-IN-DELHI-01",
    scopes: Optional[List[str]] = None,
    abha_number: Optional[str] = "91-1234-5678-9012",
    expires_minutes: int = settings.TOKEN_EXPIRE_MINUTES
) -> str:
    """
    Generate a standard JWT access token for development/integration testing.
    """
    if scopes is None:
        scopes = ["terminology:read", "mapping:read", "fhir:translate", "audit:read"]
    
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {
        "sub": subject,
        "facility_id": facility_id,
        "abha_number": abha_number,
        "scopes": scopes,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, settings.EMR_JWT_SECRET, algorithm=settings.ALGORITHM)
    return token

# Alias for backwards compatibility if needed
create_access_token = mint_dev_token

def verify_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme)
) -> TokenPayload:
    """
    Verify incoming JWT Bearer token and decode payload.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.EMR_JWT_SECRET,
            algorithms=[settings.ALGORITHM]
        )
        sub: str = payload.get("sub")
        if sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload invalid: missing sub",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenPayload(
            sub=sub,
            facility_id=payload.get("facility_id"),
            abha_number=payload.get("abha_number"),
            scopes=payload.get("scopes", []),
            exp=payload.get("exp")
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_scope(required_scope: str):
    """
    FastAPI dependency to enforce specific JWT permission scope.
    """
    def scope_checker(payload: TokenPayload = Depends(verify_bearer_token)) -> TokenPayload:
        if required_scope not in payload.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: missing required scope '{required_scope}'"
            )
        return payload
    return scope_checker
