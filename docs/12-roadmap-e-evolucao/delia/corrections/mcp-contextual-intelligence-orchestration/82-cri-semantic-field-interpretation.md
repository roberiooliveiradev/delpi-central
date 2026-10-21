# 82 — CRI semantic field interpretation: LLM proposes, owner declares, DÉLIA verifies

**Date:** 2026-10-21. **TASK_ID:** `DELIA-CRI-SEMANTIC-FIELD-INTERPRETATION-AND-AUTHORITY-ALIGNMENT-01`. **Type:** bounded refactor — removes the lexical business-meaning inference (`_field_declares_modification` token sets) from CRI presentation and replaces it with a model-proposed, contract-verified ordering semantic. **Preserves:** frozen selection-only (ADR 58), OFF byte-identical baseline, one goal stage (no new model call), all E2 sufficiency mechanics.

Follow-up to [79 — E4 real evaluation](./79-cri-e4-real-evaluation-rollback-and-acceptance.md) (residual E3-R2 lexical heuristic) and [81 — activation + audit](./81-cri-persistent-activation-and-code-audit.md) (`REQUIRES_DECISION: E3-R2 owner-schema semantic proof`).

## 1. Problem

E3-R2 blocked the defect "ordering ≠ alteration" by allowing modification wording only when the *proving field's own schema key* carried a modification marker (`updated_at`, `data_alteracao`, `atualizado_em`, camelCase variants, ~40 hardcoded tokens + connective allowlist in Python). Correct safety, wrong mechanism: the code owned a lexical theory of what field names mean — keyword heuristics encoding business semantics, exactly what DÉLIA-as-Continuous-Operational-Intelligence must not carry.

## 2. Contract inventory and reuse gate

| Need | Existing contract | Decision |
|---|---|---|
| Model interpretation point | goal stage (`_TurnGoal` / `answer_requirements` proposal inside `CAPABILITY_AND_GOAL_INSTRUCTION`) | **REUSE** — no new stage, no new call |
| Proposal surface | `parse_answer_requirements` typed hypothesis object | **EXTEND** — one optional sub-object `ordering_semantic` |
| Owner-declared semantics | `ProviderCapability.description` — for MCP verbatim tool description from `tools/list`; for OpenAPI the operation's semantic name. The same text the goal stage already projects to the model | **REUSE** — no registry, no owner-code change |
| Verification | deterministic leaf helpers in `outcome_assessment` | **EXTEND** — `verified_ordering_event()` |
| Presentation decision | `compose_cri_response(ordering_field=...)` | **EXTEND** — renamed to `ordering_event` (verified event or None) |
| Instruction to the model | governed declarative clause `delia.cri.answer_requirements_instruction` | **EXTEND** — v2 (v1 still a valid governed artifact; rollback-friendly) |

No `Semantic Field Registry`, no per-provider branch, no new agent, no second model call, no free-form factual authority.

## 3. Mechanism

```text
LLM (existing goal stage)
  → may propose ordering_semantic = {
      event: "modification",            # bounded vocabulary, parse rejects others
      field: "<a record field>",        # must appear inside the cited evidence
      contract_evidence: "<verbatim quote from the capability description>"
    }
  → DÉLIA verifies deterministically at the outcome→response edge:
      a) ordering itself must be proven (unchanged E2 mechanics);
      b) semantic.field must equal the field that ACTUALLY proves the
         ordering in the returned records (ordering_proof_fields);
      c) contract_evidence must be a verbatim substring of the
         owner-declared capability description;
      → verified event | None
  → composer emits "alterado" wording only on verified event
     (ordering_event == "modification"); otherwise neutral lead +
     "a fonte não comprova que ela represente uma alteração".
```

A fabricated or paraphrased quote, a mismatched field, an unknown event, a semantic without `ordering`, extra keys, or absent owner text all degrade to `None` — meaning unproven, honestly stated. Field names alone never carry meaning; the E3-R2 token sets and `_field_declares_modification` are deleted (~95 lines of Python).

Observability: the `stage=cri_response` decision log now reports `semantic_proposed=<bool>` and `ordering_event=<event|none>` — bounded decision metadata, never payload content.

## 4. Instruction resource v2

