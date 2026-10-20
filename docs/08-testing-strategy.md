# 8. Testing Strategy & Quality Gates

**Version:** 1.0 review-corrected draft  
**Status:** Test plan; exact thresholds and tools require owner approval.

## 1. Testing principles

- Test business outcomes and failure behavior, not only happy paths.
- Deterministic rules (authorization, state transitions, idempotency, and score formula if enabled) must be deterministic and unit-tested.
- Evaluate AI against reviewed expected outputs and report per-field quality; one aggregate score can hide dangerous weak fields.
- Use synthetic data by default. Real customer data requires documented approval and controls.
- Run deterministic checks on each relevant PR; test live integrations in a controlled environment.
- Each failure-path test specifies both what must happen and what must not happen.

## 2. Test layers and candidate tooling

Tool suggestions are pending toolchain approval: pytest for Python; a React component/E2E framework selected by the frontend team; PostgreSQL integration tests; OpenAPI schema checks; controlled n8n tests; fixed AI evaluation fixtures; CI for required gates.

| Layer | What it proves | Examples |
|---|---|---|
| Unit | One rule/function behaves correctly | priority boundaries, transition matrix, field precedence |
| API/schema | Request/response conforms to contract | enums, nullability, error envelope, OpenAPI examples |
| Database integration | Constraints and transactions work | lead+message+outbox atomic commit; uniqueness |
| Component/UI | User-visible states/actions work | queued vs replied, validation, keyboard accessibility |
| n8n workflow | Routes/handles outcomes as specified | valid event, malformed event, provider timeout |
| AI evaluation | Extraction is grounded and adequate | budget, location, intent, ambiguity, correction |
| End-to-end | Full critical path works | submit → persist → extract → respond → notify → Sales |
| Security | Access/data boundaries hold | guessed conversation ID, cross-lead access, prompt injection |
| Operational recovery | Failure can be detected/recovered | worker crash, dead letter, restore, safe replay |

## 3. Canonical test fixture format

Each evaluation case includes `case_id`, dataset version, original messages in order, expected canonical fields, expected unknown/null values and ambiguities, expected qualification/review outcome, expected safe reply intent, reviewer/adjudication status, and rationale.

Include synthetic examples for: buyer/renter, sparse general enquiry, land without transaction intent, seller/human handoff, missing budget, ambiguous “80m”, conflicting corrections, no contact details, explicit urgency, unsupported availability request, malformed AI JSON, prompt injection, and duplicate/stale events. Do not count a plausible guess as correct unless it matches reviewed ground truth.

## 4. Functional tests

### Intake and messages

- Valid chat/free-text form request is stored with original text before a success response; structured-only form fields are stored with customer-stated provenance and do not fabricate a message or call AI extraction.
- DB transaction failure does not produce a successful capture acknowledgement or orphan outbox event.
- Repeating an idempotent request returns the same logical result.
- Reusing an idempotency key with a changed request hash returns conflict.
- Same `client_message_id` in a conversation does not duplicate the logical message.
- Customer cannot access a conversation by guessing its UUID.
- Anonymous enquiry is accepted without mandatory contact details under the approved UX policy.

### Extraction and data integrity

- “I need land around Ibadan below ₦20 million” → `property_type=land`, location `Ibadan`, `budget_max_amount=20000000`, `budget_relation=maximum`, currency NGN; `transaction_type=unknown` unless buy/rent/sell is explicit. “Around ₦80 million” → `budget_amount=80000000`, `budget_relation=approximate`, no hard max bound.
- “I want to buy a house” → `transaction_type=buy`, `property_type=house`; location/budget/timeline remain unknown.
- “about 80m” without context does not silently imply currency, transaction, or location; unresolved currency remains null and the original wording is preserved.
- Seller and general/unsupported enquiries are saved and routed to human review, remain unscored in the MVP, and do not produce valuation claims.
- Customer correction updates the current normalized value with provenance history.
- Sales correction is not overwritten by stale or lower-authority AI extraction.
- Invalid enum, impossible amount, unknown source message ID, invalid confidence, or stale revision is rejected safely.

### State and priority

- Pipeline, processing, qualification, assignment, priority, outbox, message, and notification state are stored/displayed separately.
- Every allowed pipeline transition succeeds; invalid transition returns conflict and makes no partial state change.
- `won`/`lost` require authorized action and an audit record.
- If score is approved, test every dimension, band boundary, rule version, reason code, null/unscored behavior, and repeatability. If scoring is deferred, verify no fake score is shown.
- Missing contact data alone does not discard a lead.

