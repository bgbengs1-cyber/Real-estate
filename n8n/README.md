# n8n workflows and schemas

Orchestration only. n8n does **not** own scoring, permissions, pipeline transitions, or direct SQL writes.

## Layout

```text
n8n/
├── workflows/    # Sanitized workflow exports (no credentials, no execution data)
└── schemas/      # Versioned event / payload JSON Schemas
```

## Planned workflows (see docs/11-n8n-workflow-specification.md)

| Name | Role |
|------|------|
| `PH \| Lead Processing \| Extract and Qualify \| v1` | AI extraction (free text) or structured skip; callback to FastAPI |
| `PH \| Sales Notifications \| Dispatch Alert \| v1` | Minimal Sales alert; report outcome |
| `PH \| Reporting \| Export Lead \| v1` (optional) | One-way Sheets export after canonical commit |

Sanitize exports before commit. Never store credentials or PII in this directory.
