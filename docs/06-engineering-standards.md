# 6. Engineering Standards & Repository Guide

**Version:** 1.0 review-corrected draft  
**Status:** Base conventions; proposed tools/packages require approval before scaffold.

## 1. Principles

- Keep each responsibility in one authoritative layer.
- Prefer explicit schemas/domain terms over loosely typed dictionaries.
- Preserve original customer messages and traceable field provenance.
- Design side effects for retries and partial failures.
- Automate formatting, linting, type checks, tests, schema validation, and secret scanning where feasible.
- Keep abstractions proportional to actual complexity.

## 2. Canonical repository layout

```text
primehomes-real-estate-lead-bot/
├── AGENTS.md
├── README.md
├── frontend/
│   ├── package.json
│   └── src/{app,features,components,lib,tests}/
├── backend/
│   ├── pyproject.toml
│   ├── app/{api,schemas,domain,services,repositories,integrations,core}/
│   ├── migrations/       # one canonical migration directory
│   └── tests/
├── worker/               # only if outbox dispatcher is separately deployed
├── n8n/{workflows,schemas}/
├── tests/{fixtures,e2e}/
└── docs/
```

Do not create both `database/migrations/` and `backend/migrations/`. If Alembic is selected, use `backend/migrations/` as the single canonical directory unless an accepted ADR says otherwise.

## 3. Naming and formatting

- Python modules/functions/variables: `snake_case`; classes: `PascalCase`; constants: `UPPER_SNAKE_CASE`.
- React components: `PascalCase`; hooks: `useX`; variables/functions: `camelCase` in TS/JS.
- API JSON fields and database columns: `snake_case`.
- Use timezone-aware UTC timestamps and `_at` suffixes for timestamps.
- n8n name format: `PH | <domain> | <flow> | v<major>`, e.g. `PH | Lead Processing | Extract and Qualify | v1`.
- Do not rename public enum/field names without contract migration and consumer review.

## 4. Frontend standards

- React calls FastAPI only; never call internal n8n/provider endpoints requiring secrets.
- Use typed request/response contracts; generating/checking TypeScript types from OpenAPI is recommended pending toolchain approval.
- Handle loading, success, empty, validation error, network error, stale version, and unknown outcome where applicable.
- Client validation improves usability; backend validation is authoritative.
- Do not duplicate scoring, permission, qualification, or status-transition logic in the UI.
- Use semantic HTML, keyboard access, visible focus, accessible errors/status updates, responsive layouts, and appropriate contrast.
- Avoid premature abstractions; build shared components when actual reuse exists.

## 5. FastAPI standards

- Use Pydantic request/response models and strict validation at external/internal boundaries.
- Keep route handlers thin; place business rules in named domain services/use cases and database access behind consistent repository/session patterns.
- Use dependency injection for DB sessions, authenticated users, and service identities.
- Use transactions for lead/message/outbox writes and consequential sales updates/audit records.
- Never mass-assign arbitrary ORM fields from request bodies; explicitly allowlist writable fields and apply concurrency checks.
- Return a stable error envelope without stack traces or sensitive content.
- Use structured safe logs and correlation IDs.
- Keep AI/notification/Sheets clients behind integration boundaries.

## 6. n8n standards

- Orchestrate integrations; do not duplicate authoritative scoring, permissions, merge rules, or pipeline transitions.
- Validate event type/schema version and stable identifiers.
- Use n8n credential storage or the approved secret manager; never hard-code secrets.
- Use bounded retries only for transient errors. Do not indefinitely retry `400`, `401`, `403`, invalid schema, or stale-result conflicts.
- Record explicit outcomes and make side effects duplicate-safe.
- Sanitize workflow exports of credentials, execution data, PII, environment-specific URLs, and tokens before committing.
- Separate local/staging/production endpoints, credentials, and notification destinations.

## 7. Data and state invariants

- Canonical enums live in the PRD/API contract and must match database constraints/tests.
- `pipeline_status`, `processing_status`, `qualification_status`, assignment, priority, message ordering/visibility, outbox state, and notification state are distinct.
- `land` belongs to `property_type`, not `transaction_type`.
- Original messages are immutable; corrections add a message or provenance history.
- AI outputs are candidate values until backend validation succeeds.
- No stale AI result may overwrite a newer message, customer correction, or Sales correction.
- Lead/message/outbox writes that must happen together share one transaction.
- Google Sheets is not an authority for application writes in the MVP proposal.

## 8. Database and migrations

- Use one migration tool and one directory. Alembic + SQLAlchemy is a candidate choice, pending approval.
- Review every schema change for constraints, indexes, nullability, deletion/retention effects, compatibility, rollback/forward-fix strategy, and security.
- Test migrations from an empty DB and from the previous supported schema.
- No destructive production migration without explicit review, verified backup, and recovery plan.
- Runtime DB roles use least privilege; never use a superuser in the application.
- Store money as `NUMERIC` with currency and period; do not use binary floating point as the persisted money representation.

## 9. Configuration and secrets

- Maintain a safe `.env.example` with names and fake placeholders only.
- Select one settings mechanism per process; document who reads each value.
- Fail early with an actionable error when required settings are missing, without printing secret values.
- Frontend public environment variables contain only public configuration.
- If a secret reaches Git history/logs, rotate/revoke it; deleting the latest copy is insufficient.

## 10. Testing and quality automation

Suggested baseline, pending selection: Ruff + pytest for Python; TypeScript compiler and ESLint/formatter with an agreed React test framework; PostgreSQL integration tests; OpenAPI/schema checks; controlled n8n tests; synthetic AI fixtures; a small E2E critical-path suite.

Run applicable checks in CI. A test must assert behavior, not just execute lines. Keep deterministic tests independent of live model/provider availability; verify real integrations in controlled staging.

## 11. Git and review

- Use short-lived branches and small focused PRs.
- Select and document a commit-message convention; summaries should be meaningful and imperative.
- PRs include requirement IDs, approach, contract/schema/workflow changes, tests actually run, migration/release effects, risks, and screenshots for UI changes.
- Require human review for authorization, migrations, secrets, AI response policy, outbox/retry logic, and production n8n workflows.
- An agent's self-report is not the only review for security-sensitive changes.

## 12. Definition of Done

- Acceptance criteria are met and linked to the requirement.
- Code lives in the correct architecture layer.
- Relevant success and failure/edge-case tests are added and actually run.
- Configured format/lint/type/build/migration/schema checks pass.
- Contracts, fixtures, workflow exports, and docs remain aligned.
- No secrets or real customer data are added.
- Unverified environments/integrations are explicitly disclosed.
- Pending foundational decisions are raised rather than guessed.

## 13. Toolchain decisions still pending

Confirm: TypeScript vs JavaScript; Node/package manager/version; frontend test libraries; Python version/lockfile/package manager; SQLAlchemy/Alembic; auth provider; worker deployment; CI platform; local DB/container approach; formatter/linter versions. Do not publish supposedly tested commands until these are selected and verified.
