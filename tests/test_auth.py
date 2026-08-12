import pytest
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.security import mint_dev_token, verify_bearer_token, require_scope
from app.config import settings
from app.schemas import TokenPayload

def test_mint_dev_token_valid():
    token = mint_dev_token(subject="user-101", facility_id="FAC-01", scopes=["terminology:read"])
    assert isinstance(token, str)
    
    payload = jwt.decode(token, settings.EMR_JWT_SECRET, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "user-101"
    assert payload["facility_id"] == "FAC-01"
    assert "terminology:read" in payload["scopes"]

def test_verify_bearer_token_invalid():
    class DummyCreds:
        credentials = "invalid.jwt.token"

    with pytest.raises(HTTPException) as exc_info:
        verify_bearer_token(DummyCreds())
    assert exc_info.value.status_code == 401

def test_expired_token():
    expired_payload = {
        "sub": "user-expired",
        "scopes": ["terminology:read"],
        "exp": datetime.utcnow() - timedelta(minutes=10)
    }
    expired_token = jwt.encode(expired_payload, settings.EMR_JWT_SECRET, algorithm=settings.ALGORITHM)
    
    class DummyCreds:
        credentials = expired_token

    with pytest.raises(HTTPException) as exc_info:
        verify_bearer_token(DummyCreds())
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()

def test_scope_checking():
    payload = TokenPayload(sub="u1", scopes=["terminology:read"], exp=1000)
    checker = require_scope("mapping:read")
    with pytest.raises(HTTPException) as exc_info:
        checker(payload)
    assert exc_info.value.status_code == 403
