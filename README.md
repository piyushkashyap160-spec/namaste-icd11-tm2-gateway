# NAMASTE & ICD-11 TM2 Interoperability API & Dashboard

> **Disclaimer**: The mapping engine generates candidate mappings for interoperability demonstration. It does not establish official WHO or NAMASTE equivalence.

## 1. Core Objective & Problem Statement

This project addresses the healthcare interoperability challenge for Electronic Health Record (EHR) Standards for India:

```
NAMASTE concept (Ayush SAT-D)
      ↓
Terminology Mapping Engine (Clinical Normalization + Feature Extraction + Hard Rejection)
      ↓
ICD-11 TM2 Candidate Concepts
      ↓
FHIR R4 $translate Response (Parameters Resource)
      ↓
EMR Integration & Audit Trail
```

It enables Indian EMR systems to translate Traditional Ayush terminology concepts (SAT-D) into candidate WHO ICD-11 Traditional Medicine Module 2 (TM2) concepts using safe, deterministic candidate scoring and strict clinical rejection rules.

---

## 2. System Architecture

```
api-namaste/
├── app/
│   ├── main.py             # FastAPI entry point & CORS
│   ├── config.py           # JWT & DB Settings
│   ├── database.py         # SQLAlchemy engine & sessions
│   ├── models.py           # AuditLog ORM models
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── security.py        # JWT auth (mint_dev_token, verify_bearer_token, require_scope)
│   ├── terminology/        # Terminology normalization & mapper engine
│   │   ├── normalizer.py   # Text standardizer (lowercasing, plurals, safe synonyms)
│   │   ├── namaste.py      # NAMASTE SAT-D concept repository
│   │   ├── tm2.py          # ICD-11 TM2 concept repository
│   │   └── mapper.py       # Feature extractor, scoring algorithm & hard rejection rules
│   ├── fhir/               # FHIR R4 interoperability layer
│   │   ├── resources.py    # FHIR Parameters, Coding Pydantic models
│   │   └── translate.py    # FHIR $translate operation logic
│   ├── api/                # REST APIRouters
│   │   ├── auth.py         # /api/auth/dev-token
│   │   ├── terminology.py  # /api/namaste/concepts, /api/tm2/concepts
│   │   ├── mapping.py      # /api/namaste/concept/{code}/mapping
│   │   ├── fhir.py         # /fhir/$translate
│   │   └── audit.py        # /api/audit/logs
│   └── audit/              # Audit logging module (record_audit_log)
├── data/
│   ├── namaste.json        # Ayush SAT-D concepts dataset
│   └── tm2.json            # WHO ICD-11 TM2 concepts dataset
├── tests/                  # Pytest automated test suite
│   ├── test_auth.py
│   ├── test_mapping.py
│   ├── test_fhir.py
│   └── test_api.py
├── frontend/               # React + Vite Healthcare Dashboard
└── run.py                  # Server launcher script
```

---

## 3. Safe Candidate Mapping Methodology

The terminology mapper operates in distinct phases:

### A. Text Normalization (`normalizer.py`)
- Lowercasing, NFD Unicode normalization, punctuation stripping.
- Plural reduction (`stools` → `stool`, `eyes` → `eye`).
- Safe synonym substitution (`burning sensation` ↔ `burning`, `inflammatory` ↔ `inflammation`).

### B. Clinical Feature Extraction (`mapper.py`)
Extracts semantic categories from clinical definitions:
- **Anatomy**: `shoulder`, `eye`, `eyelid`, `bowel`, `skull`
- **Symptoms**: `burning`, `pain`, `inflammation`, `fever`, `cough`
- **Quality**: `burning`, `loose`, `dry`, `bloodshot`, `hard`
- **Findings**: `swelling`, `elevated temperature`
- **Objects**: `stool`, `eye`, `shoulder`
- **Functional**: `proper functioning`, `health state`
- **Temporal/Context Modifiers**: `sudden`, `onset`, `continuous`

> **Note**: Modifiers such as `"sudden"` are context modifiers and do **not** cause rejection of core disease concepts (e.g. `"sudden onset of loose stools"` matches `"Loose stool pattern disorder"`).

### C. Hard Clinical Rejection Rules
Candidate concepts are **rejected** if any of the following apply:
1. **Explicit Anatomy Conflict**: Query specifies `shoulder`, candidate specifies `eye` or `bowel`.
2. **Explicit Symptom Missing**: Query specifies `burning`, candidate specifies `frozen` without burning.
3. **Explicit Clinical Object Missing**: Query specifies `stool`, candidate specifies `eyelid`.
4. **Generic Query Over-Specification**: Query `"eye diseases"` prefers `"Eye disorders (TM2)"` over specific sub-diseases like `"Dry eye disorder"`.
5. **Functional Query Rule**: Functional queries (`"proper functioning of eyes"`) are rejected from mapping to ordinary disease concepts.
6. **No-Candidate Safety**: If no candidate reaches clinical confidence thresholds, the system returns `NO_CANDIDATE` rather than forcing a false match.

---

## 4. Authentication & Scopes

JWT bearer authentication configured via `EMR_JWT_SECRET`. Supported permission scopes:
- `terminology:read`: Catalog access
- `mapping:read`: Candidate mapping engine
- `fhir:translate`: FHIR `$translate` operation
- `audit:read`: Audit logs

### Mint Dev Token Command
```bash
curl -X POST http://127.0.0.1:8000/api/auth/dev-token \
  -H "Content-Type: application/json" \
  -d '{"subject": "test-user", "facility_id": "FAC-DELHI-01", "scopes": ["terminology:read", "mapping:read", "fhir:translate", "audit:read"]}'
```

---

## 5. API Usage Examples

### Candidate Mapping Request
```bash
curl -X GET http://127.0.0.1:8000/api/namaste/concept/SAT-D.8/mapping \
  -H "Authorization: Bearer <TOKEN>"
```

### FHIR R4 `$translate` Request
```bash
curl -X POST http://127.0.0.1:8000/fhir/\$translate \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Parameters",
    "parameter": [
      {
        "name": "code",
        "valueCoding": {
          "system": "http://namaste.gov.in/sat-d",
          "code": "SAT-D.8",
          "display": "aMsadAhaH"
        }
      }
    ]
  }'
```

---

## 6. Running Locally

### Backend Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run automated test suite
python -m pytest

# 3. Start backend server
python run.py
```
FastAPI Swagger documentation: `http://127.0.0.1:8000/docs`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Dashboard URL: `http://localhost:5173`

---

## 7. Future Integration & Limitations

- **Dataset Scope**: Uses representative sample datasets in `data/namaste.json` and `data/tm2.json` for demonstration.
- **Future Integration**: The repository data access layer (`app/terminology/namaste.py` and `tm2.py`) is designed with repository interfaces ready to plug into official WHO ICD API v11 endpoints and Ayush e-NAMASTE APIs.
