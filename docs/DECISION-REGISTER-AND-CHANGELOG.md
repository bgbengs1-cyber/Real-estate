# Decision Register, Canonical Contract & Changelog

**Documentation baseline:** 1.0 review-corrected draft  
**Purpose:** Prevent people and agents from deriving different rules from different documents.

## 1. Canonical terms and state model

| Concept | Canonical field | Values/rule | Authority |
|---|---|---|---|
| Transaction intent | `transaction_type` | `buy`, `rent`, `sell`, `general_enquiry`, `unknown` | AI proposes; FastAPI validates; PRD owns semantics |
| Property category | `property_type` | `apartment`, `house`, `duplex`, `office`, `shop`, `land`, `other`, `unknown` | AI proposes; FastAPI validates |
| Timing | `timeline` | `immediate`, `within_1_month`, `within_3_months`, `researching`, `unknown` | Customer fact; backend validates |
| Sales pipeline | `pipeline_status` | `new`, `contacted`, `viewing_scheduled`, `negotiation`, `nurturing`, `won`, `lost` | FastAPI enforces; Sales acts |
| Technical processing | `processing_status` | `queued`, `processing`, `completed`, `needs_review`, `failed` | Backend/workflow outcome |
| Qualification | `qualification_status` | `incomplete`, `qualified`, `needs_review`, `disqualified` | Backend rules/human review |
| Assignment | `assigned_to_user_id` | nullable staff ID | FastAPI permissions/audit |
| Priority | `priority_score`, `priority_band` | score 0–100/null; `hot`, `warm`, `standard`, `unscored` | Deterministic backend rule, pending business approval |
| Human review | `review_required` | boolean | Backend policy |
| Outbox delivery | `outbox_status` | `pending`, `leased`, `delivered_to_n8n`, `retry_wait`, `dead_letter` | Dispatcher |
| Notification outcome | `notification_status` | `queued`, `provider_accepted`, `delivered`, `failed`, `unknown` | Integration/provider evidence |
| Message | `sender_type`, `sequence_number` | Persisted customer-visible/staff messages only; AI drafts stay in processing state; sequence orders messages | FastAPI/database |

### Non-negotiable interpretations

- `land` is a property type, not transaction intent.
- A lead is one distinct enquiry/opportunity; a contact may have multiple leads.
- A lead can be captured without verified contact details.
- Assignment and qualification are not pipeline statuses.
- Technical processing never changes pipeline status by itself.
- Timeline bands are non-overlapping: immediate ≤7 days; within 1 month = 8–30 days; within 3 months = 31–90 days; researching = no committed date; unknown = not stated/unclear.
- Seller intent is captured but remains human-reviewed/unscored in MVP; no automatic valuation or seller qualification.
- A score is a follow-up aid, not conversion probability or property fit.
- `delivered_to_n8n` means accepted for delivery to n8n, not successful AI completion.
- An AI draft is not customer-visible until FastAPI validates and persists it.

## 2. Decisions awaiting approval

| ID | Decision | Recommended option | What it blocks |
|---|---|---|---|
| D-01 | Canonical database | PostgreSQL primary; Sheets optional one-way export | Migrations, data access, backups, export |
| D-02 | Async delivery | Transactional outbox + monitored dispatcher or explicitly chosen durable alternative | Worker and retry implementation |
| D-03 | Authentication | Managed identity provider for Sales; protected customer conversation session | Production route/session controls |
| D-04 | AI provider/model | Choose provider after privacy/vendor review | Credentials, deployment, evaluation baseline |
| D-05 | Sales notification channel | Select email/chat/CRM/other | Notification workflow and SLA tests |
| D-06 | Numeric scoring | Approve PRD formula or disable score for first pilot | Score service, UI badges, automated routing |
| D-07 | Pipeline transition rules | Approve PRD transition matrix | Dashboard actions, API validation, tests |
| D-08 | Privacy rules | Approve purpose/notice, lawful-basis review, retention/deletion, vendor flows | Production use of real data |
| D-09 | Hosting/operations | Providers/regions, RTO/RPO, backup and incident owners | Deployment/runbook and launch gates |
| D-10 | Toolchain | TS/JS, runtime versions, package managers, DB/migration/test tools, CI | Verified setup commands and CI |
| D-11 | Seller flow | Capture seller intent, route to human review only in MVP | UI wording and acceptance tests |
| D-12 | Currency | Preserve original budget wording; only normalize currency when explicit or an approved, visibly labeled UI default applies | Schema, UI, AI normalization |

Until a decision is approved, dependent work must not silently treat the recommendation as final. Non-blocking synthetic scaffolding may proceed if it does not lock in the pending choice.

## 3. Cross-document change map

- **Taxonomy/status:** PRD, architecture, API, AI contract, UI, n8n schema, tests, AGENTS.
- **Database/migrations:** architecture, API, engineering standards, tests, runbook, AGENTS.
- **AI schema/prompt:** AI contract, n8n specification, API callback schema, test fixtures/evaluation.
- **Async/retry:** architecture, ADR, n8n spec, tests, security, runbook, README, AGENTS.
- **Auth/privacy/retention:** API, UI, security, tests, runbook, vendor configuration.
- **Toolchain/setup:** engineering standards, README, runbook, CI, AGENTS.

## 4. Pull request consistency checklist

- [ ] No conflicting enum/field names introduced.
- [ ] Status/priority changes update PRD/ADR/API/tests as needed.
- [ ] API, OpenAPI, React types, n8n payloads, and fixtures remain aligned.
- [ ] No direct database writes from n8n.
- [ ] Side-effect retry/duplicate/unknown-outcome behavior is explicit.
- [ ] Stale AI results cannot overwrite newer messages or Sales state.
- [ ] No unsupported availability/valuation claims.
- [ ] Vendor/retention/credential changes receive privacy/security review.
- [ ] No unverified command is presented as tested in README/runbook.
- [ ] All linked file paths exist.

## 5. Changelog — version 1.0 critical-review corrections

- Separated pipeline, processing, qualification, assignment, priority, outbox, message, and notification states.
- Corrected intent taxonomy: `land` is `property_type`, not transaction intent.
- Defined lead/contact/conversation and cautious duplicate handling.
- Added an explicit provisional score formula with no inventory-fit claims; numeric score must remain disabled until approved.
- Made timeline windows non-overlapping and specified the proposed qualification rule.
- Corrected budget semantics: point estimate vs explicit bounds, approximate/maximum/range relation, nullable unresolved currency, and preserved original wording.
- Aligned `sender_type` as the canonical message actor field; message IDs are unique per conversation for idempotent sends.
- Defined separate outbox event paths for free-text conversation messages and structured-only form submissions; structured-only intake skips AI extraction.
- Clarified that AI drafts are not persisted/customer-visible messages until validated by FastAPI; added customer-session metadata requirements.
- Added stale callback and per-conversation sequence requirements; UUID is not a chronological cursor.
- Defined separate roles for request `Idempotency-Key` and `client_message_id`.
- Made approval states for database, outbox, auth, AI provider, notifications, scoring, privacy, and toolchain explicit.
- Removed competing migration directories and duplicate AGENTS content.
- Added dedicated n8n workflow and AI extraction/evaluation documents.
- Split developer README from operational runbook.
- Marked setup/commands as unverified until real code and deployment exist.
