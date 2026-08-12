import uuid
from typing import Optional
from sqlalchemy.orm import Session
import logging

from app.models import AuditLog

logger = logging.getLogger(__name__)

def record_audit_log(
    db: Session,
    endpoint: str,
    result: str,
    subject: Optional[str] = None,
    facility_id: Optional[str] = None,
    namaste_code: Optional[str] = None,
    selected_tm2_candidate: Optional[str] = None,
    score: Optional[float] = None,
    confidence: Optional[str] = None,
    notes: Optional[str] = None,
    request_id: Optional[str] = None
) -> AuditLog:
    """
    Log interoperability API activity for compliance and auditability.
    Strips PHI while persisting essential metadata.
    """
    if not request_id:
        request_id = str(uuid.uuid4())

    log_entry = AuditLog(
        request_id=request_id,
        subject=subject,
        facility_id=facility_id,
        endpoint=endpoint,
        namaste_code=namaste_code,
        selected_tm2_candidate=selected_tm2_candidate,
        score=score,
        confidence=confidence,
        result=result,
        notes=notes
    )

    try:
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record audit log: {str(e)}")
        raise e
