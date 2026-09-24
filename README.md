# CareTaker &mdash; AI-Powered Care. Any Language. Full Compliance.

<div align="center">

**Created for the Google x NatWest Hackathon &bull; Built by Team Byte Builders&trade;**

[![Hackathon](https://img.shields.io/badge/Hackathon-Google%20x%20NatWest%20(11--18%20March%202026)-orange.svg?logo=google&logoColor=white)](#hackathon-context--timeline-11--18-march-2026)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-black.svg?logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![AI Platform](https://img.shields.io/badge/Google%20Cloud-Vertex%20AI%20%26%20Gemini-4285F4.svg?logo=google-cloud&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Security Standard](https://img.shields.io/badge/Security-Secure%20by%20Design%20(WMG)-red.svg?logo=shield&logoColor=white)](#secure-by-design-security-architecture)
[![Regulation](https://img.shields.io/badge/Compliance-CQC%20Regulation%2017-005ea2.svg)](#cqc-regulatory-compliance-framework)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-caretaker--ai.onrender.com-success.svg?logo=render&logoColor=white)](https://caretaker-ai-0mu3.onrender.com)
[![Tests](https://img.shields.io/badge/Test%20Suite-7%20Passed%20(100%25)-brightgreen.svg?logo=pytest&logoColor=white)](#automated-test-suite)

*A production-grade, secure multimodal AI platform empowering care workers, trainers, and healthcare supervisors through multilingual voice ingestion, semantic task matching, automated CQC Regulation 17 compliance reporting, AI practice mentor reviews, and demographic-tailored video training.*

**Live Application:** [https://caretaker-ai-0mu3.onrender.com](https://caretaker-ai-0mu3.onrender.com)

</div>

---

## Hackathon Context & Timeline (11 &ndash; 18 March 2026)

This project was built for **"The Secure Intelligence Frontier" Hackathon**, organized by **Google Cloud, NatWest Accelerator, WMG Venture Studio, and Warwick Business School (WBS)**.

```
+------------------------------------------------------------------------------------------------------+
|                                      OFFICIAL HACKATHON TIMELINE                                     |
+------------------------------------------------------------------------------------------------------+
| • March 11, 2026 (3:00 PM)  | Kickoff & Ideation (IDL Auditorium, University of Warwick)             |
|                             | Technical workshops with Google Cloud & NatWest Accelerator engineers  |
| • March 14, 2026 (10:00 AM) | Semi-Finals (IDL Building, University of Warwick)                      |
|                             | Progress pitch to expert panel of technical and commercial judges      |
| • March 16–17, 2026         | MVP & Deck Polish (Junction Building) with dedicated mentors          |
| • March 18, 2026            | The Grand Final & Demo Day at the Google Offices in London             |
+------------------------------------------------------------------------------------------------------+
```

### The Hackathon Challenge Mandate:
> *"Move beyond a simple demo to create a secure, commercially viable MVP that proactively addresses the unique security vulnerabilities of the AI era."*

CareTaker fulfills both commercial viability and the **Cyber-Security Excellence Award ("Secure by Design")** by pairing multimodal Vertex AI models with Caldicott/GDPR PII redaction, adversarial prompt injection defense, and cryptographic audit hashing for statutory clinical documentation.

---

## Team Byte Builders&trade;

- **Ioannis Konstantinou** ([@ayqon](https://github.com/ayqon))
- **Akanksh Caimi**
- **Mohamed Jemseed Aathik Ahamed**
- **Rumaan Mukadam**
- **Shinja Nagvekar**

---

## The Problem: The Documentation Skills Gap in Care

In UK health and social care, accurate documentation keeps vulnerable people safe, verifies standard care delivery, and satisfies statutory audits. However:

- **The Language & Written Barrier:** Trainees and care workers can perform practical care tasks effectively, but struggle with written English (especially with English as an additional language / ESL), leading to missing or delayed documentation.
- **Administrative Drain on Trainers:** Care trainers spend **5 to 10 hours per week** marking and manually correcting care records instead of coaching hands-on clinical skills.
- **Unprepared for Placements:** Incomplete documentation leaves trainees unprepared for real-world placements and exposes providers to CQC penalties under **Regulation 17 (Good Governance)**.

```
+-----------------------------------------------------------------------------------+
|                              MARKET & INDUSTRY IMPACT                             |
+-----------------------------------------------------------------------------------+
| • UK Social Care Economy: £77.8B contribution, 1.6M+ active workforce             |
| • Urgent Demand: 470,000+ new workers required across the UK by 2040              |
| • Global Vocational Training: $388B (2024) -> $649B (2030)                        |
| • Time Saved: 5-10 hours/week per trainer reclaimed for hands-on coaching         |
+-----------------------------------------------------------------------------------+
```

---

## What CareTaker Delivers

```
TRAINER / SUPERVISOR INPUT   -->   AI STRUCTURES   -->   TRAINEE / WORKER DOCUMENTS   -->   AI COMPARES & AUDITS   -->   SEALED CQC REPORT
---------------------------------------------------------------------------------------------------------------------------------------
Supervisor enters care steps        AI converts to        Worker uses voice or text         AI translates, compares        System generates CQC
(e.g., medication round,            action points,        in their own language to          to task embeddings, and        report + SHA-256 seal
personal care plan)                 time & priority       document what they did            flags practice issues          for regulatory audit
```

| Beneficiary | Core Value Delivered |
| :--- | :--- |
| **For Trainees / Workers** | Voice/text input in native language removes barriers; instant feedback builds documentation confidence and prepares workers for placement. |
| **For Trainers / Supervisors** | 5&ndash;10 hours/week saved on marking; objective data highlights learner gaps; real-time semantic task tracking. |
| **For Care Providers & Centres** | Higher completion rates, CQC Regulation 17 compliance by design, and audit-ready clinical records. |

---

## System Architecture & Technical Design

CareTaker is built upon a decoupled **Flask Application Factory (MVC + Service Layer)** pattern:

```mermaid
graph TD
    subgraph Client & Ingestion Layer
        W[Worker - Native Voice / Text / Mobile]
        S[Supervisor - Governance Portal]
    end

    subgraph Security Defense Shield
        RBAC[RBAC Session Authenticator]
        PII[Caldicott & GDPR PII Redaction Engine]
        INJ[Adversarial Prompt Injection Interceptor]
    end

    subgraph Core Application Service Layer
        GeminiSvc[GeminiService: Structured Output & Multimodal]
        EmbSvc[Semantic Vector Matching Engine]
        CQCSvc[CQC Regulation 17 Evaluator & Mentor]
        StoreSvc[GCS / Local Hybrid Storage Adapter]
    end

    subgraph Google Vertex AI Stack
        G25[Gemini 2.5 Flash]
        GEMB[Gemini Embedding 001]
        VEO[Google Veo 3.1 Video Generation]
    end

    subgraph Data & Cryptographic Ledger
        DB[(SQLAlchemy Relational Database)]
        SHA[SHA-256 Tamper-Evident Ledger]
    end

    W --> RBAC
    S --> RBAC
    RBAC --> INJ
    INJ --> PII
    PII --> GeminiSvc
    PII --> EmbSvc
    GeminiSvc --> G25
    EmbSvc --> GEMB
    CQCSvc --> G25
    StoreSvc --> VEO
    CQCSvc --> SHA
    SHA --> DB
```

---

## Google Vertex AI Modality Matrix

| Modality & Capability | Target Model | SDK Method | Implementation & Purpose |
| :--- | :--- | :--- | :--- |
| **Multimodal Audio Understanding** | `gemini-2.5-flash` | `generate_content` (`inline_data` audio blob) | Transcribes field voice notes, detects spoken dialect, and translates to clinical English in a single call. |
| **Structured Output Generation** | `gemini-2.5-flash` | `response_schema` + JSON MIME enforcement | Converts free-form shift logs into 11-field CQC care records and structured supervisory review recommendations. |
| **Semantic Similarity Vectors** | `gemini-embedding-001` | `embed_content` (`SEMANTIC_SIMILARITY`) | Generates 768-dim embeddings to match shift submissions against assigned tasks via cosine similarity. |
| **Video Synthesis** | `veo-3.1-generate-001` | `generate_videos` (Vertex AI) | Generates 8-second 720p instructional training videos tailored to worker demographic needs. |
| **Personalized Script Generation** | `gemini-2.5-flash` | `generate_content` | Produces culturally and linguistically adapted educational training scripts per worker profile. |

---

## "Secure by Design" Security Architecture

Developed to fulfill the **Google x NatWest Cyber-Security Excellence Award** mandate:

```
+---------------------------------------------------------------------------------------+
|                                SECURITY DEFENSE MATRIX                                |
+------------------------------------+--------------------------------------------------+
| Threat Vector                      | Defensive Architecture & Mitigation              |
+------------------------------------+--------------------------------------------------+
| 1. Multilingual Prompt Injections  | Multi-pattern regex & heuristic filters          |
|    & Jailbreak Payloads            | intercepting override clauses and DAN exploits.  |
| 2. Patient PII / PHI Leakage       | Automated redaction engine stripping UK NHS      |
|    (UK GDPR & Caldicott Standards) | numbers, phone numbers, postcodes, and emails.   |
| 3. Care Record Tampering           | SHA-256 cryptographic digests generated on       |
|                                    | finalization; verifiable via REST API.           |
| 4. Privilege Escalation            | Strict RBAC decorators enforcing worker vs.      |
|                                    | supervisor route access boundaries.              |
+------------------------------------+--------------------------------------------------+
```

---

## CQC Regulatory Compliance Framework

Generated care documentation is validated against **CQC Regulation 17 (Good Governance)** across the five Key Lines of Enquiry (**KLOE**):

1. **Safe:** Medication verification, hydration/fluid intake tracking, and proactive risk/safeguarding notes.
2. **Effective:** Person-centred outcomes and standard clinical procedure adherence.
3. **Caring:** Preservation of dignity, respect, and recording service user emotional responses.
4. **Responsive:** Immediate triggers for changes in mobility, condition, or follow-up care actions.
5. **Well-led:** Tamper-evident cryptographic ledger, AI practice reviews, and continuous learning loops.

---

## Project Structure

```
CareTaker/
├── app.py                      # Application Factory (create_app)
├── config.py                   # Environment Configurations (Dev / Test / Prod)
├── models.py                   # SQLAlchemy Models with Cryptographic Hashing
├── requirements.txt            # Locked Dependencies & Pytest
├── pytest.ini                  # Pytest configuration
├── seed.py                     # Demo accounts & database seeder
├── Dockerfile                  # Container deployment specification
├── blueprints/                 # Modular Route Blueprints
│   ├── auth.py                 # Authentication & RBAC Session Handlers
│   ├── worker.py               # Worker Dashboard, Multilingual Logging & Matching
│   ├── supervisor.py           # Supervisor Operations & AI Task Structuring
│   ├── cqc.py                  # CQC Regulation 17 Generation, Reviews & Hashing
│   ├── training.py             # Personalised Script & Veo Video Pipelines
│   └── api.py                  # Verification & Dashboard REST APIs
├── services/                   # Business Logic & Infrastructure Layer
│   ├── gemini_service.py       # Google GenAI / Vertex AI Integration
│   ├── security_service.py     # Prompt Injection, PII Masking & SHA-256 Hashing
│   └── storage_service.py      # Cloud Storage & Local Fallback Adapter
├── templates/                  # Modernized Responsive Jinja2 Templates
│   ├── base.html               # Master Layout & Design System
│   ├── index.html              # Secure Portal Authentication
│   ├── signup.html             # Role & Demographic Onboarding
│   ├── worker.html             # Worker Logging & Task Matching View
│   ├── supervisor.html         # Supervisor Dashboard & Task Dispatch
│   ├── cqc_report.html         # Printable Regulation 17 Care Record
│   └── cqc_review.html         # AI Practice Recommendations & Scoring
└── tests/                      # Automated Test Suite (100% Pass Rate)
    ├── conftest.py             # Fixtures & In-Memory Database
    ├── test_auth_routes.py     # Authentication & RBAC Enforcement Tests
    ├── test_security_service.py# Injection & PII Redaction Unit Tests
    └── test_cqc_workflow.py    # End-to-End CQC Lifecycle Tests
```

---

## How to Run on Localhost

### 1. Clone & Set Up Environment
```bash
# Clone repository
git clone https://github.com/ayqon/CareTaker-AI.git
cd CareTaker-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables Configuration
Copy the template configuration file. Note that `.env` files are strictly excluded by `.gitignore` to prevent any credential leakage:
```bash
cp .env.example .env
```

Your `.env` file contains:
```env
SECRET_KEY=your-secure-random-key
GOOGLE_CLOUD_PROJECT=nastwest-u26wck-617
GOOGLE_CLOUD_LOCATION=us-central1
DATABASE_URL=sqlite:///caretaker.db
FLASK_DEBUG=1
PORT=5001
```
*(Note: If Google Cloud credentials are not set, CareTaker automatically uses its built-in offline mock fallbacks and local storage adapter so all routes and interfaces function seamlessly.)*

### 3. Seed Demo Accounts & Launch
```bash
# Seed initial demo worker & supervisor accounts
python seed.py

# Launch the Flask application
python app.py
```
Open your browser and navigate to:
**`http://localhost:5001`**

### Demo Login Accounts:
- **Supervisor Account:** `supervisor1` / `password123`
- **Care Worker Account:** `worker1` / `password123`

---

## Automated Test Suite

Run the `pytest` test suite covering prompt injection defenses, PII redaction, RBAC access boundaries, and the CQC report lifecycle:

```bash
pytest -v
```

```text
============================= test session starts =============================
tests/test_auth_routes.py::test_login_and_logout PASSED                  [ 14%]
tests/test_auth_routes.py::test_rbac_access_control PASSED               [ 28%]
tests/test_auth_routes.py::test_worker_profile_update PASSED             [ 42%]
tests/test_cqc_workflow.py::test_full_cqc_workflow PASSED                [ 57%]
tests/test_security_service.py::test_prompt_injection_detection PASSED   [ 71%]
tests/test_security_service.py::test_pii_redaction_nhs_and_contact PASSED [ 85%]
tests/test_security_service.py::test_sha256_audit_hash_integrity PASSED  [100%]
============================== 7 passed in 2.10s ==============================
```
