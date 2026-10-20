# AGENTS.md — Instructions for AI coding agents

**Authority hierarchy (highest first):**

1. This file (`AGENTS.md`)
2. `docs/DECISION-REGISTER-AND-CHANGELOG.md` (canonical enums and open decisions)
3. `docs/01-product-requirements.md` (product intent)
4. `docs/04-architecture-decision-records.md` (Accepted vs Proposed)
5. Other `docs/*` specifications
6. Code and tests (must align with the above)

If documents conflict on safety, data integrity, or access control, **stop and raise** rather than guess.

## Project identity

PrimeHomes Realty lead bot: durable web enquiry capture, AI-assisted extraction (candidates only), Sales dashboard, n8n orchestration. Stack direction: React + FastAPI + n8n.

## Non-negotiable rules

### Architecture

- FastAPI owns all canonical writes, scoring (if approved), qualification, pipeline transitions, authorization, and audit.
- n8n must **not** write to PostgreSQL tables directly.
- React must **never** call internal n8n webhooks or provider APIs that require secrets.
- AI outputs are **candidates** until FastAPI validates schema, `input_revision`, enums, and policy.
- Persist enquiry + outbox intent **before** acknowledging success (`202` means stored and queued, not AI-complete).

### Canonical enums (do not invent alternatives)

```text
transaction_type: buy | rent | sell | general_enquiry | unknown
property_type: apartment | house | duplex | office | shop | land | other | unknown
timeline: immediate | within_1_month | within_3_months | researching | unknown
pipeline_status: new | contacted | viewing_scheduled | negotiation | nurturing | won | lost
processing_status: queued | processing | completed | needs_review | failed
qualification_status: incomplete | qualified | needs_review | disqualified
priority_band: hot | warm | standard | unscored
sender_type: customer | assistant | sales_agent | system
outbox_status: pending | leased | delivered_to_n8n | retry_wait | dead_letter
notification_status: queued | provider_accepted | delivered | failed | unknown
```

- `land` is a **property_type**, never a transaction intent.
- Pipeline, processing, qualification, assignment, priority, outbox, and notification states are **independent**.
- Seller / general_enquiry → human review and **unscored** in MVP.

### Data integrity

- Original customer messages are immutable; corrections add history/provenance.
- Provenance precedence: Sales correction > latest customer statement > validated AI > unknown/null.
- Stale AI callbacks must not overwrite newer messages or Sales edits (`input_revision` check).
- Use per-conversation `sequence_number` for ordering; UUID is not a chronological cursor.
- `Idempotency-Key` (request) and `client_message_id` (message) have distinct roles.
- Budget: distinguish `budget_amount` (point) vs min/max bounds and `budget_relation`; keep currency null when unresolved.

### Proposed decisions

Do **not** implement Proposed ADRs as if Accepted. Pending items (D-01 … D-12) are listed in the decision register. Scaffolding is allowed; locking production behaviour to an unapproved choice is not.

### Repository layout

Follow `docs/06-engineering-standards.md`. One migration directory only: `backend/migrations/`. Do not create `database/migrations/`.

### Secrets and safety

- Never commit secrets, real customer data, or credential-bearing n8n exports.
- Do not invent live availability, prices, valuations, or won/lost without authorized action.
- Prefer synthetic fixtures; real data requires explicit approval.

### Definition of Done (agent)

- Code lives in the correct layer (api / domain / services / repositories / integrations).
- Success and failure paths tested where applicable.
- Enums and field names match the decision register and API contract.
- No silent assumption of Proposed ADRs.
- Docs paths and contracts remain consistent.

## Where to look

| Need | Document |
|------|----------|
| Product scope & acceptance | `docs/01-product-requirements.md` |
| Architecture & data model | `docs/02-system-architecture-data-design.md` |
| UI flows & states | `docs/03-user-flows-design-specification.md` |
| ADR status | `docs/04-architecture-decision-records.md` |
| HTTP & event contracts | `docs/05-api-contract-integration.md` |
| Coding standards & layout | `docs/06-engineering-standards.md` |
| Tests & quality gates | `docs/08-testing-strategy.md` |
| Security & privacy | `docs/09-security-privacy-reliability.md` |
| n8n workflows | `docs/11-n8n-workflow-specification.md` |
| AI schema & evaluation | `docs/12-ai-extraction-contract-evaluation.md` |
| Open decisions | `docs/DECISION-REGISTER-AND-CHANGELOG.md` |
| Ops procedures | `docs/operations/runbook.md` |
