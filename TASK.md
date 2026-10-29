# TASK 001 — Implement the First Public Lead-Intake API

- **Project:** PrimeHomes Realty — Real Estate Lead Bot
- **Task status:** Ready for engineering planning; database-backed completion is gated on the approvals listed below.
- **Priority:** P0
- **Owner:** Backend engineer / coding agent, with human engineering review
**Task type:** Backend foundation + API implementation
**Target endpoint:** `POST /api/v1/public/leads`

## 1. Objective

Implement the first FastAPI lead-intake endpoint so a prospective customer can submit a website enquiry and receive an acknowledgement only after the enquiry has been durably stored and its required downstream work has been recorded.

The endpoint must support two intake paths defined by the API contract:

1. **Message-based enquiry:** a non-empty free-text `message` is present. Persist the original customer text and create a linked conversation/message so asynchronous extraction can be performed later.
2. **Structured-only enquiry:** no free-text `message` is present, but the request contains at least one meaningful property-enquiry field. Persist the customer-entered values and provenance; do not call AI extraction for this path.

This task is about reliable intake, not building the entire Real Estate Lead Bot.

## 2. User story

As a prospective PrimeHomes Realty customer, I want to submit my property enquiry without needing to create an account or provide a phone number/email immediately, so that PrimeHomes can record my requirements and follow up when a suitable contact route exists.

As the business, we need each accepted enquiry to be persisted once, traceable, and recoverable if AI processing or a downstream integration fails.

## 3. Canonical references to read first

- [`README.md`](README.md)
- [`AGENTS.md`](AGENTS.md)
- [`docs/01-product-requirements.md`](docs/01-product-requirements.md)
- [`docs/02-system-architecture-data-design.md`](docs/02-system-architecture-data-design.md)
- [`docs/04-architecture-decision-records.md`](docs/04-architecture-decision-records.md)
- [`docs/05-api-contract-integration.md`](docs/05-api-contract-integration.md)
- [`docs/06-engineering-standards.md`](docs/06-engineering-standards.md)
- [`docs/08-testing-strategy.md`](docs/08-testing-strategy.md)
- [`docs/09-security-privacy-reliability.md`](docs/09-security-privacy-reliability.md)
- [`docs/11-n8n-workflow-specification.md`](docs/11-n8n-workflow-specification.md)
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
- [`docs/DECISION-REGISTER-AND-CHANGELOG.md`](docs/DECISION-REGISTER-AND-CHANGELOG.md)

The API contract is authoritative for endpoint payloads and response semantics. The decision register identifies decisions that remain pending. Do not infer that a recommendation has been approved simply because it appears in an architecture document.

## 4. Approval gates — do not guess these

The following decisions affect a correct implementation and must be recorded as approved in the ADR/decision register before database-backed completion:

- **D-01 — Canonical database:** approve PostgreSQL as the source of truth and confirm the development/CI database approach.
- **D-02 — Durable async delivery:** approve the transactional outbox + dispatcher or explicitly approve another durable mechanism with equivalent documented guarantees.
- **D-03 — Customer session/authentication:** approve how a message-based submission establishes a protected conversation session. Do not expose a conversation using its UUID alone.
- **D-10 — Toolchain:** confirm supported Python version, package/dependency manager, migration tool, and test commands sufficiently to lock the environment.

Also confirm the public submission's idempotency-key policy/retention and the structured-input validation rules during implementation review. If a required decision remains pending, the agent may scaffold non-committal code and write isolated validation tests, but must not silently implement a production persistence/dispatch/session choice. Record the blocker in the implementation report.

## 5. In scope

- Create or complete the FastAPI application scaffold according to the approved toolchain and repository layout.
- Implement `POST /api/v1/public/leads` using a typed request model and a stable response model.
- Validate the request at the API boundary using the API contract and canonical domain vocabulary.
- Accept optional customer contact fields; do not require name, email, or phone for initial capture.
- Accept free text and/or meaningful structured property-enquiry fields.
- Preserve original customer text exactly as submitted after defined transport normalization; never replace it with an AI summary.
- For customer-entered structured fields, record `customer_stated` provenance.
- Create a lead with the canonical initial states and independently represented status dimensions.
- If `message` is non-empty, create the lead, conversation, and initial customer message in the same transaction; return their IDs.
- If `message` is absent, require meaningful structured property-enquiry data, create no conversation/message, and use the structured-only workflow event.
- Persist request idempotency and downstream event intent in the same transaction as the lead and related records, if the approved architecture uses the documented database/outbox model.
- Return `202 Accepted` only after the database transaction commits and required downstream work is durably recorded.
- Implement the standard error envelope, correlation ID, safe structured logging, and public-route abuse/rate-limit controls according to the approved security design.
- Add unit, API, database integration, and failure-path tests appropriate to the approved stack.
- Update API examples or related documentation if implementation reveals an inconsistency; request review before changing the contract.

## 6. Out of scope

- Calling an AI provider synchronously from the request handler.
- Building the AI extraction prompt/model or the complete n8n workflow.
- Sending sales notifications or exporting to Google Sheets from inside this endpoint.
- Implementing lead scoring/priority thresholds before the business has approved the scoring rule. Initial `priority_band` must remain `unscored` and `priority_score` null.
- Implementing the Sales dashboard, sales-user CRUD, assignments, notes, or follow-up-task endpoints.
- Automatically merging contacts/leads based on fuzzy matches, similar text, or location.
- Claiming property availability, listing prices, valuations, or viewing confirmations.
- Adding channels other than the approved website form/chat intake.
- Implementing a production authentication provider not yet selected.

