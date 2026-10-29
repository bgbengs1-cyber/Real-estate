# 2. System Architecture & Data Design

**Version:** 1.0 review-corrected draft  
**Status:** Recommended architecture baseline; decisions marked pending require approval before implementation.

## 1. Architecture summary

```text
Customer browser (React)
        │ HTTPS; protected customer session
        ▼
FastAPI ─────── PostgreSQL (canonical records; pending approval)
  │                    │
  │                    └── business rows + outbox event in same transaction
  │                                      │
  │                                      ▼
  │                             Outbox dispatcher/worker
  │                                      │ authenticated, at-least-once delivery
  │                                      ▼
  │                                     n8n
  │                           ┌──────────┼─────────┐
  │                           ▼          ▼         ▼
  │                          AI      Sales alerts  Sheets export (optional)
  │                           │          │         │
  └──────── authenticated, validated callback ────┘
             FastAPI validates and persists results

Sales browser (React) ── authenticated FastAPI endpoints ── PostgreSQL
```

The diagram describes the recommended target, not an existing implementation. **FastAPI is the only application writer for canonical business data.** n8n must not update PostgreSQL tables directly. Google Sheets is an optional downstream reporting/export destination, never an equal master.

## 2. Component responsibilities

### React frontend

- Customer chat/form and Sales dashboard.
- Render queued, processing, needs-review, error, stale, and success states.
- Call FastAPI only; never call n8n internal webhooks from browser code.
- Use client validation for usability, while treating FastAPI as authoritative.
- Never bundle internal credentials, provider keys, or server-only configuration.

### FastAPI backend

- Validate payloads and enforce authentication, authorization, rate limits, and business rules.
- Create/update contacts, leads, conversations, messages, tasks, audit records, and outbox events.
- Own scoring, qualification decisions, pipeline transitions, field precedence, and stale-result rejection.
- Expose OpenAPI documentation and typed request/response schemas.
- Validate and persist n8n callback results idempotently.

### PostgreSQL (recommended; requires explicit approval)

Canonical store for leads, contacts, conversations, messages, sales assignments, tasks, audit entries, processing jobs, idempotency records, notifications, and outbox events. It provides relational constraints and transactions needed by the recommended design.

### Outbox dispatcher/worker (recommended; architecture decision pending)

- Claim due outbox rows safely (e.g., PostgreSQL `FOR UPDATE SKIP LOCKED` plus a lease/claim timestamp).
- Send an authenticated event envelope to n8n.
- Persist attempt count, last error category, next-attempt time, and terminal/dead-letter state.
- Use bounded exponential backoff with jitter for transient failures.
- Treat delivery as at-least-once, never exactly-once; downstream handling must be idempotent.
- Run as a monitored process/service with graceful shutdown and documented health checks.

### n8n

Orchestrates AI calls, notification providers, and optional Sheets export. It validates event schema/version and IDs, calls internal FastAPI routes for context/results, and reports outcomes. It does not decide final score, permissions, pipeline transitions, or write directly to canonical SQL tables.

### AI provider

Proposes structured extraction, missing-field questions, concise summaries, and draft responses. It treats customer text as untrusted data and must not invent contact details, budgets, property availability, current listing prices, appointments, or confirmed commercial decisions.

## 3. Canonical domain model

- **Contact:** person/contact identity; may be absent for an anonymous first enquiry.
- **Lead:** one distinct commercial enquiry/property need; can exist without a confirmed contact. One contact can have multiple leads.
- **Conversation:** thread linked to one lead.
- **Message:** persisted inbound/outbound message, with a per-conversation sequence.
- **Property requirement:** normalized request facts, source/provenance, and original text.
- **Sales user:** authenticated team identity mapped to app role.
- **Follow-up task:** scheduled action, due time, owner, status, completion data.
- **Audit event:** history for status/assignment/override/security-relevant changes.
- **Processing job:** asynchronous work for a lead input revision; `conversation_id` is nullable for a structured-only submission that does not contain a free-text message.
- **Outbox event:** durable intent to trigger downstream workflow after a database commit.
- **Notification attempt:** attempt/delivery outcome, separate from lead state.
- **Idempotency record:** maps a scoped key and request hash to the original result.

