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
