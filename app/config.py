import os

class Settings:
    PROJECT_NAME: str = "NAMASTE & ICD-11 TM2 Interoperability API"
    VERSION: str = "1.0.0"
    EMR_JWT_SECRET: str = os.getenv("EMR_JWT_SECRET", "dev-secret-key-change-in-production-namaste-icd11-tm2")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./namaste_audit.db")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ALGORITHM: str = "HS256"
    TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

settings = Settings()
