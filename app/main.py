from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api import auth, terminology, mapping, fhir, audit
from app.terminology.tm2 import warm_tm2_cache

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
### India EHR Standards Interoperability & Terminology Gateway
Safe candidate mapping engine integrating Ayush **NAMASTE** terminology with WHO **ICD-11 Traditional Medicine Module 2 (TM2)**.
Features deterministic clinical feature scoring, hard clinical rejection rules, FHIR R4 `$translate` API, JWT authorization, and non-PHI audit logging.

> **Disclaimer**: This mapping engine generates candidate mappings for interoperability demonstration. It does not establish official WHO or NAMASTE equivalence.
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for React/Vite dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(terminology.router)
app.include_router(mapping.router)
app.include_router(fhir.router)
app.include_router(audit.router)

@app.on_event("startup")
async def _startup_load_tm2():
    await warm_tm2_cache()

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/", tags=["System"])
def root():
    return {
        "message": "NAMASTE & ICD-11 TM2 Terminology Integration API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
