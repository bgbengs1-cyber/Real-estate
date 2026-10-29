# 1. Product Requirements Document (PRD)

**Product:** PrimeHomes Realty — Real Estate Lead Bot  
**Version:** 1.0 review-corrected draft  
**Status:** Requirements baseline for stakeholder approval  
**Owner:** Product owner (to be named)  
**Collaborators:** Sales lead, product designer, frontend engineer, backend engineer, automation engineer, QA, privacy/security owner

## 1. Executive summary

PrimeHomes Realty receives prospective customers' property enquiries through its website. Messages vary from structured requests (“3-bedroom apartment in Lekki, around ₦80 million”) to vague messages (“I want to buy a house”). Manual handling can delay responses, lose context, and make follow-up inconsistent.

The Real Estate Lead Bot captures enquiries, preserves original messages, extracts candidate requirements, asks clarification questions when useful, stores the enquiry, calculates a transparent rule-based follow-up priority, notifies Sales through the approved channel, and provides a dashboard for assignment and progress tracking.

**This is a small business system, not merely an email automation.** Reliable intake, identity boundaries, access control, auditable state changes, retries, and recoverability are product requirements.

## 2. Problem statement

Sales staff currently need to interpret messages, collect property preferences, record contacts and budgets, identify urgency, and remember follow-up. The stated possibility of 200 messages per day is a planning assumption to validate, not a measured traffic baseline.

## 3. Goals and non-goals

### 3.1 Goals

- Durably capture valid enquiries before depending on AI, notifications, or reporting integrations.
- Extract transaction intent, property type, location, budget, relevant property details, timeline, and contact data when present.
- Keep unknown, ambiguous, and customer-corrected values distinct from confirmed values.
- Ask concise clarification questions without trapping customers in an endless questionnaire.
- Give Sales a searchable queue, assignment, status updates, notes, and follow-up tasks.
- Prioritize work with explainable backend rules, not an LLM's unsupported numerical judgment.
- Make processing failures visible and recoverable without losing leads or duplicating side effects.

### 3.2 Non-goals for the first MVP

- Verified live property search, pricing, or availability; no verified inventory source is defined yet.
- Automated property valuation or a dedicated seller marketing workflow.
- Automated negotiation, offers, booking confirmation, or closing a deal.
- Autonomous AI decisions to mark leads `won` or `lost`.
- Two-way synchronization between SQL and Google Sheets.
- Additional inbound channels (WhatsApp, email, social media) unless separately approved.
- A full CRM replacement, commission engine, or property listing management system.

Seller enquiries may be captured and detected, but the MVP routes them for human review. Do not present automated seller qualification or valuation as supported functionality.

## 4. Users and roles

- **Prospective customer:** submits a form or chats without needing an account.
- **Sales agent:** views permitted leads, adds notes, schedules follow-up, and updates pipeline status.
- **Sales manager:** manages assignments and team queue; may reopen closed leads with a recorded reason.
- **System operator:** maintains deployments, n8n workflows, credentials, monitoring, and recovery.
- **Product/engineering/QA:** builds and verifies the system using synthetic data and approved requirements.

The identity provider and exact role/record permissions remain open decisions. Production authorization must never rely on a client-supplied role value.

## 5. MVP journeys

1. Customer starts web chat or submits a lead form.
2. FastAPI validates and durably stores the enquiry/message.
3. The API acknowledges persistence and returns a processing state; it does not claim AI or notification work is already complete.
4. An asynchronous workflow requests AI extraction and a draft response.
5. FastAPI validates the result, stores accepted normalized fields and any customer-visible reply, computes priority if scoring is approved, and records processing outcome.
6. Missing/ambiguous fields trigger a concise clarification or human-review route.
7. The configured integration alerts Sales for eligible events.
8. Sales searches, assigns, reviews, updates status, adds notes, and schedules follow-up.
9. Failures are visible and recoverable.

## 6. Canonical domain model

- **Contact:** a person/contact identity. It may be unknown initially for an anonymous chat.
- **Lead/opportunity:** one distinct commercial enquiry or property need. A contact may have multiple leads; a new property need must not silently overwrite an existing opportunity.
- **Conversation:** a thread of messages associated with one lead.
- **Message:** one inbound customer message, persisted assistant reply, or authorized sales message.
- **Pipeline status:** business progress managed by Sales.
- **Processing status:** technical state of AI/workflow processing.
- **Qualification status:** whether enough reliable information exists for the current sales process.
- **Assignment:** lead owner; not a pipeline status.
- **Priority score/band:** deterministic follow-up aid, not a verified probability of conversion.

### 6.1 Taxonomy

- `transaction_type`: `buy`, `rent`, `sell`, `general_enquiry`, `unknown`.
- `property_type`: `apartment`, `house`, `duplex`, `office`, `shop`, `land`, `other`, `unknown`.
- `timeline`: `immediate` (intends to act within 7 days), `within_1_month` (8–30 days), `within_3_months` (31–90 days), `researching` (no committed timeframe), `unknown` (not stated/unclear).