A new message on the same enquiry does not automatically create a new lead. A materially different property need must not overwrite the first requirement set; create/link a separate lead or route a suspected duplicate to Sales.

## 4. Canonical status and taxonomy contract

| Field | Allowed values | Owner / purpose |
|---|---|---|
| `transaction_type` | `buy`, `rent`, `sell`, `general_enquiry`, `unknown` | Extracted fact; seller enquiries route to human review in MVP |
| `property_type` | `apartment`, `house`, `duplex`, `office`, `shop`, `land`, `other`, `unknown` | Property category; `land` is not transaction intent |
| `timeline` | `immediate` (≤7 days), `within_1_month` (8–30 days), `within_3_months` (31–90 days), `researching`, `unknown` | Customer-provided intent timing |
| `pipeline_status` | `new`, `contacted`, `viewing_scheduled`, `negotiation`, `nurturing`, `won`, `lost` | Sales-owned business progress |
| `processing_status` | `queued`, `processing`, `completed`, `needs_review`, `failed` | Technical processing state |
| `qualification_status` | `incomplete`, `qualified`, `needs_review`, `disqualified` | Whether reliable data exists for the agreed sales process |
| `priority_band` | `hot`, `warm`, `standard`, `unscored` | Deterministic prioritization; `review_required` is separate |
| `sender_type` | `customer`, `assistant`, `sales_agent`, `system` | Message actor type |
| `outbox_status` | `pending`, `leased`, `delivered_to_n8n`, `retry_wait`, `dead_letter` | Dispatcher delivery state, not AI completion |
| `notification_status` | `queued`, `provider_accepted`, `delivered`, `failed`, `unknown` | Provider attempt outcome |

A lead can be `pipeline_status=new`, `processing_status=completed`, `qualification_status=incomplete`, and unassigned at the same time. Never use one generic `status` for all dimensions. For normalized budget, `budget_amount` represents one exact/approximate stated amount, `budget_min_amount`/`budget_max_amount` represent explicit bounds, and `budget_relation` explains their meaning. Do not convert “around ₦80m” into a hard maximum. `budget_currency` is null when unresolved; structured UI amounts may default to NGN only when that currency is explicitly displayed and approved.

## 5. Logical data model

This is a schema checklist, not a migration-ready SQL schema. Finalize constraints, indexes, deletion policy, and retention during migration review.

### `contacts`

- `id UUID PK`
- `name TEXT NULL`, `email TEXT NULL`, `phone TEXT NULL`
- `created_at`, `updated_at TIMESTAMPTZ`
- Add contact verification/consent metadata only as required by approved product and privacy decisions.

Do not require a contact record for anonymous enquiries. `leads.contact_id` may be null until identity is provided and validated.

### `leads`

- `id UUID PK`, `contact_id UUID NULL FK contacts`, `source_channel TEXT NOT NULL`
- `transaction_type`, `property_type`, `timeline` constrained to canonical enums
- `location_text TEXT NULL`
- `budget_amount NUMERIC(18,2) NULL`, `budget_min_amount NUMERIC(18,2) NULL`, `budget_max_amount NUMERIC(18,2) NULL`, `budget_relation` enum (`exact`, `approximate`, `minimum`, `maximum`, `range`, `unknown`), `budget_currency CHAR(3) NULL`, `budget_period` enum, `budget_text_original TEXT NULL`. Currency is nullable: do not infer NGN solely from ambiguous free text.
- `bedroom_count SMALLINT NULL`, `property_detail_text TEXT NULL`, `original_requirement_text TEXT NULL`
- `pipeline_status`, `processing_status`, `qualification_status`, `priority_band` as separate constrained fields
- `priority_score SMALLINT NULL CHECK (priority_score BETWEEN 0 AND 100)`; null means unscored
- `score_rule_version TEXT NULL`, `priority_reason_codes JSONB NOT NULL DEFAULT '[]'`
- `assigned_to_user_id UUID NULL FK sales_users`, `review_required BOOLEAN NOT NULL DEFAULT false`
- `version INTEGER NOT NULL DEFAULT 1` for optimistic concurrency/stale-result protection
- `created_at`, `updated_at TIMESTAMPTZ`, `closed_reason TEXT NULL`

