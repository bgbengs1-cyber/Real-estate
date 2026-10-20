# Backend (FastAPI)

Canonical API and business rules for the PrimeHomes lead bot.

## Layout

```text
backend/
├── pyproject.toml
├── app/
│   ├── main.py                 # Application entry
│   ├── api/                    # Route handlers (thin)
│   │   ├── public.py           # /api/v1/public/...
│   │   ├── sales.py            # /api/v1/sales/...
│   │   └── internal.py         # /api/v1/internal/...
│   ├── schemas/                # Pydantic request/response models
│   ├── domain/                 # Entities, enums, pure domain rules
│   ├── services/               # Use cases (scoring, qualification, intake)
│   ├── repositories/           # Persistence access
│   ├── integrations/           # AI, n8n, notifications, Sheets clients
│   └── core/                   # Config, security, logging, dependencies
├── migrations/                 # Single canonical migration directory
└── tests/
```

## Principles

- Route handlers stay thin; business rules live in services/domain.
- Transactions cover lead + message + outbox writes together.
- Never mass-assign ORM fields from request bodies.
- Stable error envelope; no stack traces or secrets in responses.
- PostgreSQL and Alembic are **proposed** (ADR-0002, D-10)—do not treat as approved until decision owners confirm.

See `docs/05-api-contract-integration.md` and `docs/06-engineering-standards.md`.
