# Cross-cutting tests

- `fixtures/` — synthetic AI evaluation cases, contract examples, golden enums
- `e2e/` — critical-path end-to-end scenarios (see docs/08-testing-strategy.md)

Prefer synthetic data. Real customer data requires documented approval.
Backend unit/integration tests live under `backend/tests/`.
Frontend component tests live under `frontend/src/tests/`.