### `conversations` and `messages`

- `customer_sessions`: opaque session ID, token hash (never raw token), expiry/revocation timestamps, creation/last-seen times; exact cookie/session approach requires auth decision.
- Conversation: `id UUID PK`, `lead_id UUID FK`, protected session relationship, `revision BIGINT NOT NULL DEFAULT 0`, timestamps.
- Message: `id UUID PK`, `conversation_id UUID FK`, `client_message_id UUID NULL`, `sequence_number BIGINT NOT NULL`, `sender_type`, `body TEXT`, `created_at`; unique `(conversation_id, sequence_number)` and unique `(conversation_id, client_message_id)` when supplied. Persist only messages eligible for the relevant audience; AI drafts remain processing-job data until FastAPI approves them. Client-only optimistic/pending UI state is not a persisted server message state.
- Preserve original customer messages. Use the increasing sequence for message ordering; UUID is not a chronological cursor.
- Persist a customer-visible assistant response only after FastAPI validates it and marks it available.

### Other required tables

- `property_requirement_facts`: normalized field value, source, source message/revision, confidence if AI-derived, actor, time, and supersession history; or an equivalent versioned facts model.
- `sales_users`: app identity ID, external identity subject, email, role, active flag, timestamps.
- `follow_up_tasks`: lead, owner, due date, task type, status, completion timestamp, creator.
- `lead_activity`: actor, action, prior/new value, reason, timestamp, correlation ID.
- `processing_jobs`: lead ID, nullable conversation ID, input kind (`conversation_message` or `structured_submission`), input revision, status, attempts, timestamps, safe failure code.
- `outbox_events`: event ID, type, schema version, aggregate ID/revision, payload, status, attempts, lease owner/expiry, next attempt, last safe error, timestamps.
- `idempotency_records`: scope, key, request hash, resource/result reference, created/expiry; unique scoped key.
- `notification_attempts`: lead/event, destination type, provider, attempt number, provider reference, status, safe error code/times.
- `workflow_receipts` or equivalent unique processed-event tracking for callback results.

## 6. Transaction and event flow

1. React sends a form/message to FastAPI over HTTPS with its protected customer session and idempotency identity.
2. FastAPI validates input and derives the session identity server-side.
3. In a database transaction, it inserts or resolves the lead/conversation/message and inserts the outbox event. A duplicate request returns the same logical result.
4. After commit, FastAPI acknowledges: `202 Accepted`, `processing_status=queued`. If persistence fails, it must not return successful capture.
5. Dispatcher leases and sends the event to authenticated n8n. Use `conversation.message_received` when free text needs AI extraction; use `lead.structured_submission_received` when the form already contains meaningful structured fields but no free-text message. If n8n accepts but the dispatcher times out, delivery may repeat; n8n must deduplicate by `event_id`.
6. n8n fetches authorized processing context from FastAPI. It calls the selected AI provider only for free-text extraction; for a structured-only submission it skips AI and invokes the documented completion path after backend validation.
7. FastAPI validates auth, event identity, schema, allowed values, and `input_revision`. Stale results are recorded/rejected and must not overwrite newer messages or Sales edits.
8. FastAPI transactionally persists accepted facts/provenance, updates `processing_status`, calculates priority only if approved, persists a safe reply if applicable, and queues notification/export events as needed.
9. n8n sends alerts or exports; outcomes are recorded idempotently.
10. Sales users perform actions only through authenticated FastAPI endpoints, with audit history for consequential changes.