`delia.cri.answer_requirements_instruction` v2 extends the requirements grammar with `ordering_semantic` and bounds it: quote only text literally present in the capability description; the semantic interprets *returned records* and is never a request argument; omit when no declared meaning supports the claim. Loader accepts `{1, 2}` — v1 remains valid for rollback. First v2 draft observed live to nudge the model into passing `date_field` as a *request filter* (owner-rejected for entity `process`); the published text explicitly decouples semantic interpretation from request arguments — the rejection class disappeared on retest.

## 5. Evidence

**Unit/integration:** full suite PASS in container (`infra-delia-api`, repo mount). New E2 section covers: valid parse; bounded event vocabulary rejection; evidence-not-referencing-field rejection; missing/extra keys; non-mapping; semantic-without-ordering; verified event on real quote; fabricated quote rejected; proving-field mismatch; no proving field; absent proposal; hostile contract text not leveraged. E3 block rewritten to `ordering_event` contract: verified event → alteration wording; unverified → neutral + unproven clause; suggestive names (`data_alteracao`, `updated_at`, `dataAlteracao`) stay neutral without verification; unknown event values stay neutral; two orchestrator integration tests exercise the full model→verify→compose edge (positive: verified quote unlocks "mais recentemente alterado"; negative: quote absent from capability description stays neutral).

**Live (isolated eval container, worktree mount, `effective=cri`, resources v2+v2):**
- `requested=cri effective=cri`, instruction v2 `sha256 d5d0f75d…`, vocabulary v2.
- Real TÉO `record_read` turns: plain list GROUNDED; "3 processos alterados mais recentemente" GROUNDED with 3 records + owner total attribution; "último processo alterado" honestly insufficient when the model fetches `page_size=1` (one record cannot prove ordering — correct pre-existing E2 semantics).
- `semantic_proposed=False ordering_event=none` on every observed turn: the model correctly abstains because TÉO's tool description declares no field meaning to quote — the intended abstention, not a failure.
- No `date_field` filter misuse after the v2 refinement; no writes; no new model stage; latency unchanged (19–30s model-bound).
- OFF parity: unchanged — the flag, resource loading and byte-identical baseline are untouched; E1 suite green.

## 6. Contractual gap recorded

No current owner contract declares field event semantics: TÉO `record_read` describes actions/filters, VISTA and DAVI describe operations, DELPI projections carry semantic names. Therefore the verified-modification wording path is exercised in tests but cannot trigger on real owners yet — modification claims stay honestly unproven, which is the designed safe state. **Owner-side contract evolution** (e.g. tool descriptions or schema property descriptions declaring `updated_at` as "data de atualização do registro") is the legitimate unlock and requires a separate decision — recorded, not improvised inside DÉLIA.

## 7. Residuals

- `B1` single-ticket lexical shortcut: untouched, still deferred (out of scope).
- `orchestration.py` size: unchanged; broad refactor remains out of scope.
- Live positive-path (verified event → "alterado" wording) pending owner contract evolution per §6.
- Model may still choose `page_size=1` for superlative intents → honest `ordering_unproven`; pre-existing E2 semantics, not a regression.

## 8. Report

