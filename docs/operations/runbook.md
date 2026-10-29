# Operations Runbook — PrimeHomes Realty Lead Bot

**Version:** 1.0 review-corrected draft
**Important:** This is an operating plan. Verify commands against the actual repository, dependency lockfiles, hosting platform, and n8n version before treating this as executable.

## 1. Operating principles

- PostgreSQL is the proposed canonical store only after ADR-0002 approval; Sheets is downstream export in the proposed MVP.
- A success acknowledgement must follow durable capture.
- AI/notification/Sheets failures do not delete a lead.
- Do not replay external side effects blindly when provider outcome is unknown.
- Do not run destructive production commands without explicit approval, verified backup, and a rollback/recovery plan.

## 2. Service inventory

Maintain a deployment-specific table before pilot:

| Service | Purpose | Health signal | Owner | Secrets/config |
|---|---|---|---|---|
| React web app | Customer UI/Sales dashboard | HTTP/build availability | To assign | Public config only |
| FastAPI | API/business rules | readiness + DB connectivity | To assign | Approved secret store/env |
| PostgreSQL | Canonical records | connections, storage, backup status | To assign | DB secret store |
| Outbox worker (if approved) | Deliver durable events | heartbeat, queue age, dead-letter count | To assign | Service credentials |
| n8n | AI/integration orchestration | instance/workflow health | To assign | n8n credential store |
| AI provider | Extraction/draft replies | latency/error metrics | To assign | Provider secret store |
| Notification provider | Sales alerts | provider/attempt status | To assign | Provider secret store |
| Google Sheets (optional) | Reporting/export | export lag/failures | To assign | Restricted workspace credential |

Replace every “To assign” with an accountable role/person before production.

## 3. Local setup — verify after toolchain approval

1. Clone the repository and read `README.md` and `AGENTS.md`.
2. Install the exact Node/Python versions recorded in the approved toolchain manifest.
3. Copy `.env.example` to the approved local settings file; use only local/test credentials.
4. Start local PostgreSQL using the approved method (native service or container), create a least-privilege application database/user, and verify connectivity.
5. Install backend dependencies with the committed lockfile; run migrations from the single canonical directory (`backend/migrations/` if Alembic is selected).
6. Start FastAPI using the verified project command; check health and OpenAPI endpoints.
7. Install frontend dependencies with the committed lockfile and start React using the verified script.
8. Import/activate only sanitized development n8n workflows with test credentials. Ensure all webhook URLs point to local/staging, never production.
9. If ADR-0004 is accepted, start the dispatcher using its documented command and verify heartbeat/queue consumption.
10. Run unit, schema, integration, and smoke tests with synthetic fixtures.

Do not copy command examples into a final README until they match committed scripts and have been tested from a clean checkout.

## 4. Environment configuration

Maintain exactly one documented configuration source per process. `.env.example` contains variable names and fake placeholders, never real secrets. Validate required settings at startup without printing values. Public React variables must be non-secret.

The final variable names must come from the implemented settings models. Expect categories for environment name, API URL, database, customer session/auth, internal service authentication, n8n, AI provider/model, notification provider, optional Sheets, logging, and retention/feature flags. Do not invent final names before the settings module exists.

## 5. Smoke-test checklist

- [ ] FastAPI readiness checks database connectivity.
- [ ] Starting a conversation returns only after lead/conversation/message persistence.
- [ ] Repeating the same start/message request returns the same logical resource.
- [ ] Processing event appears in durable queue/outbox if enabled.
- [ ] n8n authenticates and accepts a synthetic event.
- [ ] Validated callback updates processing state and persists one assistant response.
- [ ] Stale result is rejected.
- [ ] Sales endpoint denies unauthenticated access.
- [ ] Notification outcome is recorded.
- [ ] Sheets export (if enabled) does not affect the canonical record.
- [ ] Logs contain IDs/status codes but not message body, full contact data, or secrets by default.

## 6. Incident triage

1. Record start time, environment, correlation/event/lead ID, symptoms, and affected service; avoid copying PII into incident channels.
2. Verify whether the lead/message exists in the canonical database.
3. Identify stage: API persistence, dispatcher, n8n, AI provider, callback validation, notification, or export.
4. Use safe error codes and timestamps; do not paste secrets or raw customer prompts into general logs.
5. Avoid retries when side-effect outcome is unknown until provider/internal state is reconciled.
6. Escalate data-integrity, unauthorized-access, privacy, or repeated dead-letter incidents to the named owner.
7. Record resolution, affected data, recovery action, and follow-up prevention tasks.

## 7. Failure playbooks

### 7.1 Lead persisted; no AI result