## 7. Field provenance and merge precedence

Allowed provenance values: `customer_stated`, `ai_extracted`, `sales_corrected`, `system_derived`. Recommended precedence: explicit authorized Sales correction > latest explicit customer statement > validated AI extraction > unknown/null. Keep historical versions; do not silently erase contradictory facts. Never merge contacts/leads based only on fuzzy similarity.

## 8. Scoring ownership

The provisional deterministic formula lives in the PRD. If approved, FastAPI implements it in one tested service; React only renders the returned result; n8n may route using the API-provided band but must not recalculate it. No budget/property-fit scoring without verified inventory and business criteria.

## 9. API and integration boundaries

- Public customer endpoints: `/api/v1/public/...`; conversation access requires the protected server-issued session, not only a conversation ID.
- Staff endpoints: `/api/v1/sales/...`; authenticate active staff and verify role/action/record permissions.
- Internal endpoints: `/api/v1/internal/...`; service authentication, request-size limits, schema validation, idempotent callbacks.
- OpenAPI is the proposed canonical HTTP schema; n8n event schemas are versioned with `docs/11-n8n-workflow-specification.md`.

## 10. Reliability and recovery

- Use at-least-once delivery with idempotent consumers; do not claim exactly-once delivery.
- `delivered_to_n8n` means n8n accepted the event, not that AI or notification completed.
- Transient timeout/5xx/rate-limit errors: bounded exponential backoff with jitter. Permanent schema/auth failures: record, alert, and repair; do not retry indefinitely.
- Dispatcher claims expire so abandoned work can be reclaimed. Dead-letter events remain inspectable and replayable by an authorized operator.
- Replays must retain traceability and follow idempotency rules.
- Notification timeout with unknown outcome is recorded as `unknown`; choose provider reconciliation before blind resend.
- Failed Sheets export never affects lead capture.

## 11. Security, privacy, and observability

Follow `docs/09-security-privacy-reliability.md`. Requests/jobs carry correlation/event/lead/conversation IDs and safe status metadata. Do not log raw message text, full phone/email, secrets, or full prompts by default. Restrict n8n editor/history access and retention; separate credentials by environment.

## 12. Proposed repository shape

```text
primehomes-real-estate-lead-bot/
├── AGENTS.md
├── README.md
├── frontend/
├── backend/
│   ├── app/
│   ├── migrations/       # one canonical migration directory
│   └── tests/
├── worker/               # only if outbox/dispatcher runs as a separate process
├── n8n/
│   ├── workflows/
│   └── schemas/
├── tests/
│   ├── fixtures/
│   └── e2e/
└── docs/
```

Do not create a second `database/migrations/` directory. If the worker is folded into the backend deployment, remove the separate `worker/` directory and document how the worker process starts.

## 13. Pending architecture approvals

1. PostgreSQL as canonical store, hosting, backup plan, and restore owner.
2. Transactional outbox/dispatcher vs another durable queue design.
3. Authentication provider, customer session, role policy, and record-access boundaries.
4. AI vendor/model and data-processing review.
5. Notification provider, delivery semantics, and service-level target.
6. Exact migration/toolchain choices.

## 14. Acceptance checklist

- [ ] Lead and initial message commit before acknowledgement.
- [ ] Rollback cannot leave an outbox event for a nonexistent lead.
- [ ] Duplicate event delivery does not create duplicate messages or unintended side effects.
- [ ] Stale AI callback cannot overwrite a newer revision.
- [ ] Sales changes are not overwritten by background processing.
- [ ] Pipeline, processing, qualification, assignment, and notification state are separate.
- [ ] Dispatcher crash permits lease expiry and safe reclaim.
- [ ] Retry exhaustion produces an observable dead-letter event and controlled replay path.
- [ ] Database schema and OpenAPI agree on names, enums, nullability, and identifier types.