### Notifications and Sheets

- Notification outcome is recorded separately from lead status.
- Timeout after provider submission may produce `unknown`; apply reconciliation policy.
- Retry does not duplicate a notification where provider idempotency is available; limitations are documented where it is not.
- Sheets outage leaves the canonical lead and Sales status unchanged.
- Export uses allowlisted columns and safely handles formula-like user text.

## 5. AI quality and safety evaluation

Track per-field precision/acceptable-match rate and recall where applicable, unsupported non-null guesses, ambiguity detection, clarification behavior, schema validity, stale-result rejection, unsafe availability/price claims, and response-policy violations. Product/Sales must set thresholds after reviewing baseline data and error costs.

Use deterministic mocks for routine PR tests. Record model/provider, prompt/schema version, evaluation dataset version, and run date for controlled AI runs. Do not include hidden model reasoning or secrets in logs/evidence.

Mandatory adversarial cases: instruction override attempts in customer text; requests for internal prompts/other customer data; fake availability requests; malformed provider output; conflicting facts; oversized/malformed messages; HTML/script-like input; malicious retrieved content if retrieval is added later.

## 6. n8n and asynchronous reliability tests

- Duplicate event ID is recognized; processing/side effects do not repeat beyond the idempotent contract.
- 429/5xx/timeout follows bounded backoff and attempt limit.
- 400/401/403/schema errors go to repair/alert path; no infinite retry.
- Dispatcher lease expires after worker crash; event is safely reclaimed, if outbox worker is approved.
- Exhausted event becomes inspectable dead-letter work with a safe error code.
- n8n failure before AI callback is recoverable.
- Duplicate callback persists no duplicate result or assistant message.
- New customer message before older AI callback causes old result to be rejected as stale.
- Unknown notification outcome does not cause blind resends.
- Export replay does not create a new lead or change pipeline status.

## 7. Critical end-to-end cases

1. Buyer enquiry → durable capture → validated extraction → persisted assistant response → notification outcome recorded.
2. Missing location/budget → lead persisted → one clarification question → follow-up message merges correctly.
3. AI outage after capture → lead remains visible, processing failure/review is visible, recovery works.
4. Duplicate customer send → one logical message and one logical processing event.
5. Notification failure → lead retained, failed/unknown attempt visible, controlled retry.
6. Unauthorized staff attempts to read/update lead → denied and audited where appropriate.
7. Sheets outage → core workflow succeeds; export remains retryable separately.
8. Stale AI callback after newer customer/Sales update → rejected; no overwrite or duplicate reply.
9. Dispatcher crash during lease → lease expiry/reclaim works, if applicable.
10. Backup restored into isolated environment → application can read a consistent dataset.

## 8. Provisional quality gates

### Pull request

- Configured format/lint/type checks pass for touched code.
- Unit tests for changed deterministic rules pass.
- API schema/shared types remain aligned.
- No critical/high security finding or secret is introduced.
- Relevant migration tests pass; no unreviewed destructive migration.
- Workflow export is sanitized and its contract matches the schema.

### Main branch

- Required CI checks pass.
- Contract and integration tests for changed boundaries pass.
- State/idempotency/score tests pass where relevant.
- Documentation and fixtures are updated.

### Production release

- Controlled staging E2E passes.
- Authentication/authorization and privacy controls are verified.
- Backup restore and failed-event recovery have current evidence.
- AI evaluation meets owner-approved per-field thresholds or uncertain results remain human-reviewed.
- Notification unknown/failure behavior and contact policy are approved.
- Rollback procedure and incident owners are known.

Numeric thresholds for coverage, performance, extraction accuracy, retries, and availability remain provisional until tools, dataset, traffic assumptions, and risk appetite are approved. Coverage percentage alone is not a release criterion.

## 9. Test evidence

Record commit/build ID, commands run, pass/fail counts, environment, relevant AI model/schema/dataset versions, known failures, and approver. Separate checks actually run from checks planned but not run.

## 10. Exit criteria

Testing is not ready for production until a reviewed ground-truth dataset exists, score is approved or disabled, state transitions are canonical, quality gates are executable in CI, and critical failure tests assert both required and forbidden side effects.
