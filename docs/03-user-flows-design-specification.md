# 3. User Flows & Design Specification

**Version:** 1.0 review-corrected draft  
**Status:** Behavioral specification; final visual design still requires approval.

## 1. Design goals

- Make submitting an enquiry easy without forcing unnecessary personal data collection.
- Set truthful expectations: stored, processing, responded, and failed are different states.
- Ask one concise clarification at a time.
- Keep Sales focused on actionable leads and clear next actions.
- Treat loading, empty, error, stale, success, and permission-denied states as first-class design states.
- Ensure priority never replaces human judgment or hides leads from the queue.

## 2. Information architecture

### Customer-facing area

- Website entry point/help text (if placed within the existing website).
- Chat start and active conversation.
- Optional structured lead form.
- Optional contact details capture for follow-up outside the current browser session.
- Confirmation and safe fallback states.

### Sales area

- Sign-in (identity provider undecided).
- Lead queue with search/filter/sort.
- Lead details and conversation history.
- Assignment and pipeline status controls.
- Notes and follow-up task management.
- Processing/notification warnings, displayed separately from pipeline state.

## 3. Canonical UI state model

Do not represent every state with one badge. Show independent dimensions:

- **Pipeline:** `new`, `contacted`, `viewing_scheduled`, `negotiation`, `nurturing`, `won`, `lost`.
- **Processing:** `queued`, `processing`, `completed`, `needs_review`, `failed`.
- **Qualification:** `incomplete`, `qualified`, `needs_review`, `disqualified`.
- **Assignment:** assigned person or unassigned.
- **Priority:** `hot`, `warm`, `standard`, `unscored`, plus reasons and calculation time when scoring is approved.
- **Follow-up:** next due task or none.

“Processing failed” must never look like “Sales lost the deal.”

## 4. Customer flow A — clear enquiry

1. Customer opens chat and sees concise welcome copy with examples of useful details.
2. Customer writes: “I’m looking for a 3-bedroom apartment around Lekki. Budget is about ₦80 million; I want to move in within two months.”
3. Frontend shows “Sending…” and does not claim the message is safely sent until FastAPI confirms durable persistence.
4. API returns `202 Accepted`, message ID, sequence number, and `processing_status=queued`.
5. UI renders the persisted customer message and “Checking your requirements…” state.
6. After backend-validated processing, UI displays the persisted assistant message returned by FastAPI.
7. Bot summarizes known details and asks at most one useful remaining clarification.
8. Customer may optionally provide validated contact details for follow-up outside the current session.

## 5. Customer flow B — incomplete enquiry

Example: “Hi, I want to buy a house.”

1. Persist message and create lead immediately.
2. Extraction may return `transaction_type=buy`, `property_type=house`; location, budget, and timeline remain unknown.
3. If processing succeeds, ask one useful question (usually location or budget according to approved policy).
4. If the customer declines, do not loop. Keep the lead and route to Sales where appropriate.
5. The UI must not imply that an incomplete enquiry is invalid.

## 6. Customer flow C — ambiguous or conflicting input

Example: “I want something around 80m,” without currency or transaction context.

- Preserve raw text.
- Do not infer precise transaction type/currency without sufficient context.
- Use `unknown`/`null`, flag material ambiguity, and ask one clear question.
- For a correction, the newest explicit customer statement supersedes earlier customer-stated data unless Sales has made an explicit correction; retain provenance/history.

## 7. Customer flow D — seller enquiry or unsupported request

Example: “I want to sell my house in Yaba.”

- Capture the enquiry and set `transaction_type=sell` where clear.
- Set qualification to `needs_review` and route to Sales in the MVP.
- Do not estimate value, promise a marketing timeline, or claim the company accepts the listing unless supported by approved policy/data.
- Say a team member can review the enquiry; do not promise a response SLA until one is approved and the follow-up is actually queued.

## 8. Customer flow E — availability question

Example: “Is that 3-bedroom apartment available today?”

No verified property inventory is included in the MVP. The bot must state it cannot verify current availability and offer Sales follow-up. It must not invent listings/prices or claim an appointment is booked.

## 9. Customer-visible processing states

