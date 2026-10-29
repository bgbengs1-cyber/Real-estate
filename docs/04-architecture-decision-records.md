# 4. Architecture Decision Records (ADRs)

**Version:** 1.0  
**Rule:** `Accepted` means approved by the named decision owner and recorded in the repository. A recommendation elsewhere in the documents does not make a `Proposed` ADR accepted.

## Decision log

| ADR | Decision | Status | Owner |
|---|---|---|---|
| ADR-0001 | React + FastAPI + n8n core stack | Accepted as project direction from the brief | Product/engineering owner to record name |
| ADR-0002 | PostgreSQL canonical database; Google Sheets one-way export | Proposed — approval required | Product/business owner + backend lead |
| ADR-0003 | FastAPI owns canonical writes and business rules; n8n orchestrates | Proposed baseline — approval required | Backend lead + automation lead |
| ADR-0004 | Durable outbox/dispatcher for asynchronous work | Proposed — architecture cost review required | Backend lead + operations owner |
| ADR-0005 | AI returns candidate facts/drafts; backend validates | Accepted safety principle | Product/engineering owner to record name |
| ADR-0006 | React calls FastAPI only, never internal n8n endpoints | Accepted safety/architecture principle | Engineering owner to record name |
| ADR-0007 | OpenAPI as HTTP contract source | Proposed — toolchain confirmation required | Backend lead |
| ADR-0008 | Idempotency, bounded retries, explicit failure tracking | Accepted reliability principle | Engineering/operations owner to record name |
| ADR-0009 | Sheets is reporting/export only in MVP | Proposed, linked to ADR-0002 | Product/business owner + automation lead |

## ADR-0001 — Use React, FastAPI, and n8n as the core stack

**Status:** Accepted as project direction.  
**Context:** The project brief explicitly selects React for frontend, FastAPI for backend/API, and n8n for orchestration.  
**Decision:** Build the customer chat/form and Sales dashboard in React; expose APIs and enforce business rules in FastAPI; use n8n for AI/integrations/notifications workflows.  
**Consequences:** Component boundaries must remain clear. Exact React language (TypeScript vs JavaScript), package manager, deployment, and internal module structure still require confirmation.  
**Alternatives:** A single full-stack framework; n8n as the public API; a backend-only UI. Rejected for current project direction, not universally inferior.

## ADR-0002 — PostgreSQL as the recommended canonical store; Sheets as secondary export

**Status:** Proposed — do not treat as approved until owner confirms.  
**Context:** Leads, messages, identity, status history, follow-up tasks, idempotency, and recoverable asynchronous events require relational integrity and transactions. Google Sheets is useful for viewing/reporting but is weak as an equal transactional master for these requirements.  
**Proposed decision:** PostgreSQL is the sole canonical data store. Google Sheets, if enabled, receives approved fields one way after successful database commit. Edits in Sheets do not modify canonical records.  
**Alternatives:** Sheets-only; two-way synchronization; relational DB only.  
**Consequences:** Requires a managed PostgreSQL environment, migration ownership, backup/restore practice, access control, and retention policy. Sheets export can fail independently.  
**Approval questions:** Hosting, cost, credentials, backups, recovery objectives, and business reporting needs.

## ADR-0003 — FastAPI owns canonical writes and business rules

**Status:** Proposed baseline — approval required.  
**Context:** Duplicating validation, scoring, status transitions, and persistence across Python, JavaScript, and n8n would produce divergent behavior.  
**Proposed decision:** FastAPI owns lead/contact/message updates, business validation, qualification, scoring, authorization, pipeline transitions, audit entries, and idempotency. n8n orchestrates and calls authenticated API endpoints for context/results/actions. No direct n8n SQL writes.  
**Consequences:** Internal APIs need schemas and service authentication. n8n workflows are easier to replace/test, but some operations require extra round trips.

## ADR-0004 — Persist enquiry before asynchronous AI/notification processing

**Status:** Proposed — architecture cost review required.  
**Context:** A synchronous AI call or webhook before database commit risks losing the enquiry when a provider times out.  
**Proposed decision:** Commit the lead/conversation/message and durable outbox event in one transaction; a monitored dispatcher delivers events to n8n at least once.  
**Alternatives:** Direct webhook call after commit; managed queue; transactional outbox/worker.  
**Benefits:** Durable intent to process, observable retries, recoverability.  
**Costs:** Worker deployment, leases, retry scheduling, metrics/alerts, dead-letter handling, replay controls, and more tests.  
**Approval condition:** Select this only if the team commits to implementing and operating the worker; otherwise approve a simpler durable queue design and update every dependent document. Do not silently pretend a direct webhook is equivalent.

## ADR-0005 — AI produces candidates; backend validates and applies rules

**Status:** Accepted safety principle.  
**Decision:** AI may extract candidate facts, identify ambiguity, summarize, and draft a reply. FastAPI validates schemas, source revision, field values, provenance, message policy, score, permissions, and status transitions. AI must not independently set final score, authorize access, or mark a lead won/lost.  
**Consequences:** Requires a versioned AI schema and evaluation dataset (Document 12).

## ADR-0006 — React communicates only through FastAPI

**Status:** Accepted safety/architecture principle.  
**Decision:** Browser code never calls internal n8n webhook URLs or provider APIs requiring secrets.  
**Consequences:** FastAPI must expose all required customer and sales operations; CORS/session/auth controls are configured at the API boundary.

## ADR-0007 — OpenAPI is the HTTP contract source

**Status:** Proposed — toolchain confirmation required.  
**Proposed decision:** Maintain OpenAPI alongside FastAPI request/response models, generate or validate frontend TypeScript types, and add contract tests. Avoid manually maintained, divergent API enums.  
**Consequences:** Changes to public schemas require compatibility review and coordinated updates.

## ADR-0008 — Idempotency, bounded retries, explicit failure tracking

**Status:** Accepted reliability principle.  
**Decision:** Assume duplicate requests and at-least-once event delivery. Use persisted idempotency keys, stable event IDs, unique constraints, bounded retries with backoff for transient errors, and terminal/dead-letter states. Treat timeouts with unknown side-effect outcome distinctly.  
**Consequences:** Notification deduplication depends partly on provider capabilities; unknown delivery may require reconciliation/manual review.

## ADR-0009 — Google Sheets is reporting/export only in MVP

**Status:** Proposed, dependent on ADR-0002 approval.  
**Proposed decision:** Export allowlisted fields from the canonical DB to a restricted sheet. Sheets is not used as a second writer. Export failures are retried and visible; they never affect lead capture.  
**Risks:** Sheet permissions, accidental sharing, stale reports, formula injection, retention/deletion copies.

## Decision approval process

1. An ADR author marks the record `Proposed` and documents context, options, rationale, consequences, owner, and approval needed.
2. The named owner reviews through the team's agreed PR/review process.
3. On approval, set `Accepted`, add reviewer/decision date, and update affected documents in the same change or an explicit linked follow-up.
4. If reversed, mark `Superseded` and link the replacement ADR; do not erase history.
5. AI coding agents must not convert a proposed decision into an implementation assumption. They must stop or request a human decision when the pending choice affects foundational work.

## Cross-document impact checklist

When a decision changes, review PRD scope/acceptance; architecture and data model; API/OpenAPI; React flows/types; n8n workflows/payloads; testing; security; README/runbook; `AGENTS.md`; deployment cost and ownership.