```text
TASK_ID=DELIA-CRI-SEMANTIC-FIELD-INTERPRETATION-AND-AUTHORITY-ALIGNMENT-01

EXISTING_EQUIVALENT=YES (goal stage + answer_requirements + capability.description
    + deterministic leaf verification — all pre-existing contracts)
REUSE_DECISION=REUSE+EXTEND (minimal: one optional sub-object, one verifier,
    one composer parameter, resource v2)

GOAL_STAGE_REUSED=YES (CAPABILITY_AND_GOAL_INSTRUCTION + injected CRI clause)
MODEL_PROPOSAL_CONTRACT=answer_requirements.ordering_semantic
    {event, field, contract_evidence} — parse fail-closed, bounded keys/values
AUTHORITATIVE_SEMANTIC_SOURCE=ProviderCapability.description
    (MCP: verbatim tool description; OpenAPI: operation semantic name)
SEMANTIC_CONTRACT_VERIFICATION=verified_ordering_event()
    — field must equal the actual proving field; evidence must be a
    verbatim substring of owner contract text; bounded event vocabulary

LEXICAL_HEURISTIC_REMOVED=YES (_field_declares_modification,
    _MODIFICATION_FIELD_TOKENS, _TEMPORAL_FIELD_CONNECTIVES, tokenizers — ~95 lines)
PROVIDER_SPECIFIC_BRANCHES=0
NEW_REGISTRIES=0
NEW_MODEL_STAGES=0

ORDERING_PROOF=UNCHANGED (ordering_proof_fields / _temporal_proofs)
COVERAGE_PROOF=UNCHANGED
OUTCOME_ASSESSMENT=UNCHANGED (one verdict, same edge)
GROUNDED_PRESENTATION=ordering_field → ordering_event;
    "alterado" wording only on verified event

DECLARATIVE_RESOURCE_CHANGES=cri_instructions.delpi.json v1 → v2
    (v1 still accepted; ordering_semantic grammar + request-arg decoupling)
PUBLIC_CONTRACT_CHANGES=NONE (internal proposal/compose contracts only)

OFF_BASELINE_PARITY=PASS (E1 suite; flag/loader/baseline untouched)
ON_GENERALIZATION=PASS (unit: arbitrary field names, any owner text;
    verification is contract-text-bound, never name-bound)
MODEL_CALL_DELTA=0
LATENCY_DELTA=0 (observed 19–30s, unchanged composition)
SECURITY_NEGATIVE_TESTS=PASS (fabricated quote, field mismatch, hostile
    contract text, unknown event, extra keys, semantic without ordering)

BACKEND_TESTS=PASS (full suite, exit 0)
REAL_MODEL_EVALUATION=EXECUTED (isolated eval container, real kimi-k3,
    real TÉO MCP; model correctly abstains — no declared semantics to cite)
REAL_OWNER_EVALUATION=PASS (TÉO record_read GROUNDED turns;
    honest insufficient_evidence on unprovable ordering)

RUNTIME_CODE_CHANGED=YES (3 app files + 2 governed artifacts + 2 test files)
PRODUCTION_ACTIVATION=NO
CRI_DEV_ENABLED=YES_PERSISTENT (unchanged; eval ran isolated worktree container)

MATERIAL_RESIDUALS=owner contracts declare no field event semantics →
    positive modification wording cannot trigger on real owners until an
    owner-side contract evolution (separate decision required)
NON_BLOCKING_RESIDUALS=B1 deferred; model page_size=1 on superlatives
    → honest ordering_unproven; orchestration.py size unchanged
```


## 9. Independent coordination review — 2026-10-21

**Verdict: `ACCEPT_WITH_RESIDUAL` for removing lexical business-semantics inference, NOT positive-path acceptance of authoritative semantic meaning.** Published implementation SHA `34a75d12a7ffcee3e4c7058969fa84fdd586e20a` statically inspected via GitHub (`outcome_assessment.py`, `conversational_response.py`, report 82); independent test re-execution `TEST_NOT_RUN`. Executor reports full backend suite PASS and real TÉO grounded reads with correct semantic abstention. CRI development mode was reportedly kept ON; independent runtime verification `TEST_NOT_RUN`.

**Accepted:** `_field_declares_modification` and token lists removed; same goal-model stage reused; typed `ordering_semantic` with bounded fields; no provider branches, new registry, extra mandatory model stage, or ADR58 factual synthesis change. Missing owner declaration results in neutral wording — safety-preserving.

**Material boundary / semantic-verification gap:** `verified_ordering_event()` checks only (a) proposed field equals the field that proves returned-record ordering and (b) the LLM-provided quote is a **literal substring** of `ProviderCapability.description`. `_parse_ordering_semantic` requires the field name in that quote. **Neither check establishes that the quoted owner text actually declares the model-proposed `event` meaning for that field.** A truthful owner description merely mentioning a field, or explicitly negating its modification meaning, can satisfy the current byte/field checks while the LLM proposes `event=modification`. A verbatim quote is evidence of text provenance, not proof of semantic entailment. Metadata/tool descriptions are untrusted interoperability data and cannot themselves create business authority. The report's `SEMANTIC_CONTRACT_VERIFICATION=PASS` should be read narrowly as *quote and field binding verified*, not authoritative event semantics proven. Do not treat the live-abstention test as a positive-path business outcome.