“Land” is a property type, not a transaction type. Seller intent is captured and routed to human review in the MVP.

### 6.2 Independent statuses

**`pipeline_status`** (Sales-owned): `new`, `contacted`, `viewing_scheduled`, `negotiation`, `nurturing`, `won`, `lost`. `won` and `lost` require authorized human action and audit history.

**`processing_status`** (system-owned): `queued`, `processing`, `completed`, `needs_review`, `failed`.

**`qualification_status`:** `incomplete`, `qualified`, `needs_review`, `disqualified`.

Initial qualification rule (proposed for Sales approval): `qualified` only after processing is completed, transaction is explicitly `buy` or `rent`, property type and location are known, a usable budget amount is stated, a viable follow-up route exists (validated contact method or active replyable session), and no material conflict remains. `incomplete` means an otherwise supported buyer/renter enquiry lacks one or more of those details. `needs_review` applies to seller/general/unsupported intent needing human action, materially conflicting values, stale/untrusted extraction, or AI processing failure. `disqualified` is a human Sales action with a reason (for example spam/out-of-scope), never an LLM-only decision. Review with Sales before enforcing this exact rule.

**`priority_band`:** `hot`, `warm`, `standard`, `unscored`. Use separate `review_required` and qualification status to represent uncertainty; `review` is not a priority band.

A lead can be `pipeline_status=new`, `processing_status=completed`, `qualification_status=incomplete`, and unassigned at the same time. Never use `processing` as a Sales pipeline status.

## 7. Functional requirements

Priority: **P0** required for the first reliable MVP; **P1** required for pilot; **P2** later.

### 7.1 Intake and conversation

- **FR-001 (P0):** Accept web form enquiries with a free-text message and/or meaningful structured enquiry fields. When free text exists, preserve it in a conversation/message record; structured-only submissions use customer-stated field provenance and skip AI extraction.
- **FR-002 (P0):** Start a web conversation and persist each inbound message before asynchronous processing.
- **FR-003 (P0):** Preserve original text alongside normalized extraction.
- **FR-004 (P0):** Acknowledge only after transaction commit. `202 Accepted` means stored and queued, not processed.
- **FR-005 (P0):** Prevent duplicate submissions using persisted idempotency.
- **FR-006 (P1):** Read persisted conversation messages and processing state through a protected session.

### 7.2 Extraction and clarification

- **FR-007 (P0):** Extract candidate transaction type, property type, location, budget, applicable property details, timeline, name, email, and phone when explicit.
- **FR-008 (P0):** Represent missing/unknown values as `unknown` or `null`; never fabricate them.
- **FR-009 (P0):** Track field provenance: `customer_stated`, `ai_extracted`, `sales_corrected`, or `system_derived`.
- **FR-010 (P0):** Backend validates AI output against schema, the relevant input revision (conversation revision for chat, lead/input revision for structured submissions), and policy before persisting fields or displaying a reply.
- **FR-011 (P1):** Ask at most one concise clarification question at a time; stop repetitive questioning and route to Sales when appropriate.
- **FR-012 (P0):** Never claim live availability, current listing prices, approved viewings, or sales decisions without a verified source/authorized action.

### 7.3 Identity and persistence

- **FR-013 (P0):** Persist anonymous enquiries without requiring phone/email at initial capture.
- **FR-014 (P0):** Allow later contact details to be linked to the existing lead/conversation after validation.
- **FR-015 (P0):** Keep request idempotency, conversation identity, and business lead deduplication separate.
- **FR-016 (P0):** Never auto-merge uncertain identities based on similar text/location; flag for review.
- **FR-017 (P1):** Allow a contact to have multiple distinct leads without overwriting an earlier property need.

### 7.4 Qualification and priority

- **FR-018 (P0):** Keep qualification separate from pipeline and processing states.
- **FR-019 (P1):** Implement an explainable deterministic score only after the formula is approved; numeric score may remain disabled for the first build.
- **FR-020 (P0):** Invalid, stale, or failed extraction must not fabricate a score or overwrite newer data.
- **FR-021 (P1):** Record score, reason codes, rule version, and manual overrides.

### 7.5 Sales and notifications

- **FR-022 (P1):** Provide authenticated Sales list/detail/search.
- **FR-023 (P1):** Support assignment, notes, follow-up tasks, and valid pipeline transitions.
- **FR-024 (P1):** Audit assignment, status changes, overrides, and follow-up completion.
- **FR-025 (P1):** Notify the approved destination and persist each attempt/outcome.
- **FR-026 (P1):** A notification failure never deletes, rolls back, or invalidates a stored lead.

### 7.6 Operations

