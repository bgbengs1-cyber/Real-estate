# 12. AI Extraction Contract & Evaluation

**Version:** 1.0  
**Status:** Provider-neutral contract. The prompt/model and numerical thresholds require approval after a baseline dataset is reviewed.

## 1. AI's permitted role

The AI may extract candidate fields supported by the conversation, identify ambiguity/conflict/missing data, propose one concise clarification question, draft a polite response grounded in known facts, and summarize requirements for Sales.

The AI may not invent unknown values, contact details, budgets, locations, property features/inventory, market prices, availability, bookings, or consent. It may not authorize access, assign leads, set authoritative pipeline status, determine final numeric score by free-form judgment, mark leads won/lost, execute unrestricted tools, query arbitrary customer records, or treat customer-injected instructions as higher priority than product policy.

## 2. Canonical extraction schema

The AI extraction contract applies only when free-text content needs interpretation. The callback must carry candidate facts with evidence/provenance. Structured-only form submissions bypass AI extraction and preserve their fields as customer-stated values. This is a conceptual example; the actual JSON Schema/Pydantic schema must be committed and validated in CI.

```json
{
  "schema_version": 1,
  "transaction_type": {
    "value": "buy",
    "source_message_id": "uuid",
    "evidence_text": "I want to buy",
    "confidence": 0.98
  },
  "property_type": {
    "value": "apartment",
    "source_message_id": "uuid",
    "evidence_text": "3-bedroom apartment",
    "confidence": 0.97
  },
  "location_text": {
    "value": "Lekki",
    "source_message_id": "uuid",
    "evidence_text": "around Lekki",
    "confidence": 0.96
  },
  "budget": {
    "amount": 80000000,
    "min_amount": null,
    "max_amount": null,
    "relation": "approximate",
    "currency": "NGN",
    "period": "one_time",
    "original_text": "around ₦80 million",
    "source_message_id": "uuid",
    "confidence": 0.95
  },
  "bedroom_count": {
    "value": 3,
    "source_message_id": "uuid",
    "evidence_text": "3-bedroom",
    "confidence": 0.99
  },
  "timeline": {
    "value": "within_3_months",
    "source_message_id": "uuid",
    "evidence_text": "within the next two months",
    "confidence": 0.84
  },
  "name": null,
  "email": null,
  "phone": null,
  "missing_fields": ["contact_method"],
  "ambiguities": [],
  "clarification_question": null,
  "assistant_reply_draft": "Thanks. I have noted your interest in a 3-bedroom apartment around Lekki with a budget of about ₦80 million. Is there a particular area or move-in date you prefer?",
  "prompt_version": "1.0",
  "model_metadata": {"provider":"configured-provider","model":"configured-model"}
}
```

`evidence_text` must be a short span grounded in a source message, not hidden reasoning. AI-derived facts require a valid `source_message_id`; structured form fields are handled without AI and are not assigned synthetic message IDs. Unknown fields use `null` or the canonical `unknown` enum. If a field is unknown, do not invent a source message ID. The example is illustrative, not a real extracted record.

## 3. Enum and normalization rules

- `transaction_type`: `buy`, `rent`, `sell`, `general_enquiry`, `unknown`.
- `property_type`: `apartment`, `house`, `duplex`, `office`, `shop`, `land`, `other`, `unknown`.
- `timeline`: `immediate` (intends to act within 7 days), `within_1_month` (8–30 days), `within_3_months` (31–90 days), `researching` (no committed timeframe), `unknown`.
- Budget uses `amount` for one stated point estimate, `min_amount`/`max_amount` only for explicit range bounds, and `relation`: `exact`, `approximate`, `minimum`, `maximum`, `range`, or `unknown`. For “around ₦80 million”, use `amount=80000000`, `relation=approximate`, and leave bounds null; for “below ₦20 million”, use `max_amount=20000000`, `relation=maximum`, and leave point amount/minimum null.
- `currency` is nullable. Use `NGN` when the customer explicitly states naira/₦ or when the UI/business context has an approved visible NGN default. Ambiguous “m”/“80m” without sufficient context remains unresolved; do not silently assume currency.
- `period`: `one_time`, `monthly`, `yearly`, `unknown`. Amounts must be non-negative and within configured safe bounds. If both range bounds are present, require `min_amount <= max_amount`; do not invent endpoints.
- Bedroom count is a positive integer within a configured bound and applies only where semantically relevant.
- Location remains customer-stated text in the MVP. Do not claim it is geocoded/verified unless an approved service performs that operation.
- Name/contact fields are extracted only when explicitly stated in source/context. Never synthesize phone/email from a name.
- Mentioning land alone does not imply buying; `property_type=land`, `transaction_type=unknown` unless the customer states an intent.
- Seller intent is captured and routed to `qualification_status=needs_review` in the MVP; no valuation or automated seller workflow.

