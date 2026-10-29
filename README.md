# PrimeHomes Realty — Real Estate Lead Bot

**Documentation baseline:** 1.0 (review-corrected draft)
**Status:** Requirements and architecture baseline for stakeholder approval; not proof of an implemented or tested application.

## Product summary

PrimeHomes Realty receives property enquiries through its website. The Real Estate Lead Bot captures each enquiry durably, extracts candidate requirements from natural language, asks useful clarification questions, prioritizes follow-up using transparent backend rules, and helps Sales manage the opportunity through a dashboard.

## Proposed technology baseline

- **Frontend:** React. TypeScript is recommended, pending approval before scaffolding.
- **Backend/API:** Python + FastAPI.
- **Workflow orchestration/integrations:** n8n.
- **Canonical database:** PostgreSQL is the recommended baseline and requires explicit owner approval before migrations are created.
- **Google Sheets:** Optional one-way reporting/export destination only in the MVP; not a second system of record.
- **AI:** Provider/model undecided. AI output is candidate data; FastAPI validates and persists accepted results.

## Canonical responsibility boundaries

1. React renders screens and collects user input. It does not enforce authoritative business rules.
2. FastAPI owns validation, authentication/authorization, lead and conversation state, scoring, status transitions, persistence, and API contracts.
3. PostgreSQL stores canonical business records once approved as the primary database.
4. n8n coordinates asynchronous AI/integration steps and notifications. It does not write directly to canonical database tables.
5. The AI model extracts or drafts; it does not authorize, assign, score by free-form judgment, mark leads won/lost, or claim unverified property availability.
6. A durable event mechanism connects committed records to asynchronous n8n work. The transactional-outbox/dispatcher design is proposed and must be approved before implementation.

## Documentation map

| # | Canonical file | Purpose |
|---|---|---|
| 1 | [`docs/01-product-requirements.md`](docs/01-product-requirements.md) | Product problem, scope, users, requirements, metrics, acceptance criteria |
| 2 | [`docs/02-system-architecture-data-design.md`](docs/02-system-architecture-data-design.md) | Components, data model, event flow, reliability architecture |
| 3 | [`docs/03-user-flows-design-specification.md`](docs/03-user-flows-design-specification.md) | Customer and sales journeys, UI states and behavior |
| 4 | [`docs/04-architecture-decision-records.md`](docs/04-architecture-decision-records.md) | Decisions, alternatives, trade-offs, approvals |
| 5 | [`docs/05-api-contract-integration.md`](docs/05-api-contract-integration.md) | API semantics, schemas, endpoints, idempotency, errors |
| 6 | [`docs/06-engineering-standards.md`](docs/06-engineering-standards.md) | Repository layout and engineering conventions |
| 7 | [`AGENTS.md`](AGENTS.md) | Instructions for AI coding agents |
| 8 | [`docs/08-testing-strategy.md`](docs/08-testing-strategy.md) | Test layers, fixtures, gates, failure-path verification |
| 9 | [`docs/09-security-privacy-reliability.md`](docs/09-security-privacy-reliability.md) | Threats, privacy controls, operational reliability |
| 10a | `README.md` | Developer entry point and setup summary |
| 10b | [`docs/operations/runbook.md`](docs/operations/runbook.md) | Deployment, incidents, backup, recovery, operations |
| 11 | [`docs/11-n8n-workflow-specification.md`](docs/11-n8n-workflow-specification.md) | Workflow inputs/outputs, retries, idempotency, failure paths |
| 12 | [`docs/12-ai-extraction-contract-evaluation.md`](docs/12-ai-extraction-contract-evaluation.md) | AI schema, field rules, prompt safety, evaluation dataset |
| — | [`docs/DECISION-REGISTER-AND-CHANGELOG.md`](docs/DECISION-REGISTER-AND-CHANGELOG.md) | Open decisions, cross-document consistency, revision log |
| — | [`docs/CRITICAL-REVIEW-RESOLUTION.md`](docs/CRITICAL-REVIEW-RESOLUTION.md) | Corrections applied and remaining approval gates |

## Task planning and implementation

- [`TASK.md`](TASK.md) defines Task 001: implement the first public lead-intake API endpoint.
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md) describes the technical sequence, approval gates, data/transaction behavior, and required tests for that task.

Read both before assigning an AI coding agent the first backend task. They do not override pending decisions in the ADR/decision register.

## Current development status

These documents describe the intended system. They do not imply that the codebase, migrations, workflow exports, API endpoints, or CI checks exist yet. Commands in the runbook must be verified after the repository toolchain is selected and scaffolded.

## Minimum decisions before implementation

1. Approve PostgreSQL as primary database and confirm hosting/backup arrangements.
2. Approve the asynchronous delivery design: transactional outbox + dispatcher, or a documented simpler alternative with acceptable durability.
3. Choose sales authentication/identity provider and define record-level access.
4. Select AI provider/model and review data-processing terms.
5. Choose notification channel(s) and business response SLA.
6. Approve scoring weights/thresholds or defer numeric scores for the first pilot.
7. Confirm privacy notice, retention, and customer-contact rules with the accountable business/privacy owner.

## Local setup

The repository is not yet guaranteed to contain the code or scripts described in the engineering documents. Once the scaffold and approved toolchain exist, follow [`docs/operations/runbook.md`](docs/operations/runbook.md) and replace provisional commands with verified commands.