**Owner-contract gap:** Actual TÉO `record_read` capability description does not declare field-event semantics accessible to the existing goal stage, even though the owner-side repository has `updated_at` update-order behavior. Owner must expose an approved, consumer-appropriate schema/contract or other authoritative representation through the existing boundary. Only then can runtime proof be tested. Prefer a stable typed owner declaration bound to field/event over LLM-selected quote substrings; use the LLM to interpret/match semantic intent, deterministic code to verify legitimate typed claims. Do not solve this by new regex, token dictionaries, provider-specific Python branches, or a parallel registry.

**Operational residual:** Real superlative turns can lead the model to select unsupported `date_field` arguments or `page_size=1`, causing fail-closed NON_GROUNDED or insufficient coverage. This is a measurable task-outcome/generalization gap; inspect existing owner argument schema and proposal boundaries before deciding a bounded correction. Do not silently increase the deadline or redesign planning.

**Next decision:** separately scope the *owner-contract publication + bound semantic verification* and the *superlative argument quality* against the canonical authority chain. No immediate second implementation round or production activation from this review; preserve current dev ON and operational safeguards. `LEXICAL_HEURISTIC_REMOVAL=ACCEPTED_WITH_RESIDUAL`; `AUTHORITATIVE_EVENT_PROOF=INCONCLUSIVE`; `SEMANTIC_POSITIVE_PATH=TEST_NOT_RUN_LIVE`; `CRI_PRODUCTION_ON=NOT_AUTHORIZED`; `I04_ACCEPTED=NO`; `C3_EXECUTED=NO`.

## 10. Direct MCP/plugin and GitHub contract verification — 2026-10-21

READ-only inspection of connected TEO, VISTA and DAVI plugin tools and DÉLIA GitHub source. No runtime changes or independent test execution.

- TÉO: get_catalog returns entity_schemas and capability_surface. Process search filterable_fields include page, page_size, q, but not date_field; instance/revision filterable fields include date_field. Tool-level record_read signature nevertheless accepts optional date_field without entity-specific constraint: entity-dependent argument admissibility must be validated by the owner contract. Process lists created_at/updated_at as server-owned, but inspected catalog did not expose a typed field-to-modification-event declaration. Prior owner code may document update/order behavior; the contract presented to the DÉLIA model is insufficient to prove that meaning.
- VISTA: get_catalog publishes typed operations, field vocabularies and data-model presentation contracts; list_playlists advertises limit/offset pagination. No general temporal field-event contract was proven in inspected surface.
- DAVI: discover_delpi_information publishes candidate argument_schema, semantic_hints, pagination_hints. Query about most recently modified processes returned candidate_count=0 with eligible_action_count=95. Discovery miss is not evidence that underlying records or a capability are absent. Metadata is descriptive, not AuthZ or domain authority.
- DÉLIA: verified_ordering_event confirms proposed field equals actual ordering proof field and quoted text occurs literally in ProviderCapability.description. It does NOT establish that the quote semantically entails the proposed event; merely mentioning or negating an event can satisfy substring validation. Current check is textual provenance/binding, NOT authoritative event meaning proof.

Reuse gates: LLM goal/answer_requirements EXISTING_EQUIVALENT=YES, REUSE_DECISION=EXTEND. Typed owner field-event/order semantics EXISTING_EQUIVALENT=TO_INVENTORY, REUSE_DECISION=TO_DECIDE_AFTER_OWNER_CONTRACT_CHECK (prefer extending existing Domain API/MCP projection, not building a DÉLIA registry). Entity-specific argument contracts EXISTING_EQUIVALENT=YES, REUSE_DECISION=REUSE/EXTEND, validate before provider invocation. Pagination sufficiency reuse existing evidence/outcome contracts.

Recommended bounded next steps: inspect existing TÉO authoritative field/event/order contract and consuming projection; if truly absent authorize owner-controlled typed publication in existing contract; bind LLM hypothesis to owner-approved semantics deterministically; independently resolve entity-sensitive date_field and superlative page_size/coverage issues with existing schema; run generalization and real TÉO read eval. No regex, hardcoded provider branches, duplicate registry or new model stage.

EVIDENCE_STATUS=LIVE_PLUGIN_AND_STATIC_GITHUB_VERIFIED; INDEPENDENT_RUNTIME_TEST=TEST_NOT_RUN; SEMANTIC_POSITIVE_PATH=NOT_PROVEN; PRODUCTION_ACTIVATION=NOT_AUTHORIZED; I04_ACCEPTED=NO; C3_EXECUTED=NO.