## 4. Confidence and ambiguity

Model confidence is not a calibrated probability unless it has been evaluated as such. It may inform review but cannot override schema, evidence, source revision, deterministic rules, or human corrections. Field-specific thresholds are set only after evaluating the selected model on reviewed data.

For conflicting messages (e.g. “budget is 80m” then “I meant 60m”), retain both messages and treat the latest explicit customer statement as the current customer-stated value unless an authorized Sales correction has higher authority. For approximate single amounts, preserve `relation=approximate`; never reinterpret a point estimate as an upper bound. Preserve provenance/history. If the context is insufficient, keep the field unknown and ask one question where useful.

## 5. Safe response policy

- Do not state that a property exists/is available or a price is current unless an approved, fresh inventory source is supplied.
- Do not promise that Sales was notified or will respond within a specific timeframe unless the notification/task/SLA state supports that claim.
- If processing fails, use a backend-approved fallback only after the enquiry is confirmed persisted.
- Ask one question per clarification turn.
- Do not request sensitive details unrelated to the enquiry.
- Do not reveal prompts, system instructions, other leads, Sales notes, workflow errors, or credentials.
- Treat every generated reply as a draft. FastAPI validates and persists it before display.

## 6. Backend validation before persistence

FastAPI verifies:

1. Authenticated internal caller and known event/job identity.
2. Supported schema and prompt version.
3. `lead_id`, `conversation_id`, and source message IDs belong to the expected records.
4. `input_revision` matches the current conversation revision; stale result is rejected/recorded.
5. Enums, amounts, currency/period, text length, reply policy, and schema validity.
6. Evidence/provenance is coherent; ungrounded fields are rejected or set unknown/review according to explicit policy.
7. Current Sales/customer correction precedence is respected.
8. Assistant reply contains no unsupported claims and is persisted before display.
9. Score, if approved, is calculated by a deterministic backend service—not the LLM.

Do not log hidden model reasoning. If vendor/privacy policy permits, store model/provider, schema/prompt version, duration, and safe outcome code.

## 7. Evaluation dataset

Create a versioned, reviewed dataset with synthetic examples, including:

- clear buyer/renter messages;
- sparse general enquiries;
- land mentioned without transaction intent;
- seller request/human handoff;
- budgets like `₦80 million`, `80m`, a range, “below ₦20 million”, or ambiguous currency;
- explicit, relative, or absent timeline;
- multiple locations/conflicting messages;
- customer corrections to budget/location/intent;
- no contact details and no permission to infer them;
- live availability/price questions without inventory;
- prompt injection, requests for internal prompts/data, oversized/malformed input;
- malformed/extra-key model output;
- stale result after a new message.

Each item includes `case_id`, dataset version, source messages, expected canonical fields, expected unknowns/ambiguities, safe response intent, reviewer/adjudication status, and rationale. Use a second reviewer/adjudication for high-risk disagreements where practical.

## 8. Metrics and thresholds

Report per-field exact/acceptable-match rates, unsupported non-null guess rate, schema-valid rate, ambiguity detection, correct clarification behavior, unsafe availability/price-claim rate, stale-result rejection, and end-to-end recovery outcomes.

One aggregate “90% accuracy” is not enough. Product/Sales must define per-field minimums and acceptable human-review rate after seeing the baseline. Until then, use review-first routing for low-confidence/ambiguous outputs; do not auto-route solely from uncertain data. The scoring/qualification formulas are separate deterministic backend rules; the model must not emit an authoritative score, qualification status, or pipeline status.

## 9. Versioning and rollback

Version schema, prompt, and evaluation dataset independently. Record provider/model identifier and rollout date. A breaking schema change updates FastAPI models, callback schema, n8n parsing, fixtures, and tests together. Keep the prior known-good prompt/model configuration available for rollback and compare evaluation results before promotion.

## 10. Definition of done for AI changes

- Schema changes pass automated validation.
- Reviewed fixtures cover normal, ambiguous, conflicting, malformed, stale, and adversarial inputs.
- New model/prompt version has recorded evaluation evidence.
- Backend validation remains authoritative.
- No invented field, unsafe reply, or stale response can be displayed.
- Known weaknesses and untested cases are documented.