- **FR-027 (P0):** Each asynchronous event has a stable event ID, event/schema version, correlation ID, attempt count, and terminal failure path.
- **FR-028 (P0):** Bound retries and distinguish transient from permanent failures.
- **FR-029 (P0):** Protect internal callbacks and reject malformed/unauthenticated requests.
- **FR-030 (P1):** If enabled, export allowlisted fields one-way to Google Sheets after canonical commit.

## 8. Provisional priority formula

This formula is a concrete review proposal, not an approved commercial policy. Product Owner and Sales Manager must approve it before scores affect routing. Do not add budget-to-inventory fit without verified inventory and explicit business criteria.

| Dimension | Rule | Max |
|---|---|---:|
| Intent clarity | 20 for explicit `buy`/`rent`; 0 for `unknown`. `sell` and `general_enquiry` are routed to human review and remain unscored in the MVP | 20 |
| Timeline | `immediate`=30; `within_1_month`=25; `within_3_months`=15; `researching`=5; `unknown`=0 | 30 |
| Completeness | +5 each for known transaction type, property type, location, usable budget (a stated point amount or bound with currency resolved), and applicable property detail | 25 |
| Follow-up route | 15 for validated phone/email; 10 for an active replyable web conversation only; 0 if no viable route | 15 |
| Explicit urgency | 10 if customer explicitly requests prompt contact/viewing/callback; otherwise 0 | 10 |
| **Total** | Deterministic sum, 0–100 | **100** |

Proposed bands: `hot` 70–100, `warm` 40–69, `standard` 0–39. If extraction fails, results conflict materially, the result is stale, or human review is needed—including `sell` and `general_enquiry` in the MVP—use `priority_band=unscored`. Missing contact details alone must not discard a lead. Store score version and reason codes. If scoring is not approved, do not show a numeric score or fake bands.

## 9. Proposed pipeline transitions

- `new` → `contacted`, `nurturing`, `lost`
- `contacted` → `viewing_scheduled`, `negotiation`, `nurturing`, `won`, `lost`
- `viewing_scheduled` → `contacted`, `negotiation`, `nurturing`, `won`, `lost`
- `negotiation` → `contacted`, `nurturing`, `won`, `lost`
- `nurturing` → `contacted`, `viewing_scheduled`, `negotiation`, `won`, `lost`
- `won`/`lost` → no ordinary transition; manager-only reopen with reason and audit.

Sales Manager approval is required. FastAPI enforces transitions; React only presents them; n8n must not directly mutate status.

## 10. Non-functional requirements and measurement

All numeric targets remain provisional until the owner approves the measurement protocol.

- **Durable capture rate:** valid submissions whose canonical transaction commits. Queued/dead-letter work is not equivalent to a committed lead.
- **Acknowledgement latency:** request receipt to acknowledgement after commit; report p50 and p95. Proposed p95 ≤2 seconds under an agreed pilot load, subject to measurement.
- **Extraction quality:** field-level exact/acceptable-match rate against a reviewed versioned dataset; report each core field, not just one aggregate. Proposed ≥90% is a hypothesis to validate, not a launch promise.
- **Notification delivery:** distinguish provider acceptance from provider-confirmed delivery; set SLA after channel selection.
- **Reliability:** test recovery from AI/notification failures and duplicate-safe retries.
- **Accessibility:** target WCAG 2.2 AA where applicable, subject to testing.

Do not claim “99% reliable” without a time window, denominator, sample size, and explicit success condition.

## 11. Acceptance criteria

1. Valid enquiry is stored before relying on AI/notification work.
2. Retrying the same idempotent submission creates no duplicate lead/message.
3. Missing budget stays unknown/null and is never guessed.
4. “I need land around Ibadan below ₦20 million” yields `property_type=land`, location `Ibadan`, `budget_max_amount=20000000`, `budget_relation=maximum`, `budget_currency=NGN`, and `transaction_type=unknown` unless buying/renting/selling is explicit. “Around ₦80 million” yields `budget_amount=80000000`, `budget_relation=approximate`, and no hard min/max bounds.
5. Seller enquiry is captured and routed for human review; no valuation claim.
6. Stale AI result cannot overwrite a newer message/result.
7. Notification outage leaves the lead intact and records a recoverable attempt.
8. Unauthorized Sales user cannot read or mutate a lead outside their permission.
9. Invalid pipeline transition is rejected and valid changes are audited.
10. Sheets outage cannot affect canonical capture or sales status.

## 12. Open decisions

Approve PostgreSQL and hosting; choose durable event design; choose authentication provider/record access; choose AI provider/model; choose notification channel/SLA; approve or disable scoring; approve pipeline transition matrix; confirm seller enquiry is human-routed only in MVP; approve privacy notice/retention/deletion; confirm NGN-only normalized budget or multi-currency support.

## 13. Document authority

This PRD owns product intent and scope. API payload details are in `docs/05-api-contract-integration.md`; approved technical choices are in `docs/04-architecture-decision-records.md`. Cross-document conflicts involving safety, data integrity, or access must be raised rather than guessed.
