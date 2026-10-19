# Migration Map from Draft v0.1 Files to Corrected v1.0

This package replaces the prior draft files with canonical paths and aligned terminology. The original files remain separate in the conversation's working area; this bundle contains the corrected set.

| Previous draft file | Corrected canonical destination | Main corrections |
|---|---|---|
| `PRD-real-estate-lead-bot.md` | `docs/01-product-requirements.md` | Split status dimensions; correct intent taxonomy; clarify seller scope, lead/contact identity, scoring, metric definitions, and acceptance tests |
| `system-architecture-data-design.md` | `docs/02-system-architecture-data-design.md` | Align state model and domain entities; add data-integrity requirements, worker lifecycle, idempotency, stale-result handling, and approval gates |
| `user-flows-design-specification.md` | `docs/03-user-flows-design-specification.md` | Align UI statuses; remove implied live availability; clarify contact collection, seller handoff, persisted replies, and failure states |
| `architecture-decision-records.md` | `docs/04-architecture-decision-records.md` | Make approval status explicit and consistent; document the operational cost of outbox/worker choice |
| `api-contract-integration-specification.md` | `docs/05-api-contract-integration.md` | Separate transaction/property types; define idempotency roles, sequence-based pagination, protected session boundary, state enums, and stale callbacks |
| `engineering-standards-repository-guide.md` | `docs/06-engineering-standards.md` | Remove competing migration directories and duplicated agent instructions; clarify toolchain pending decisions |
| `AGENTS.md` | `AGENTS.md` | Fix all document paths; establish authority hierarchy and canonical enums; prevent silent implementation of proposed ADRs |
| `testing-strategy-quality-gates.md` | `docs/08-testing-strategy.md` | Add reviewed AI ground-truth data requirement, explicit failure-path assertions, boundary tests, and gates tied to approved thresholds |
| `security-privacy-reliability-requirements.md` | `docs/09-security-privacy-reliability.md` | Make privacy/owner decisions explicit; align access, vendor, retention, score-impact and recovery requirements |
| `README-setup-operations-runbook.md` | `README.md` plus `docs/operations/runbook.md` | Split onboarding from operations; label all unverified commands as provisional; add worker monitoring/replay expectations |
| Previously missing specification | `docs/11-n8n-workflow-specification.md` | Adds workflow ownership, event envelope, retry matrix, export controls, and release checklist |
| Previously missing specification | `docs/12-ai-extraction-contract-evaluation.md` | Adds schema, field normalization, response guardrails, dataset format, evaluation metrics, and versioning |
| `documentation-critical-review.md` | `docs/DECISION-REGISTER-AND-CHANGELOG.md` | Converts cross-document findings into a canonical contract, approval register, and update checklist |

## Important implementation caveat

These are documentation corrections and design contracts, not application code. Do not treat the API examples as a completed OpenAPI file, the logical data model as applied database migrations, the workflow specification as importable n8n exports, or the runbook as tested commands. Those artifacts must be generated, implemented, and verified in the actual repository.