| State | Behavior/copy guidance |
|---|---|
| Sending | “Sending your message…”; retry must reuse the same logical message identity |
| Stored/queued | “Your message has been received. I’m checking the details now.” |
| Processing | Show discreet progress; avoid an indefinite spinner |
| Needs clarification | Ask one question tied to a missing/uncertain field |
| Delayed | “Your enquiry is saved, but processing is taking longer than expected.” |
| Failed | “Your enquiry is saved. Our team may need to review it before we can answer.” Only promise handoff if a real handoff event/task is recorded |
| Outcome unknown/offline | Explain delivery is unconfirmed; retry/read using the same idempotency identity |
| Reply available | Show only the validated, persisted assistant message |

Never manufacture a frontend-only assistant reply or claim notification delivery succeeded without evidence.

## 10. Contact details and privacy UX

- Do not require phone/email for initial capture unless an approved product decision changes this.
- Explain why contact details are requested and link to the approved privacy notice.
- Valid format does not mean a contact method has been verified.
- Do not show full contact details to unauthorized users.
- Explain conversation/session limitations before the customer closes the page if the session cannot be restored.

## 11. Sales dashboard

### Lead queue

Show lead reference, received time, source, transaction/property type, location, budget when provided, timeline, priority/reasons if enabled, qualification state, processing warning, assignment, pipeline status, and next follow-up. Show missing values as “Not provided” or “Unknown,” never guessed.

Filters should cover pipeline state, processing/qualification state, assignment, date, source, transaction/property type, priority, review required, processing failure, and overdue follow-up. Unassigned and failed-processing leads must remain discoverable.

### Lead details

- Contact details and verification state when available.
- Original messages and chronological conversation history.
- Extracted facts with provenance and authorized correction controls.
- Separate pipeline, qualification, processing, priority, and assignment sections.
- Activity timeline, follow-up tasks, notification outcome, and safe error summary.

### Pipeline/assignment actions

- Render permitted transitions according to API contract; FastAPI is authoritative.
- Handle `409 conflict`, `403 forbidden`, validation errors, and stale versions.
- `won`/`lost` requires authorized human action; request reason where policy requires it.
- Reopening a closed lead is manager-only and reasoned/audited.
- An assigned lead can still be incomplete/processing; assignment is not status.

### Follow-up tasks

A task needs action type, due time/timezone, owner if assigned, and status. Overdue means incomplete after due time; a completed task is not overdue. Reminders use the approved provider and duplicate-safe behavior.

## 12. Visual system and accessibility

Final design file/tokens require approval. Do not call invented brand styling approved. Requirements:

- Responsive chat and dashboard, usable on mobile and desktop.
- Semantic markup, keyboard navigation, visible focus, labeled fields, accessible errors/status announcements.
- Do not use color alone to represent priority/status.
- Target WCAG 2.2 AA where applicable, subject to testing.
- Respect reduced-motion settings; provide useful loading states.
- Store timestamps in UTC and display in an agreed timezone; use consistent NGN formatting unless multi-currency is approved.

## 13. Suggested reusable React components

`ChatPanel`, `MessageList`, `MessageBubble`, `MessageComposer`, `ProcessingState`, `ClarificationPrompt`, `LeadForm`, `ContactDetailsForm`, `LeadQueueTable`, `LeadFilters`, `PriorityIndicator`, `PipelineStatusControl`, `ProcessingStatusNotice`, `LeadDetailsPanel`, `ActivityTimeline`, `FollowUpTaskForm`, `ErrorNotice`, `EmptyState`, `ConfirmDialog`.

Keep component abstraction proportional to actual reuse.

## 14. Frontend/API interaction

- React calls documented FastAPI endpoints only.
- Generate one stable `client_message_id` for each logical chat message and reuse it on retry.
- Separate optimistic/pending messages from confirmed persisted messages.
- Poll/refresh according to API contract with backoff, not tight loops.
- Discard stale client results when conversation revision advances.
- On timeout, treat outcome as unknown until idempotent retry/read resolves it; do not blindly create a second message.

## 15. UX acceptance criteria

- A customer can start a general enquiry without mandatory contact details.
- Customer can distinguish queued from answered.
- Missing budget remains missing; no default is fabricated.
- Seller/live-availability questions get safe human-review wording.
- Sales can distinguish pipeline stage from processing state.
- Processing failure does not hide a lead.
- Concurrent status updates refresh/reconcile rather than silently overwrite.
- Essential chat/dashboard actions work with keyboard and screen readers.

## 16. Decisions still needed

Brand/tokens and screen mocks, authentication, session persistence, privacy copy, Sales role permissions, notification channel, and final transition approval. See `docs/DECISION-REGISTER-AND-CHANGELOG.md`.
