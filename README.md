# PrimeHomes Realty — Real Estate Lead Bot

**Product:** Online receptionist / lead capture and sales workflow for PrimeHomes Realty  
**Stack direction (accepted):** React frontend · FastAPI backend · n8n orchestration  
**Documentation baseline:** 1.0 review-corrected draft

This repository holds the product documentation and the application scaffold. Application code, OpenAPI, migrations, and n8n workflow exports are not yet implemented. Setup commands below are **provisional** until toolchain decisions (D-10) are approved and verified in a clean checkout.

## What this system does

- Durably captures website enquiries (chat and structured form) before depending on AI or notifications
- Extracts candidate property requirements with provenance; backend validates before persistence
- Keeps pipeline, processing, qualification, assignment, and priority as **separate** dimensions
- Gives Sales a searchable queue with assignment, notes, follow-up tasks, and audited status changes
- Uses n8n only for orchestration (AI, alerts, optional Sheets export)—not as the database writer

## Canonical repository layout

```text
.
├── AGENTS.md                 # Instructions for AI coding agents (authority hierarchy)
├── README.md                 # This file — developer entry point
├── LICENSE
├── .env.example              # Safe placeholders only
├── .gitignore
├── frontend/                 # React customer chat/form + Sales dashboard
├── backend/                  # FastAPI API, domain services, repositories
│   ├── app/
│   ├── migrations/           # Single canonical migration directory
│   └── tests/
├── worker/                   # Optional outbox dispatcher (only if deployed separately)
├── n8n/
│   ├── workflows/
│   └── schemas/
├── tests/
│   ├── fixtures/             # Synthetic evaluation & contract fixtures
│   └── e2e/
└── docs/                     # Approved foundational documents
    ├── INDEX.md
    ├── operations/runbook.md
    └── ...
```

## Documentation

Start here:

1. [`docs/INDEX.md`](docs/INDEX.md) — document map and status
2. [`docs/01-product-requirements.md`](docs/01-product-requirements.md) — product intent and acceptance
3. [`docs/DECISION-REGISTER-AND-CHANGELOG.md`](docs/DECISION-REGISTER-AND-CHANGELOG.md) — open decisions and canonical enums
4. [`AGENTS.md`](AGENTS.md) — rules for automated coding agents

Do **not** treat proposed ADRs as accepted. See `docs/04-architecture-decision-records.md`.

## Prerequisites (provisional)

Toolchain is **pending approval** (decision D-10). The scaffold assumes the following candidates only; pin and verify before publishing tested commands:

| Area | Provisional candidate |
|------|------------------------|
| Frontend | Node.js 20+, React, TypeScript |
| Backend | Python 3.12+, FastAPI, Pydantic v2 |
| Database | PostgreSQL 16+ (ADR-0002 still **Proposed**) |
| Orchestration | n8n |
| Package managers | npm or pnpm (frontend); uv or pip (backend) |

## Local development (provisional — not verified)

```bash
# Clone
git clone https://github.com/bgbengs1-cyber/Real-estate.git
cd Real-estate

# Copy environment template (never commit real secrets)
cp .env.example .env

# Backend (after toolchain pin)
# cd backend && uv sync   # or: pip install -e ".[dev]"
# uv run uvicorn app.main:app --reload

# Frontend (after toolchain pin)
# cd frontend && npm install && npm run dev

# Optional worker (if outbox dispatcher is approved and separate)
# cd worker && ...
```

Commands above are placeholders. Do not present them as tested until a clean-checkout verification is recorded.

## Architecture boundaries (non-negotiable)

- **FastAPI** is the only writer of canonical business data
- **React** calls FastAPI only — never internal n8n or provider endpoints with secrets
- **n8n** orchestrates AI/notifications/export; it does not score, authorize, or write SQL directly
- **AI** produces candidate facts and draft replies; backend validates schema, revision, and policy before persistence
- Enquiry is **committed before** asynchronous AI/notification work (outbox or approved durable alternative)

## Pending decisions that block production implementation

See the decision register. High-impact items:

- D-01 PostgreSQL as canonical store
- D-02 Transactional outbox vs alternative queue
- D-03 Authentication / customer session
- D-04 AI provider
- D-05 Notification channel
- D-06 Numeric scoring on/off
- D-10 Toolchain pins

Synthetic scaffolding may proceed; do not lock unapproved choices into production paths.

## License

MIT — see [LICENSE](LICENSE).
