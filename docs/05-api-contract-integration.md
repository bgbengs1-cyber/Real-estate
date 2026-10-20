# 5. API Contract & Integration Specification

**Version:** 1.0 review-corrected draft  
**Status:** Proposed contract. Mirror the reviewed schema in FastAPI OpenAPI and automated contract tests before implementation.

## 1. Contract principles

- FastAPI is the only API used by browser clients; browser code never calls n8n internals.
- JSON fields use `snake_case`; timestamps use RFC 3339/ISO 8601 with UTC (`Z`).
- IDs are opaque UUID strings. A UUID is not a chronological cursor.
- Use explicit `null`/`unknown` rather than guessed values.
- `202 Accepted` means the request was durably persisted and asynchronous processing queued; it does not mean AI, notification, or export is complete.
- Side effects must be idempotent or have an explicitly recorded unknown outcome.

## 2. Canonical enums

```text
transaction_type: buy | rent | sell | general_enquiry | unknown
property_type: apartment | house | duplex | office | shop | land | other | unknown
timeline: immediate (<=7 days) | within_1_month (8-30 days) | within_3_months (31-90 days) | researching | unknown
pipeline_status: new | contacted | viewing_scheduled | negotiation | nurturing | won | lost
processing_status: queued | processing | completed | needs_review | failed
qualification_status: incomplete | qualified | needs_review | disqualified
priority_band: hot | warm | standard | unscored
sender_type: customer | assistant | sales_agent | system
outbox_status: pending | leased | delivered_to_n8n | retry_wait | dead_letter
notification_status: queued | provider_accepted | delivered | failed | unknown
```

These are independent dimensions. Do not merge them into one generic `status`. The field `transaction_type` describes buy/rent/sell/general intent; `property_type=land` describes the property category. A server message is stored only when it is eligible to be returned to its intended audience; AI drafts are not exposed or represented as available messages. A pending optimistic message may exist locally in React before server acknowledgement.

Budget fields: `budget_amount`, `budget_min_amount`, `budget_max_amount`, `budget_relation` (`exact`, `approximate`, `minimum`, `maximum`, `range`, `unknown`), nullable `budget_currency`, `budget_period` (`one_time`, `monthly`, `yearly`, `unknown`), and `budget_text_original`. A point amount and explicit range bounds must not be confused. Keep currency null if ambiguous; a form may preselect NGN only when the UI visibly labels the currency and this default is approved. Never erase original wording.

## 3. Security boundary

- **Public/customer endpoints:** rate-limited; a protected server-issued session authorizes conversation access. A conversation UUID alone is not authorization.
- **Sales endpoints:** authenticated active staff identity, role check, and record/action-level authorization on every request.
- **Internal endpoints:** service-to-service authentication, schema validation, request limits, idempotency, and network restrictions where available.
- Apply HTTPS, CORS, cookie, CSRF, and token protections appropriate to the approved authentication/session design.

