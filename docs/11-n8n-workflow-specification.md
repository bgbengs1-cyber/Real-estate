# 11. n8n Workflow Specification

**Version:** 1.0  
**Status:** Proposed workflow contract; align with deployed n8n version and approved architecture before import/activation.

## 1. Purpose and boundary

n8n coordinates asynchronous processing and external integrations. It is not the canonical database, API authorization layer, lead-scoring engine, or sales pipeline state machine. Canonical writes occur through FastAPI after validation.

## 2. Workflow inventory

| Workflow | Trigger/input | Responsibility | Success outcome | Failure outcome |
|---|---|---|---|---|
| `PH | Lead Processing | Extract and Qualify | v1` | Authenticated `conversation.message_received` or `lead.structured_submission_received` event | Fetch context; call AI only for free text; validate outcome and submit callback | Bounded retry; safe failure status; lead remains stored |
| `PH | Sales Notifications | Dispatch Alert | v1` | `sales.notification_requested` event after canonical commit | Send minimum necessary alert and report provider outcome | Record failed/unknown; no lead mutation |
| `PH | Reporting | Export Lead | v1` (optional) | `reporting.export_requested` event after canonical commit | Upsert allowlisted fields using stable key | Retry independently; no rollback of core workflow |

Use a new schema/workflow major version for breaking input/output changes.

## 3. Event envelope

```json
{
  "event_id":"uuid",
  "event_type":"conversation.message_received",
  "schema_version":1,
  "occurred_at":"RFC3339 UTC",
  "correlation_id":"uuid",
  "aggregate":{"lead_id":"uuid","conversation_id":"uuid","input_revision":4},
  "data":{"input_kind":"conversation_message","message_id":"uuid"}
}
```

For `lead.structured_submission_received`, use the same envelope shape with `conversation_id: null`, `input_revision` equal to the current lead/input revision, and `data.input_kind="structured_submission"`; no `message_id` is required. Example values are illustrative. A production event must validate against the versioned schema. Reject unsupported event types/versions before side effects. Use `event_id` as the logical event idempotency identity.

## 4. Workflow A — Lead extraction and response draft

1. Receive the event through an authenticated internal webhook.
2. Validate required fields, UUID format, event type, schema version, input kind, and revision.
3. Deduplicate by stable `event_id` using a durable receipt. Re-delivery must not create a second customer-visible reply.
4. Fetch authorized processing context from FastAPI; do not trust a webhook payload as unrestricted PII/context.
5. Check that the relevant input revision is still current; if stale, stop and report stale/handled. For conversation messages, compare the conversation revision; for structured-only submissions, compare the lead/input revision.
6. If `input_kind="conversation_message"`, call the configured AI provider with the versioned extraction contract and minimum context. If `input_kind="structured_submission"`, skip AI extraction; the fields were entered by the customer and must be validated by FastAPI.
7. For AI output, validate JSON/schema and reject invalid enums, ungrounded amounts, invented contact details, invalid source-message references, and malformed responses.
8. Submit one result callback containing `event_id`, `result_kind`, `input_revision`, candidate facts where applicable, missing/ambiguous fields, optional draft reply, and safe diagnostics. Never include hidden reasoning or secrets.
9. FastAPI revalidates, merges facts, calculates priority if approved, decides if reply is safe, persists accepted results, and updates processing state.
10. A stale/conflict callback is not retried indefinitely; record it as stale/handled.
11. Emit safe metrics such as duration, outcome code, retry count, schema version, and correlation/event ID.

### Prompt/data safety

Customer message content is untrusted data, not workflow instructions. Keep product instructions separate. Do not grant the extraction workflow unrestricted tools or direct SQL access. If retrieval is added later, retrieved content must also be treated as untrusted input.

## 5. Workflow B — Sales notification

1. Receive an authenticated event after canonical business data is committed.
2. Validate event/lead identity, schema, and permitted notification purpose.
3. Fetch a minimal safe summary from FastAPI if needed.
4. Send through the approved provider/channel.
5. Use provider idempotency/client reference if supported.
6. Report an attempt ID and status: `provider_accepted`, `delivered` (only when provider confirms), `failed`, or `unknown`.
7. If a timeout occurs after submission, do not assume it failed; reconcile or record `unknown` for a controlled decision.

Notification should generally contain a lead reference, approved priority/reason, and authenticated dashboard link—not unnecessary message/contact detail.

## 6. Workflow C — Optional Sheets export

- Run only after canonical transaction commit.
- Use allowlisted columns and stable row identity (`lead_id` plus export version/event ID) to upsert rather than append duplicates.
- Escape formula-like user text; restrict sheet access.
- Report export outcome separately from processing status.
- Sheets outage must not change lead status or customer acknowledgement.
- Sheets edits do not write back to PostgreSQL in the MVP proposal.

## 7. Retry taxonomy

| Failure | Action |
|---|---|
| Temporary network timeout, provider 5xx, retryable 429 | Bounded exponential backoff with jitter; honor `Retry-After` |
| Invalid event/schema/field | Permanent failure; safe error and operator review |
| 401/403 service authentication | Stop rapid retries; alert owner and repair credentials/permissions |
| Unsupported schema version | Quarantine/dead-letter until compatible workflow or approved replay |
| Stale conversation result | Mark stale/handled; no repeated retry or assistant reply |
| Callback timeout after possible commit | Retry same event/result identity; FastAPI callback must be idempotent |
| Notification outcome unknown | Reconcile provider status before deliberate resend |
| Sheets outage/rate limit | Retry export independently; monitor queue age |

Maximum attempts, exact backoff schedule, retention, and alert thresholds require approval and deployment tests. Every retryable path must reach a terminal/dead-letter outcome.

## 8. Credentials and execution data

- Store credentials in n8n credential store/approved secret manager, separated by environment.
- Never commit credential-bearing exports or raw execution data.
- Restrict editor/execution-history access; set retention consistent with the privacy decision.
- Redact or disable unnecessary payload retention while preserving safe operational metadata.
- Authenticate internal webhooks; random URL obscurity is not sufficient.

## 9. Required workflow tests

Test valid/malformed/unsupported-version/duplicate events for both free-text and structured-only intake; assert structured-only intake skips AI; invalid AI JSON/enums/source IDs; provider timeout/429/5xx and permanent 401/403; callback commit followed by timeout/retry; stale callback after a newer message or lead revision; notification success/failure/unknown/duplicate; Sheets outage/formula-like input/replay; absence of credentials and PII in committed exports.

## 10. Workflow release checklist

- Workflow and schema version are clear.
- Input/output contract matches API/AI documents.
- Credentials are mapped in target environment without exporting secrets.
- Test webhooks/destinations are non-production.
- Success and failure cases are exercised.
- Deactivation/rollback procedure is documented.
- Owner, activation time, change summary, and test result are recorded.
