from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.schemas import AuditLogResponse, TokenPayload
from app.security import require_scope
from app.database import get_db
from app.models import AuditLog

router = APIRouter(prefix="/api/audit", tags=["Audit & Governance"])

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    auth: TokenPayload = Depends(require_scope("audit:read"))
):
    """
    Retrieve clinical terminology audit log history for compliance reporting.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return logs
