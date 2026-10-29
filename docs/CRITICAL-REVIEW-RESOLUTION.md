# Critical Review Resolution Report

**Documentation baseline:** 1.0 review-corrected draft  
**Purpose:** Record what the critical review changed and what must still be approved before implementation or production use.

## 1. Corrections applied

| Review finding | Correction in this bundle | Canonical location(s) |
|---|---|---|
| Sales lifecycle was mixed with technical workflow state | Split `pipeline_status`, `processing_status`, `qualification_status`, assignment, priority, outbox delivery, and notification outcome | PRD, architecture, API, UI spec, decision register, tests, `AGENTS.md` |
| `land_enquiry` mixed a property type with a transaction intent | Use `transaction_type` and `property_type` as separate enums; `land` is a property type | PRD, architecture, API, AI contract, tests, `AGENTS.md` |
| Lead/contact/opportunity identity was ambiguous | Define a lead as one distinct enquiry/opportunity; contacts can have multiple leads; do not fuzzy auto-merge | PRD, architecture, decision register |
| Idempotency mechanisms overlapped | Assign request-level `Idempotency-Key` and per-conversation `client_message_id` distinct responsibilities; use server-assigned message sequence numbers for ordering | API, architecture, tests, runbook |
| UUIDs were treated as chronological cursors | Use per-conversation `sequence_number` and sequence-based pagination | Architecture, API, tests |
| Scoring weights were not executable and could imply inventory fit | Document a deterministic provisional formula, reasons, null/unscored outcomes, and an explicit approval gate; do not imply property inventory fit | PRD, API, tests, decision register |
| General/seller enquiries conflicted with numeric score behavior | Seller/general/unsupported enquiries go to human review and remain unscored in the MVP | PRD, AI contract, tests, decision register |
| Budget points and maxima were conflated | Add `budget_amount`, explicit `budget_min_amount`/`budget_max_amount`, `budget_relation`, nullable currency, period, and original wording; “around ₦80m” is approximate, not a hard maximum | PRD, architecture, API, AI contract, tests |
| Ambiguous text could silently default to NGN | Keep currency null when unresolved; only use a visible, approved NGN form default or explicit/unambiguous currency evidence | API, architecture, AI contract, decision register |
| Structured-only forms had no coherent automation path | Add `lead.structured_submission_received`; validate customer-entered fields and skip AI extraction when there is no free text | API, architecture, n8n spec, AI contract, tests |
| Assistant drafts could be displayed before validation | AI drafts remain internal candidates; FastAPI validates and persists any customer-visible assistant message first | PRD, architecture, UI spec, API, AI contract, `AGENTS.md` |
| Stale AI results and retries could overwrite newer state | Use revision checks, idempotent callbacks, explicit stale-result handling, and bounded retries | Architecture, API, n8n spec, tests, runbook |
| Outbox was proposed without operational consequences | Document lease/worker duties, at-least-once semantics, backoff, dead-letter handling, monitoring, and approval status | Architecture, ADRs, n8n spec, runbook |
| ADR proposals were presented as though accepted | Marked proposed decisions clearly and defined an approval/supersession process | ADRs, decision register, `AGENTS.md` |
| Engineering guide had duplicate migration paths and agent instructions | One migration directory in the proposed repository; root `AGENTS.md` is authoritative and engineering standards link to it | Engineering standards, `AGENTS.md` |
| AI/automation contracts were missing | Added dedicated n8n workflow specification and AI extraction/evaluation contract | Documents 11 and 12 |
| README and operations procedures were mixed | Root README is the entry point; detailed incident/deployment/recovery procedures live in `docs/operations/runbook.md` | README, runbook, index |
| Testing relied on broad accuracy claims | Added reviewed ground-truth dataset requirements, field-level reporting, deterministic scoring tests, and specific failure-path cases | Testing strategy, AI contract |
| Security/privacy text could be mistaken for compliance proof | Clarified that production use requires privacy/legal review, assigned owners, retention/vendor decisions, and tested recovery | Security document, decision register, runbook |
| Setup commands were described before the codebase existed | Marked commands/tooling as provisional and requires clean-checkout verification against the actual scaffold | README, engineering standards, runbook |
| Documentation references were inconsistent | Added a single index, migration map, decision register, and path validation | `docs/INDEX.md`, `docs/MIGRATION-MAP.md`, `MANIFEST.json` |

## 2. Decisions intentionally not fabricated

The bundle does **not** pretend the following have been approved. They remain in the decision register with an owner/impact description:

1. PostgreSQL deployment/cost and approval as canonical database; Google Sheets export scope.
2. Transactional outbox plus dispatcher vs a simpler durable queue/approved alternative.
3. Authentication/session implementation and exact sales role/record-access policy.
4. AI provider/model and associated vendor/privacy review.
5. Sales notification channel and response SLA.
6. Whether to enable the proposed numeric lead score; score and pipeline-transition approval by Sales.
7. Seller-intake scope beyond capture-and-human-review.
8. Privacy notice, lawful-basis review, retention/deletion, vendor and cross-border data flow.
9. Hosting providers/regions, recovery targets, operational owners, and restore evidence.
10. Language/runtime/package manager, migration/test toolchain, and CI commands.
11. Currency behavior, including whether a visibly labeled NGN default is approved for structured form inputs.

## 3. What this review does not claim

- The application has not been implemented or executed as part of this documentation correction.
- OpenAPI schemas, database migrations, TypeScript types, tests, and n8n JSON exports must still be created/validated in the repository.
- Proposed score thresholds and quality/performance targets are not validated against production data.
- This bundle is not legal advice, a privacy compliance certification, or proof that a deployment is secure.
- README and runbook commands remain unverified until a real scaffold and target environment exist.

## 4. Minimum approval gate before feature implementation

- [ ] Product/Sales approve supported intents, lead qualification criteria, pipeline transitions, seller handling, and initial UI journey.
- [ ] Engineering owners approve canonical storage and asynchronous delivery design.
- [ ] API and AI schemas are translated into machine-validated OpenAPI/JSON Schema/Pydantic models and test fixtures.
- [ ] Authentication and authorization boundaries are agreed before building staff routes or accepting real customer data.
- [ ] Toolchain and setup commands are pinned and verified in a clean checkout.
- [ ] No proposed ADR is treated as approved without a recorded decision owner and review.

## 5. Recommended implementation order

1. Resolve approval-gated domain and architecture decisions.
2. Create canonical schemas/enums and migrations; add contract tests.
3. Build durable intake, idempotency, and processing-state persistence.
4. Implement n8n event processing and AI extraction with reviewed fixtures.
5. Build React customer flows and the Sales dashboard against the API contract.
6. Add notification/reporting integrations, retry/reconciliation and monitoring.
7. Complete security/privacy review, restore/recovery exercises, and a controlled pilot.
