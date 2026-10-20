# Frontend (React)

Customer chat/form and Sales dashboard for the PrimeHomes lead bot.

## Layout

```text
frontend/
├── package.json
└── src/
    ├── app/            # App shell, routing, providers
    ├── features/       # Feature modules (chat, lead-form, sales-dashboard)
    ├── components/     # Shared UI (ChatPanel, LeadQueueTable, ...)
    ├── lib/            # API client, types, utilities
    └── tests/          # Component / unit tests
```

## Principles

- Call **FastAPI only** — never internal n8n or provider endpoints with secrets.
- Prefer types generated or checked against OpenAPI (pending toolchain approval).
- Handle loading, success, empty, validation error, network error, stale version, and unknown outcome.
- Do not duplicate scoring, permission, qualification, or status-transition logic in the UI.
- Accessibility: semantic HTML, keyboard access, visible focus (see docs/03).

Suggested components (build when reuse exists): `ChatPanel`, `MessageList`, `MessageBubble`, `MessageComposer`, `ProcessingState`, `ClarificationPrompt`, `LeadForm`, `ContactDetailsForm`, `LeadQueueTable`, `LeadFilters`, `PriorityIndicator`, `PipelineStatusControl`, `ProcessingStatusNotice`, `LeadDetailsPanel`, `ActivityTimeline`, `FollowUpTaskForm`, `ErrorNotice`, `EmptyState`, `ConfirmDialog`.

TypeScript vs JavaScript and package manager remain pending (D-10).