- Inspect `processing_status`, processing job/event IDs, attempts, age, and safe error code.
- Check worker heartbeat/queue age, n8n execution, provider status, and callback response.
- If pending, restore service; if transient, allow bounded retry.
- If dead-lettered, fix root cause and use the approved replay process.
- Confirm there is one accepted result/reply and that newer conversation revision did not make the result stale.

### 7.2 Lead exists; Sales not notified

- Inspect notification attempt state and distinguish `failed` from `unknown`.
- Check destination settings, provider limits, and n8n execution.
- For known failure, retry with the same logical notification identity where supported.
- For unknown outcome, reconcile with provider state/logs or request an operator decision; do not blindly resend.
- Confirm the lead remains visible in the Sales queue regardless of notification status.

### 7.3 Duplicate lead/message suspected

- Compare idempotency record, `client_message_id`, event ID, conversation ID, and timestamps.
- Do not auto-delete/merge; distinguish repeated request from a separate property opportunity.
- Fix uniqueness/dedup logic, add regression test, and reconcile downstream notifications/exports.

### 7.4 Repeated 4xx/5xx

- `400/422`: fix schema/payload; do not retry unchanged indefinitely.
- `401/403`: repair/rotate service credentials or permissions; stop rapid retry.
- `409`: fetch current state and reconcile stale/conflicting result; do not replay unchanged.
- `429/5xx/timeouts`: bounded backoff; inspect provider health and rate limits.
- Avoid exposing stack traces outside protected logs.

### 7.5 PostgreSQL unavailable

- Check provider/service status, network/DNS, connection limits, storage, and recent migrations.
- Do not return successful capture acknowledgements if writes cannot commit.
- Restore connectivity and verify transaction integrity and pending work recovery.
- Do not create Sheets as an improvised second canonical store without a deliberately designed failover architecture.

### 7.6 Sheets export lag/failure

- Confirm canonical records are present and unchanged.
- Inspect export attempt state, sheet IDs/permissions, quota response, and allowlisted mapping.
- Repair credentials/permissions/quota and replay idempotently.
- Verify formula-like user text was escaped and sheet access remains restricted.

### 7.7 Unsafe or incorrect AI response

- Identify conversation revision, prompt/schema/model version, and persisted message ID.
- If not persisted, block delivery and use an approved fallback/review path.
- If already sent, follow the correction/escalation policy; do not silently rewrite history.
- Preserve only necessary evidence securely, add an evaluation case, and consider review-first mode until fixed.

### 7.8 Outbox worker crash (if enabled)

- Check worker heartbeat and oldest pending event age.
- Inspect leases; do not clear one manually while a worker may still own it.
- Restart with the deployment's graceful procedure.
- Verify expiry/reclaim and safe duplicate handling.
- If dead-letter count grows, pause bulk replay and fix root cause first.

## 8. Safe replay policy

- Replay only after identifying the cause and classifying side effects.
- Keep event/job/resource IDs traceable. Retry the same logical operation with the same identity; any new replay event must link to its source and respect dedup rules.
- Do not replay a customer-facing response if the conversation revision has changed.
- Do not repeat notifications with unknown outcome until reconciled or explicitly approved.
- Never replay a production event using local/staging credentials.
- Record operator, reason, time, original state, and result.

## 9. Backup and restore

Before production, approve frequency/retention, encryption, access, RTO/RPO, and owner. Test restore to an isolated environment on an approved cadence. Verify key relationships, recent leads/messages, idempotency records, pending outbox work, and app readability.

After restoring, reconcile events that were in flight at backup time. Do not assume notifications or workflow calls are safe to replay without checking provider/idempotency outcomes.

## 10. Deployment and rollback

**Before release:** CI and staging E2E pass; auth/privacy controls are verified; backup/restore evidence is current; DB migrations are reviewed and compatible; n8n exports are sanitized and tested against non-production destinations; health checks, alert routes, owners, and rollback version are known.

**After release:** Check API errors/latency, queue age, dead-letter count, AI failures/stale callbacks, notification outcomes, DB health, and frontend errors. Run a synthetic smoke enquiry without notifying real customers.

Rollback if capture/data integrity/auth/security is impaired, failure/queue rates exceed approved thresholds, or unsafe customer responses are observed. A DB rollback may require a forward fix or restore rather than reversing destructive migrations; follow the reviewed migration plan.

## 11. Owners and decisions required before production

Assign named owners for API/app, database backups, dispatcher, n8n, AI vendor, notifications, security/privacy, and Sales follow-up queue. Approve hosting, auth provider, AI provider, notification SLA, retention/deletion, recovery objectives, and replay policy before launch.
