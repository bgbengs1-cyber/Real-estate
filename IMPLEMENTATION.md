# IMPLEMENTATION — Task 001: Public Lead Intake API

- **Applies to:** [`TASK.md`](TASK.md) — Implement `POST /api/v1/public/leads`
- **Status:** Proposed implementation plan; database-backed work depends on the approval gates in `TASK.md`.
- **Architecture source:** [`docs/02-system-architecture-data-design.md`](docs/02-system-architecture-data-design.md)
**HTTP contract source:** [`docs/05-api-contract-integration.md`](docs/05-api-contract-integration.md)

## 1. Implementation goal

Build the smallest dependable FastAPI vertical slice that accepts an enquiry, validates the payload, persists one canonical lead and its associated intake records, records durable downstream work, and returns the documented acknowledgement. Do not put AI processing, sales notification, or Google Sheets calls into the request handler.

## 2. Pre-implementation gates

Before implementing persistence or side-effect behavior, verify the decision register and accepted ADRs:

| Gate | Required decision | Why it matters |
|---|---|---|
| G-01 | D-01 approves PostgreSQL as canonical DB | Determines transaction, constraints, tests, connection lifecycle, migrations, and backup expectations. |
| G-02 | D-02 approves transactional outbox/dispatcher or a documented durable alternative | Determines how this endpoint safely schedules async work. |
| G-03 | D-03 approves customer session handling for message-based intake | Prevents creating a public conversation that is accessible by UUID alone. |
| G-04 | D-10 approves language/runtime/package/migration/test toolchain | Avoids incompatible lockfiles and setup commands. |
| G-05 | Idempotency scope and expiry are agreed | Prevents duplicate or conflicting requests across retries. |

A human reviewer must record the selected options in the ADRs/decision register before the agent proceeds past the affected gate. Do not invent approvals based on this plan.

## 3. Proposed module placement

