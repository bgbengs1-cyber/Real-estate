# 9. Security, Privacy & Reliability Requirements

**Version:** 1.0 review-corrected draft  
**Status:** Control baseline; not a legal compliance certification or proof of implementation.

## 1. Purpose and scope

Protect customer contact/property-enquiry data, prevent unauthorized access and side effects, and ensure enquiries survive external service failures. Data may flow through hosting, the AI provider, n8n execution history, notification providers, logs, and optional Google Sheets exports.

Applicable legal duties depend on PrimeHomes' circumstances, purposes, vendor locations, and actual deployment. Arrange qualified privacy/legal review and maintain current official references before production. This document is an engineering control plan, not legal advice or a claim of compliance.

## 2. Data classification and minimization

- **Public:** approved product copy and generic property guidance.
- **Internal:** workflow IDs, non-sensitive config descriptions, aggregate operations metrics.
- **Confidential/customer data:** name, phone, email, message text, location/budget preferences, conversation history, Sales notes.
- **Secrets:** passwords, access tokens, API keys, session tokens, signing keys, database credentials.

Collect only fields needed for enquiry handling/follow-up. Do not require contact details for initial capture by default. Avoid logging raw messages/contact details in generic logs, metrics labels, errors, analytics, or workflow names.

## 3. Privacy requirements

Before production, a named privacy/business owner must approve:

- Privacy notice/purpose language at collection.
- Appropriate lawful basis for each processing purpose, reviewed by qualified privacy/legal expertise.
- Whether separate consent is needed for direct marketing or non-essential channels.
- Data categories, recipients/processors, cross-border flows, retention, deletion, and data-subject request handling.
- AI vendor/model retention/training and whether prompts are retained by the provider.
- Google Sheets sharing and access policy if exports are enabled.

Maintain a data lifecycle inventory for the database, AI-provider requests, n8n execution history, application logs, notification records, Sheets, and backups. Deletion from the primary database does not automatically remove all copies. Define deletion propagation and backup expiration behavior. Do not invent retention periods in code; implement the approved schedule.

## 4. Identity and access control

### Customer

- Conversation IDs are identifiers, not credentials.
- Use a server-controlled protected session or equivalent design; protect tokens in production and never log them.
- Verify session-to-conversation ownership on each read/write.
- Rate-limit creation/message endpoints and restrict payload size.

### Sales users

- Production requires an approved identity provider; current provider is undecided.
- Check identity, account active state, role, and record/action authorization on every server request.
- Never trust a role or user ID supplied only by browser payload.
- Define agent/manager/operator scope, reassignment behavior, and disabled-account/session behavior before launch.
- Audit assignment, pipeline changes, overrides, privileged actions, and relevant security events.

### Service identities

- n8n-to-FastAPI calls require service authentication and least privilege.
- Separate credentials by environment and define rotation/revocation.
- Never place internal credentials in React, workflow JSON, Git history, screenshots, or logs.

## 5. Application/API security

- Validate request sizes, string lengths, types, enums, numeric bounds, and nested structures.
- Parameterize SQL; restrict DB network access; use least-privilege runtime roles.
- Configure HTTPS, CORS origins, secure cookies, CSRF controls where cookie auth requires them, security headers, and rate limits for the chosen deployment.
- Prevent mass assignment: endpoints may change only allowlisted fields.
- Avoid revealing the existence of restricted records to unauthorized callers.
- Scan dependencies and secrets where possible; keep dependencies updated.
- Return safe errors without stack traces, SQL details, environment variables, provider payloads, or secrets.

## 6. AI security and safe behavior

- Customer text and external content are untrusted data, not instructions that override system policy.
- Version the extraction schema and validate output. Reject unexpected keys/enums, invalid ranges, source message IDs outside the conversation, and stale revisions.
- Model replies are drafts. Do not display them until FastAPI applies policy/schema checks and persists them.
- AI may not expose prompts, other leads, Sales notes, credentials, hidden system messages, or logs.
- Do not provide unrestricted AI tools or SQL access. Future action tools require server authorization and human approval where consequential.
- Do not claim live availability, current prices, valuations, booked viewings, or `won`/`lost` without verified data/authorized action.
- Review AI vendor retention/training, data region, subprocessors, and contractual terms before sending real customer messages.

