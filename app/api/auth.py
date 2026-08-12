from fastapi import APIRouter
from app.schemas import DevTokenRequest, Token
from app.security import mint_dev_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/dev-token", response_model=Token)
def generate_dev_token(request: DevTokenRequest = DevTokenRequest()):
    """
    Mint a JWT bearer access token for development/testing.
    """
    token_str = mint_dev_token(
        subject=request.subject,
        facility_id=request.facility_id,
        scopes=request.scopes,
        abha_number=request.abha_number
    )
    return Token(
        access_token=token_str,
        token_type="bearer",
        expires_in=settings.TOKEN_EXPIRE_MINUTES * 60,
        scopes=request.scopes
    )

@router.post("/token", response_model=Token)
def generate_token(request: DevTokenRequest = DevTokenRequest()):
    """
    Alias endpoint to mint a JWT bearer access token.
    """
    return generate_dev_token(request)