Use the canonical structure from `docs/06-engineering-standards.md`; the exact filenames may be adapted to the approved scaffold without changing responsibilities.

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── routes/
│   │       └── public_leads.py
│   ├── schemas/
│   │   └── lead_intake.py
│   ├── domain/
│   │   └── lead_intake.py          # domain rules/types as appropriate
│   ├── services/
│   │   └── lead_intake.py          # use case orchestration
│   ├── repositories/
│   │   ├── leads.py
│   │   ├── conversations.py
│   │   ├── idempotency.py
│   │   └── outbox.py
│   ├── integrations/
│   │   └── ...                     # no live AI call in this task
│   └── core/
│       ├── config.py
│       ├── errors.py
│       └── logging.py
├── migrations/                     # single canonical migration directory if selected
├── tests/
│   ├── unit/
│   ├── api/
│   └── integration/
└── pyproject.toml                  # only after toolchain approval
```

Do not create every folder as an empty abstraction if the selected scaffold does not require it. Keep route handlers thin; use a service/use-case function to coordinate validation, transaction boundaries, idempotency, and event creation.

## 4. Request-to-response flow

### 4.1 Common preflight

1. Generate or accept a validated correlation ID according to the API contract; do not trust arbitrary oversized log data.
2. Apply public endpoint rate limits and request-size limits at the chosen API/middleware/gateway boundary.
3. Parse the JSON into a strict Pydantic request model (or approved equivalent). Reject unexpected system-owned fields.
4. Validate `source_channel`, taxonomy enums, message length, contact format, budget relation/bounds, and structured-only meaningful-input rules.
5. Compute a deterministic request hash from a normalized representation of the validated request. Do not include transient headers or generated IDs in the hash unless the approved policy requires it.
6. Check the persisted idempotency record. If a completed matching key exists, return the original logical response. If the key is reused with a different hash, return `409 idempotency_conflict`.
7. Start the persistence transaction only after the request passes validation.

### 4.2 Message-based request

When `message` contains non-whitespace text:

1. Create the lead with its canonical initial states and customer-stated structured fields/provenance, if any.
2. Create or associate a contact only according to the approved contact-linking rule. Do not fuzzy-merge identity based on text or location. If identity is uncertain, keep the lead's contact link null and preserve the submitted details according to the approved data model.
3. Create a conversation linked to the lead and establish the approved protected session. The session secret must not appear in ordinary JSON or logs; use the approved secure cookie/session design.
4. Insert the original inbound message as `sender_type=customer` and assign `sequence_number=1`. Advance the conversation revision as defined by the canonical schema.
5. Create a processing-job/outbox record for `conversation.message_received`, with a stable `event_id`, `correlation_id`, current conversation revision, and initial message ID.
6. Insert the idempotency record and the exact response to be replayed on duplicate request.
7. Commit all records atomically.
8. Only after commit, return the contract-defined `202 Accepted` body and any approved session cookie/header. Do not wait for the AI provider or n8n execution.

### 4.3 Structured-only request

When `message` is absent or null:

1. Require at least one meaningful enquiry field. Contact information alone is not enough.
2. Create the lead and store each submitted field as customer-stated information with provenance/history according to the approved data model.
3. Do not create a conversation or message; response `conversation_id` and `initial_message_id` are null.
4. Create the processing-job/outbox event `lead.structured_submission_received` with `conversation_id=null`, `data.input_kind="structured_submission"`, a current lead/input revision, and no message ID.
5. The downstream contract may handle notification/reporting and any required completion bookkeeping, but **must skip AI extraction** for this input kind.
6. Store idempotency data and the response in the same transaction, commit, then return `202 Accepted`.

### 4.4 Transaction failure

If any required insert (lead, conversation/message as applicable, idempotency record, processing job/outbox event) fails, roll the entire transaction back. Return a safe error response; do not return success or pretend work has been queued. Do not synchronously call n8n before commit to compensate for a missing durable event record.

## 5. Suggested data responsibilities

Exact SQL types, constraints, foreign keys, indexes, deletion rules, and migrations must follow the approved schema. The logical responsibilities are:

- `leads`: source channel, normalized customer-entered attributes, separate pipeline/processing/qualification states, priority initialized to unscored, review flag, version, timestamps.
- `contacts`: optional identity record, only linked when policy permits; a contact may own multiple distinct leads.
- `conversations`: optional for structured-only submissions; protected session association and monotonically increasing revision.
- `messages`: original inbound text, customer actor, sequence number, created timestamp. The unique `(conversation_id, sequence_number)` constraint protects ordering; idempotency must also prevent duplicate first messages.
- `property_requirement_facts` or approved equivalent: field, value, provenance `customer_stated`, relevant source/revision, actor, timestamp, supersession history.
- `processing_jobs`: lead ID, nullable conversation ID, `input_kind`, input revision, processing state, bounded attempt metadata.
- `outbox_events`: stable event ID/type/schema version, aggregate ID/revision, payload, delivery state/attempt/lease data if the outbox architecture is approved.
- `idempotency_records`: scoped key, request hash, created/expiry times, and reference/serialized response sufficient to replay the original result.

Do not use a single generic `status` field for unrelated state dimensions. Do not store monetary values in binary floating point. Do not write canonical tables directly from n8n.

## 6. API schema and response rules

Use [`docs/05-api-contract-integration.md`](docs/05-api-contract-integration.md) as the source for exact field names and response envelopes. Ensure the implemented FastAPI schema yields the documented semantics:

- `202 Accepted` only after durable commit and durable async event recording.
- Message path returns `lead_id`, `conversation_id`, `initial_message_id`, `pipeline_status`, `processing_status`, `qualification_status`, `priority_band`, and `correlation_id` as specified by the contract.
- Structured-only path returns `conversation_id=null` and `initial_message_id=null`.
- Initial priority is `unscored`; `priority_score` remains null until the score formula is approved and implemented as deterministic backend logic.
- Errors use the shared envelope with a safe `code`, customer-safe message, field details when appropriate, and `correlation_id`.
- Same idempotency key + same payload returns the same logical resource IDs/result. Same key + different payload returns HTTP 409 `idempotency_conflict`.
- Exact status codes for validation, rate limiting, dependency outage, and internal failure must match the reviewed API contract; update the contract first if implementation proves a correction is needed.

## 7. Business rules to keep out of the route handler

Implement reusable validation/service functions for the following:

- A structured-only payload must describe an enquiry, not merely provide contact information.
- `transaction_type` and `property_type` remain independent; `land` is a property type.
- Preserve raw budget wording. Do not infer currency from ambiguous free text. Do not convert an approximate point amount into a maximum bound.
- A customer may submit without a phone number/email.
- Do not auto-merge a lead based on fuzzy similarity. This endpoint creates one distinct enquiry unless an explicitly approved idempotent retry returns the existing result.
- Seller intent is captured and flagged/routed for human review according to the PRD; do not run automated valuation or claim the system supports a seller qualification workflow.
- AI extraction, numeric priority scoring, notification dispatch, and Sheets export are not implemented in the HTTP request function.

If the meaning of “meaningful enquiry field,” contact linking, seller review flag, or structured-only processing completion is not sufficiently specified for a deterministic test, open a decision and get review instead of silently embedding assumptions.

## 8. Security and privacy controls

- Validate all client fields at the API boundary.
- Apply the approved rate-limit and request-size policy to public intake.
- Use parameterized ORM/query APIs; never build SQL by concatenating customer input.
- Keep database and service credentials out of frontend configuration, source control, logs, and error responses.
- Redact contact details and message bodies from routine logs unless an approved, access-controlled diagnostic need exists.
- Never trust client-supplied role, pipeline status, processing status, priority score, provenance, or internal event IDs.
- If session credentials are created, use only the selected secure transport/storage pattern and do not return them in ordinary response JSON.
- Ensure CORS allows only approved frontend origins in non-development environments.
- No real customer data in unit/integration fixtures; use synthetic lead examples.

## 9. Test plan

### Unit tests

- Valid request with free text.
- Valid structured-only request.
- Whitespace-only message.
- Empty request / contact-details-only request.
- Invalid enum and unsupported extra fields.
- Approximate budget versus explicit maximum/range.
- Currency unresolved stays null.
- `budget_min_amount > budget_max_amount` is rejected when both bounds are supplied.
- `land` accepted as property type without forcing transaction type.
- Input normalization/hash remains stable across equivalent JSON key ordering.

### API tests

- Message path response contains non-null conversation/message IDs; structured-only response uses null IDs.
- Response is not successful when persistence fails.
- Request validation returns the standard error shape.
- Internal exception does not leak stack trace, raw SQL, configuration, or secrets.
- Rate-limit behavior matches the configured policy.

### Database/integration tests (after DB decision)

- Lead + associated records + idempotency + outbox/job are committed atomically.
- Forced failure at each insert point rolls back all required records.
- Same key/same payload returns existing logical result.
- Same key/different payload returns 409.
- Concurrent identical submissions create one logical result, enforced by database constraints.
- Outbox dispatcher failure after commit does not remove the lead.
- Message event includes correct lead/conversation/message IDs and revision.
- Structured-only event has null conversation ID and skips AI extraction.
- PII does not appear in routine test-captured logs.

### Contract tests

- Response and error schemas match `docs/05-api-contract-integration.md`.
- Event payloads match `docs/11-n8n-workflow-specification.md`.
- Any field/enum change is reflected in API schema, persistence constraints, fixtures, and docs.

## 10. Implementation sequence

1. Inspect the actual repository state and all canonical references; report missing files and current branch changes.
2. Confirm G-01 through G-05. If any foundational gate is pending, do not invent the decision; isolate code/tests that do not lock it in.
3. Establish and verify the approved Python/toolchain configuration.
4. Create FastAPI app factory/entry point, configuration validation, safe error handling, and health endpoint as the minimal scaffold.
5. Implement request/response schemas and pure validation functions. Add unit tests before persistence work.
6. Implement database models/repositories and migrations according to the accepted database/migration decision.
7. Implement the transaction-aware intake service, idempotency, and accepted durable event mechanism.
8. Add the route and rate-limiting/session integration required by the approved security design.
9. Add API, transaction rollback, concurrency/idempotency, and event-schema tests.
10. Run format/lint/type/test/migration/schema checks using actual configured commands; record exact results.
11. Review the full diff for unsafe logging, incorrect status names, duplicate logic, missing rollback, stale revisions, secret leakage, and contract drift.
12. Update only documents affected by discovered contract changes, and have a human approve changes to ADRs/security-sensitive behavior.

## 11. Definition of done

- `POST /api/v1/public/leads` conforms to the reviewed API contract for both message-based and structured-only intake.
- A valid request is acknowledged only after required durable records commit.
- Idempotency holds under retries and concurrent duplicate requests.
- Outbox/queue behavior matches the approved durable-delivery decision; no synchronous AI or notification call is required for capture success.
- Customer-stated fields and original text are preserved with provenance.
- No guessed currency, transaction intent, property availability, numerical score, or contact verification is introduced.
- Unit/integration/contract tests pass, and exact commands/results are recorded.
- Security and privacy checklist is reviewed; no real customer data or secrets enter the repository.
- Documentation, API schemas, database constraints, event payloads, and tests agree.
- Any unresolved decision or untested behavior is clearly listed in the completion report.