## 7. n8n and integration security

- Restrict n8n editor access to approved operators; separate environments.
- Authenticate webhooks; a hard-to-guess URL alone is not access control.
- Limit credentials/permissions to the minimum required.
- Minimize execution-history retention and redact payloads where possible while retaining enough safe metadata for support.
- Sanitize workflow exports before Git commit; do not commit credentials or execution data.
- Validate event schema/source IDs before external side effects.
- Permanent authorization/schema failures alert and stop rather than loop.
- Sheets exports use allowlisted columns, restricted access, and formula-like text escaping.
- Notifications contain minimal necessary information; prefer an authenticated dashboard link to full customer messages/contact details.

## 8. Lead priority safeguards

A score is an operational triage aid, not a verified conversion probability or measure of a person's worth. If enabled:

- Use the approved deterministic rule version and reason codes.
- Do not use sensitive or irrelevant traits.
- Do not silently exclude incomplete/contactless leads from Sales' queue.
- Permit authorized review/override with reason and audit trail.
- Monitor patterns by enquiry category using privacy-conscious metrics.
- Do not add budget-to-property fit without verified inventory and explicit criteria.

## 9. Reliability and side-effect safety

- Persist enquiry before AI, notification, or export work.
- Use a transactional outbox or other explicitly approved durable queue design.
- Assume at-least-once delivery and make consumers idempotent.
- Bound retries and distinguish transient, permanent, and unknown outcomes.
- Stale callbacks must not overwrite newer messages, customer corrections, or Sales decisions.
- Notification failure does not invalidate the lead; Sheets failure does not invalidate lead capture.
- Dead-letter work remains visible, access-controlled, and replayable only through documented procedures.

## 10. Backup, recovery, availability

The business owner must approve Recovery Time Objective (RTO) and Recovery Point Objective (RPO) based on business needs and cost. Operations must demonstrate through restore exercises that the chosen plan can meet the targets. Do not claim recovery readiness based only on having a backup file.

Establish encrypted backups, restricted access, retention/expiry, restore steps, migration compatibility, and periodic restore tests. Define what happens to in-flight outbox and notification work after restoration.

## 11. Logging, monitoring, and audit

- Include correlation/event IDs, safe error codes, duration, component, environment, and state changes.
- Do not log raw customer messages, full phone/email, access tokens, passwords, full prompts, or entire provider payloads by default.
- Audit consequential business changes with actor, action, resource ID, before/after values where appropriate, reason, time, and correlation ID.
- Alert on repeated 5xx/timeouts, queue age, dead-letter events, AI failure spikes, notification failure/unknown outcomes, failed backups, authorization anomalies, and abuse/rate-limit spikes.
- Choose alert thresholds, retention, dashboard, and owner before production.

## 12. Incident response and ownership

Assign real owners for incident lead, privacy/data requests, DB recovery, credential rotation, and n8n operations before launch. Minimum response: contain, preserve evidence safely, assess scope, notify accountable owners, follow legal/regulatory notification assessment, remediate, recover, and record lessons.

## 13. Production gates

- [ ] AuthN/AuthZ and record-level access tests pass.
- [ ] Customer session ownership checks pass.
- [ ] Secrets scanning and environment separation are configured.
- [ ] AI vendor/data-processing review is approved.
- [ ] Privacy notice, purpose/lawful basis review, retention, deletion, and request process are approved.
- [ ] n8n access/history retention and export sanitization are configured.
- [ ] Retry/idempotency/stale-result/duplicate-notification cases pass.
- [ ] Backup restore and failed-event recovery are demonstrated.
- [ ] Named incident/data-handling owners exist.
- [ ] RTO/RPO and notification SLA are approved and tested against deployment capacity.

## 14. Open decisions

Identity provider/session design; hosting/regions; AI provider/model; notification provider; data retention/deletion schedule; privacy copy and lawful basis review; Sheets access; RTO/RPO; queue/worker choice; incident owner. These must be resolved before production use of real customer data.
