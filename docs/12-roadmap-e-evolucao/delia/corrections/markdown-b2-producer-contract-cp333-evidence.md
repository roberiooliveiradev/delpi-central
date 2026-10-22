# DÉLIA — Markdown B2 / Producer Contract / CP-333 — evidence and implementation gate

TASK_ID: DELIA-C3-MARKDOWN-B2-PRODUCER-CONTRACT-AND-CP333-01
Reviewed GitHub main HEAD: d63b8985c9db41f5bb4a0d22b0170e6112c3c1a2
Date: 2026-10-22
Status: INCONCLUSIVE FOR CONTRACT FREEZE; read-only review, no runtime modifications.

## Verified direct-source facts

1. `delia-api/app/application/interaction/presentation.py`: `PRESENTATION_CONTRACT_VERSION = "1"`. `compose_presentation(result)` emits `version`, `message_kind`, `semantic_status`, `grounding_status`, `blocks`, `allowed_interactions`. Allowed block kinds: text and notice; max 8 blocks and 16,384 chars per block. It reads governed `InteractiveTurnResult`, not arbitrary provider payload, and preserves the canonical message-kind and confirmation vocabulary.
2. `delia-api/app/application/interaction/handle_interactive_turn.py`: the serialized interaction field is `"presentation": compose_presentation(result)`, with legacy top-level fields retained. This is the confirmed producer/serialization edge.
3. `plugins/delia/src/api/presentation.ts`: the v2 reader is parse-only; version 2 requires a closed envelope of `version, message_kind, semantic_status, grounding_status, blocks, allowed_interactions`; v2 text blocks require `format = plain|markdown_safe` and `text`. The reader reports `not_v2|neutral_error|ok`. An unknown contract version does not coerce into v2. Malformed v2 returns neutral_error; calling layer must be traced before asserting user-visible fallback.
4. IMPORTANT discrepancy: `authorized_links` is NOT an allowed field in the examined v2 envelope or text block. It must NOT be added by the producer without a contract reconciliation/approved schema extension. The frontend comment explicitly says it does not invent authorized links.
5. The existing v1 producer does not emit v2 or `markdown_safe`; the v2 reader's presence is not runtime acceptance.

## Reuse gate

- Presentation composition: EXISTING_EQUIVALENT=YES; REUSE_DECISION=EXTEND existing `compose_presentation`.
- Interactive result/epistemic classification: YES; REUSE.
- Frontend typed v1/v2 readers: YES; REUSE.
- Frontend Markdown/code block: handoff reports implemented; runtime component and spec 96 verification remain TO_INVENTORY in this scoped connector review; DO NOT duplicate.
- Authorized link emission/admission: TO_INVENTORY due to missing v2 wire field; neither invent a new authority nor assume it is part of the producer contract.
- A second presentation engine: REUSE_DECISION=DO_NOT_CREATE.

## Boundaries and recommended finite implementation design (not authorized yet)

Preferred conditional direction: deterministic Markdown serialization of already-governed textual or structured presentation fields, emitted from the existing presentation boundary. Markdown is presentation, not factual synthesis and not an AuthZ channel. Preserve ADR 58 selection-only; no LLM stage added merely for formatting; no MCP/provider-specific branches. If content cannot be admitted, use existing plain path. Do not silently promote non-grounded data to grounded.

Before choosing version/format gates, resolve:
- Canonical docs 82/83/84/91/96 and CP-333 exact wording, owners, RQ/AC and phase against HEAD; current review has not fetched their verified canonical sections.
- How the MFE host selects `parsePresentationV2` and the response rendering gate; `presentationFault` and authorized-link transport, neither proven at this producer edge.
- Any prior frozen decision constraining Markdown tokens and link admission.
- JSON/NDJSON reader behavior on malformed v2, including no unauthorized link clickability.

No runtime code change, no deployment, no CP-333 acceptance claimed.

## Proposed bounded implementation package after contract gate

A. RED tests for v1 byte-for-byte compatibility, a grounded text block with admitted safe Markdown, non-grounded/clarification/confirmation cases, invalid token/link/HTML/code payloads, overlong content, unsupported format and plain fallback.
B. Extend existing composer/serializer with deterministic v2 opt-in only when frozen contract permits. Avoid new engine, registry, model step or provider branches.
C. Test actual JSON and NDJSON serialization, frontend parser/rendering, security controls, RQ/AC matrix and outcome on evaluated SHA/config.
D. Report factual evidence, docs and ledger; send to coordination for ACCEPT / REWORK decision. Deploy excluded from this documentary task.

## Current verdict

PRESENTATION_PRODUCER=compose_presentation version 1 (PROVEN)
PRESENTATION_CONSUMER_V2=parsePresentationV2 parse-only (PROVEN)
MARKDOWN_SAFE_BACKEND_EMITTER=NOT_IMPLEMENTED at reviewed producer (PROVEN)
AUTHORIZED_LINKS_WIRE=TO_INVENTORY; mismatch with conceptual brief
PRESENTATION_FAULT_WIRE=TO_INVENTORY
CP_333_ACCEPTANCE=NOT_PROVEN
GENERALIZATION_EVALS=TEST_NOT_RUN
RUNTIME_CHANGED=NO
DEPLOYMENT=NOT_APPLICABLE
ARCHITECTURE_DECISION_REQUIRED=YES_IF canonical CP-333 requires authorized_links outside current v2 contract or free factual prose
NEXT_BOUNDED_IMPLEMENTATION=BLOCKED_ON_CANONICAL_CONTRACT_RECONCILIATION; finite tests/package described above
REVIEW_RECOMMENDATION=INCONCLUSIVE pending formal CP-333 and thematic-spec verification
