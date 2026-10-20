# Operations Runbook

**Status:** Placeholder. Procedures require deployment, monitoring, and recovery verification before use.

## Scope

Operational procedures for:

- Deployment and rollback
- Worker / outbox monitoring and dead-letter replay (if outbox approved)
- Credential rotation
- Backup restore evidence
- Incident response contacts

Do not treat commands here as tested until environments exist and exercises are recorded.

See also:

- `docs/09-security-privacy-reliability.md`
- `docs/DECISION-REGISTER-AND-CHANGELOG.md` (D-09 hosting/operations)
- Root `README.md` for developer onboarding (separate from this runbook)

## Incident owners (to be assigned)

| Role | Name | Contact |
|------|------|--------|
| Incident lead | TBD | |
| Database recovery | TBD | |
| n8n operations | TBD | |
| Privacy / data requests | TBD | |
| Credential rotation | TBD | |

## Provisional checklist (not yet verified)

- [ ] Health endpoints documented and monitored
- [ ] Outbox age / dead-letter alerts configured (if applicable)
- [ ] Backup schedule and last successful restore exercise recorded
- [ ] Replay procedure for dead-letter events documented and access-controlled
- [ ] Rollback steps for API, worker, and n8n workflow versions
