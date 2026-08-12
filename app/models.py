from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    subject = Column(String(100), nullable=True)
    facility_id = Column(String(100), nullable=True)
    endpoint = Column(String(200))
    namaste_code = Column(String(50), nullable=True)
    selected_tm2_candidate = Column(String(100), nullable=True)
    score = Column(Float, nullable=True)
    confidence = Column(String(20), nullable=True)
    result = Column(String(50)) # CANDIDATE_MAPPING / NO_CANDIDATE / SUCCESS / ERROR
    notes = Column(Text, nullable=True)