## 7. Request behavior and validation

Use the request/response schema in [`docs/05-api-contract-integration.md`](docs/05-api-contract-integration.md) as the contract source. At minimum:

- `source_channel` must be a supported value; this task's form path uses `website_form`.
- `message` may be omitted or null. If supplied, it must be a non-blank string within an approved maximum length.
- A structured-only request must include at least one meaningful enquiry field, such as an explicit non-unknown transaction type, explicit non-unknown property type, location, a valid budget statement, a timeline other than `unknown`, bedroom count, or property-detail text. Contact details alone do not constitute a property enquiry.
- `transaction_type` and `property_type` are different fields. `land` is valid as `property_type`; it is not a `transaction_type`.
- Missing/unclear values remain null or `unknown` according to the contract; do not infer missing data.
- Do not require phone/email at initial capture.
- Validate email/phone syntax without claiming that an unverified contact method has been verified.
- Validate non-negative/positive budget values according to the agreed money policy; when both range bounds are present, ensure the minimum does not exceed the maximum.
- Keep `budget_amount` (single stated point/approximate amount) separate from `budget_min_amount` and `budget_max_amount` (explicit bounds). Preserve `budget_text_original`. Do not convert an approximate budget into a hard maximum. Do not infer `NGN` from ambiguous text.
- Reject unknown enum values and unexpected writable/system-owned fields; never mass-assign request JSON to a database model.

If a validation rule is not explicit in the canonical documents, propose the rule and update the contract with reviewer approval rather than silently inventing a permanent rule.

## 8. Initial state and event behavior

- New lead: `pipeline_status=new`.
- Before asynchronous work has completed: `processing_status=queued`.
- Initial qualification: `qualification_status=incomplete`, except an explicitly approved policy may route a seller/unsupported enquiry to `needs_review`.
- Initial priority: `priority_band=unscored`, `priority_score=null`.
- `review_required` must follow the approved explicit rule; it must not be inferred from an LLM-generated score.
- Message path event: `conversation.message_received`, with stable event ID, conversation revision, and original message ID.
- Structured-only event: `lead.structured_submission_received`, with `conversation_id=null`, a lead/input revision, and `data.input_kind="structured_submission"`; no AI extraction is run for this path.
- An outbox event is not proof that n8n has completed processing. Keep outbox delivery state separate from `processing_status`.
- A failed AI, notification, or Sheets integration must not roll back an already committed lead.

## 9. Idempotency and persistence requirements

- Require the documented `Idempotency-Key` for mutation requests where specified by the contract; do not rely on a client button being disabled.
- Scope the key appropriately to the public operation/session and persist a request hash and original result.
- Same key + same request hash returns the same logical result without creating another lead, conversation, message, or event.
- Same key + different request hash returns `409` with `idempotency_conflict`.
- Keep `Idempotency-Key` separate from `client_message_id`, which is a per-message identity for the conversation-message endpoint.
- Use database uniqueness constraints as a final guard against concurrent duplicate requests.
- If persistence or durable event insertion fails, do not return a successful `202` acknowledgement.

## 10. Acceptance criteria

- [ ] A valid message-based submission returns `202` only after commit and returns `lead_id`, `conversation_id`, `initial_message_id`, canonical initial states, and `correlation_id`.
- [ ] A valid structured-only submission returns `202`, has `conversation_id=null` and `initial_message_id=null`, persists submitted facts/provenance, and does not invoke AI extraction.
- [ ] An empty submission (no message and no meaningful enquiry field) is rejected with the standard validation error.
- [ ] A blank/oversized message, invalid enum, malformed contact value, invalid budget range, and invalid budget relation are handled consistently with the API contract.
- [ ] Missing currency remains null/unknown when not explicit; original budget wording is retained.
- [ ] Missing name, email, and phone do not block initial capture.
- [ ] `land` is stored only as `property_type=land`; transaction intent remains `unknown` unless explicit.
- [ ] Repeating the same idempotent request creates no duplicate logical resources or event.
- [ ] Reusing an idempotency key with a different request body returns `409 idempotency_conflict`.
- [ ] A failure inside the persistence transaction leaves no partial lead/conversation/message/outbox write.
- [ ] A downstream n8n timeout/failure after commit cannot delete or invalidate the lead.
- [ ] The public endpoint does not expose internal prompts, stack traces, database details, service credentials, internal failure data, or Sales-only fields.
- [ ] No score is calculated by the LLM; the endpoint's initial priority is unscored until the approved backend scoring policy exists.
- [ ] Tests cover concurrent duplicate submission and validate database uniqueness/idempotency behavior.
- [ ] The documented tests/commands have actually been run; the PR reports the exact commands and results.

## 11. Deliverables

- FastAPI route and typed request/response schemas.
- Intake service/use case and persistence implementation in the approved architecture layer.
- Database migration(s) and constraints, only after D-01 and the migration toolchain are approved.
- Durable event/outbox integration, only after D-02 is approved.
- Unit and integration tests plus reusable synthetic request fixtures.
- API/README updates if the verified implementation commands or actual schema differ from the current draft.
- Pull request summary with files changed, tests actually run, decisions consumed, assumptions, risks, and anything not tested.

## 12. Definition of done

All applicable acceptance criteria pass; data writes and event intent are atomic under the approved architecture; retry and duplicate behavior is tested; security review is complete for the public endpoint; no unapproved architectural decision has been silently locked in; and API/docs/fixtures remain consistent.