## 4. Standard error envelope

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid fields.",
    "details": [{"field": "budget_max_amount", "issue": "must be >= budget_min_amount when both bounds are present"}],
    "correlation_id": "e8e6b5a8-2e66-41b1-86af-d47d11d1e98d"
  }
}
```

Never include stack traces, tokens, internal prompts, SQL text, or unnecessary personal data. Suggested error codes: `validation_error`, `authentication_required`, `forbidden`, `not_found`, `conflict`, `idempotency_conflict`, `stale_result`, `rate_limited`, `dependency_unavailable`, `processing_failed`, `internal_error`.

## 5. Idempotency and message ordering

Two IDs have distinct jobs:

1. **`Idempotency-Key` header:** prevents duplicate execution of a mutation/request such as form submission or task creation. Store the scoped key, request hash, and original result. Reusing a key with a changed request hash returns `409 idempotency_conflict`. Expiry policy remains to be approved.
2. **`client_message_id` UUID:** identifies one logical message in one conversation. Enforce uniqueness on `(conversation_id, client_message_id)`. Reuse only for retries of the same message; create a new ID for a new message.

Messages receive a server-assigned increasing `sequence_number` per conversation. Paginate by `after_sequence`/`before_sequence`; never sort messages by UUID to infer chronology.

## 6. Public customer endpoints

### `POST /api/v1/public/conversations`

Starts a conversation and associated lead. The server creates/associates a protected session. Request:

```json
{"source_channel":"website_chat","initial_message":"Hello, I want to buy a house."}
```

Response `201 Created` after conversation, lead, and initial message commit:

```json
{
  "conversation_id":"3efb2a64-43b0-4ccb-9dbb-34eaab1c4ce9",
  "lead_id":"7ac251c0-e063-4a1d-b7d9-d5334fd3c590",
  "initial_message_id":"465f2f0e-24f3-4451-aeb0-710c813e36a7",
  "sequence_number":1,
  "processing_status":"queued",
  "created_at":"2026-10-13T13:00:00Z"
}
```

Use an idempotency key for repeat starts. The session credential is established through the chosen secure session mechanism, not returned as a secret in JSON.

### `POST /api/v1/public/leads`

Accepts a structured form; it may create a lead without a conversation when meaningful structured fields are supplied without free text. When `message` is present, FastAPI creates a conversation and stores the original message so AI evidence can reference it. Structured-only submissions retain customer-entered field provenance and skip AI extraction; they use the `lead.structured_submission_received` workflow event for any queued downstream work. Every path uses the same durable persistence/idempotency guarantees. Do not require phone/email for initial capture unless the approved product decision changes this.

Example:

```json
{
  "source_channel":"website_form",
  "message":"I need land around Ibadan below ₦20 million.",
  "name":null,
  "email":null,
  "phone":null,
  "transaction_type":"unknown",
  "property_type":"land",
  "location_text":"Ibadan",
  "budget_amount":null,
  "budget_min_amount":null,
  "budget_max_amount":20000000,
  "budget_relation":"maximum",
  "budget_currency":"NGN",
  "budget_period":"one_time",
  "budget_text_original":"below ₦20 million",
  "timeline":"unknown"
}
```

The UI may submit user-entered form values. AI-inferred values must use the internal processing contract, not masquerade as user input. Backend validates all values. When `message` is present, return the associated `conversation_id` and `initial_message_id`; for structured-only submissions these are null. Response `202 Accepted` after commit and creation of the appropriate outbox event:

```json
{
  "lead_id":"7ac251c0-e063-4a1d-b7d9-d5334fd3c590",
  "conversation_id": null,
  "initial_message_id": null,
  "pipeline_status":"new",
  "processing_status":"queued",
  "qualification_status":"incomplete",
  "priority_band":"unscored",
  "correlation_id":"e8e6b5a8-2e66-41b1-86af-d47d11d1e98d"
}
```

### `POST /api/v1/public/conversations/{conversation_id}/messages`

Request:

```json
{
  "client_message_id":"ed4f5b31-3dd7-4ec7-9797-41ed4a4c3225",
  "body":"My budget is around 80 million naira and I want to move in within two months."
}
```

The server verifies session ownership, validates size/format, commits the message and event, and returns `202 Accepted`:

```json
{
  "message_id":"f0e00b11-0429-48d9-9268-39e3ba2a22bc",
  "sequence_number":4,
  "processing_status":"queued",
  "conversation_revision":4,
  "poll_after_ms":1000
}
```

Do not report that the assistant replied until an assistant message has been validated and persisted.

### `GET /api/v1/public/conversations/{conversation_id}`

Requires protected customer session. Returns permitted processing state, latest revision, and customer-visible summary. Never expose internal notes, Sales-only contact data, scores, prompts, workflow payloads, or private failure details without explicit approval.

### `GET /api/v1/public/conversations/{conversation_id}/messages?after_sequence=4&limit=50`

Returns chronological persisted messages after the sequence number. Clamp `limit`; verify session ownership. Draft/queued assistant content is not available to display.

## 7. Sales endpoints

All `/api/v1/sales/...` routes require staff authentication, active account, permissions, and audit behavior where applicable.

- `GET /api/v1/sales/leads`: filter by pipeline/processing/qualification status, assignment, date, intent, property type, priority, review flag, and overdue task; stable pagination and deterministic ordering.
- `GET /api/v1/sales/leads/{lead_id}`: returns permitted lead, field provenance, messages, activities, notification outcomes, and tasks.
- `PATCH /api/v1/sales/leads/{lead_id}`: allowlist editable facts/contact data; require `expected_version` or ETag/If-Match.
- `PATCH /api/v1/sales/leads/{lead_id}/pipeline-status`: `new_status`, optional reason, and expected version; server enforces transition matrix.
- `PATCH /api/v1/sales/leads/{lead_id}/assignment`: assign/unassign only with permission; audit before/after.
- `POST /api/v1/sales/leads/{lead_id}/notes`: append note/activity; validate size and privacy.
- `POST /api/v1/sales/leads/{lead_id}/follow-up-tasks`: action type, `due_at`, owner, optional note.
- `PATCH /api/v1/sales/follow-up-tasks/{task_id}`: permitted task changes with concurrency checks.
- `POST /api/v1/sales/leads/{lead_id}/priority-override`: only if policy permits; require reason/audit. Score calculation remains backend-controlled.

No generic PATCH may write `processing_status`, raw score, audit fields, or other system-owned properties.

## 8. Internal FastAPI ↔ n8n contract

### Event envelope

```json
{
  "event_id":"d5aeb93c-e638-4a1f-8b75-3cb4f5e691f2",
  "event_type":"conversation.message_received",
  "schema_version":1,
  "occurred_at":"2026-10-13T13:00:00Z",
  "correlation_id":"e8e6b5a8-2e66-41b1-86af-d47d11d1e98d",
  "aggregate":{"lead_id":"7ac251c0-e063-4a1d-b7d9-d5334fd3c590","conversation_id":"3efb2a64-43b0-4ccb-9dbb-34eaab1c4ce9","input_revision":4},
  "data":{"input_kind":"conversation_message","message_id":"f0e00b11-0429-48d9-9268-39e3ba2a22bc"}
}
```

The sibling event `lead.structured_submission_received` uses the same envelope, with `aggregate.conversation_id=null`, `aggregate.input_revision` set to the lead/input revision, and `data.input_kind="structured_submission"`; it contains no AI-extracted data. Send IDs/minimal data. n8n fetches the allowlisted processing context from FastAPI through an authenticated route, instead of assuming the webhook payload contains complete trusted PII.

Internal routes to formalize in OpenAPI:

- `GET /api/v1/internal/processing-context?event_id=...`
- `POST /api/v1/internal/workflow-results/lead-processing`
- `POST /api/v1/internal/notifications/results`
- `POST /api/v1/internal/exports/results`

Every callback authenticates the caller, validates schema and associations, is idempotent, and checks input revision. Stale result returns `409 stale_result` (or a documented equivalent) and must not update the conversation or create another reply.

A processing result includes `event_id`, `schema_version`, `result_kind` (`ai_extraction` or `structured_submission`), `lead_id`, nullable `conversation_id`, `input_revision`, and an outcome. For `ai_extraction`, include candidate fields with provenance/source message ID/confidence, missing/ambiguous fields, and an optional assistant reply draft plus safe provider/prompt metadata. For `structured_submission`, do not invent an AI result; confirm the validated customer-entered fields and return no assistant draft unless a separately approved response-generation step ran. Hidden reasoning and credentials are prohibited.

## 9. Error and retry semantics

- `400/422`: invalid request/schema; do not retry unchanged.
- `401/403`: auth/permission failure; repair credentials/permissions; no blind retry loop.
- `404`: missing/invisible resource; do not leak existence to unauthorized caller.
- `409`: idempotency payload conflict, stale version, invalid transition, or stale AI result; reconcile rather than retry unchanged.
- `429`: honor `Retry-After` with bounded backoff.
- `5xx`/timeouts: may be transient; bounded backoff with jitter and stable idempotency identifiers.

Notification timeout after submission may mean `unknown`, not failed. Reconcile provider outcome before resending where possible.

## 10. Qualification, lifecycle, scoring, provenance

The proposed qualification rule (requires Sales approval): `qualified` only when processing completed, transaction type is `buy` or `rent`, property type and location are known, a usable normalized budget amount/bound and currency are available, a viable follow-up route exists, and no material conflict remains. Otherwise use `incomplete`; use `needs_review` for seller/unsupported intent, material conflict, stale/untrusted extraction, or processing failure. `disqualified` requires an authorized human action and reason. Do not let an LLM mark a lead disqualified.

Pipeline transitions are defined in the PRD and enforced by FastAPI. Processing state does not change pipeline state. Qualification and assignment remain separate. The backend computes score from an approved rule version; n8n/AI never recalculate it. Provenance precedence: authorized Sales correction > latest explicit customer statement > validated AI extraction > unknown/null, with history retained.

## 11. Contract acceptance

- OpenAPI matches FastAPI models and database constraints.
- Frontend types are generated or checked against OpenAPI in CI.
- Examples validate against schemas.
- Duplicate request returns the same logical result.
- Unauthorized access fails even with a known UUID.
- Stale callback/update cannot overwrite newer data.
- Public responses do not leak private Sales notes or internal workflow errors.
