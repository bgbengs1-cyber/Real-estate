# Outbox dispatcher / worker

**Status:** Optional directory. Only required if a transactional outbox + separate dispatcher process is **approved** (ADR-0004 / D-02).

## Responsibility (when approved)

- Claim due `outbox_events` rows safely (e.g. `FOR UPDATE SKIP LOCKED` + lease)
- Deliver authenticated event envelopes to n8n (at-least-once)
- Record attempts, errors, next-attempt time, and dead-letter state
- Bounded exponential backoff with jitter for transient failures
- Graceful shutdown and health checks

If the team chooses a managed queue or folds the worker into the backend process, remove or collapse this directory and update architecture docs and the decision register.

Do not implement production dispatcher behaviour until D-02 is accepted.
