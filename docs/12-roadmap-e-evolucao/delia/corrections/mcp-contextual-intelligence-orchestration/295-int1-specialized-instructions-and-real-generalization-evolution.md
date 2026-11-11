# 295 — INT-1 specialized instructions isolation and real generalization evolution

**TASK_ID:** `DELIA-C3-T2-INT1-SPECIALIZED-INSTRUCTIONS-AND-REAL-GENERALIZATION-EVOLUTION-01`
**PO_AUTHORIZED_BOUNDED_REWORK:** YES (explicit exception to exhausted rework budget; not unlimited)
**EXISTING_EQUIVALENT:** YES (`PydanticAiInvestigationOrchestrator`)
**REUSE_DECISION:** EXTEND
**INT1_STAGE_ACCEPTANCE:** BLOCKED

## 1. Isolation

| Item | Result |
|---|---|
| Runtime | Reused `pydantic_ai_investigation.py` Agent |
| Instructions | Extracted to `delia-api/config/investigation_instructions.delpi.json` |
| Loader | Extended governed pattern in `cri_instruction_resource.py` (`load_investigation_instructions`) |
| Active selection | `default_instruction_version` + optional `DELIA_INVESTIGATION_INSTRUCTION_VERSION` |
| Old inline prose | Removed from Python module |
| Admission/orchestration JSON | Untouched |
| Default active version | **`generalist-semantic-v2`** (baseline preserved) |

## 2. Versions

| Version | Fingerprint | Role |
|---|---|---|
| `generalist-semantic-v2` | `7dbc94c5035b0f19` | Frozen baseline (byte-equivalent extraction) |
| `generalist-semantic-v3-objective-progress` | `658d3da51783e23d` | Single cognitive candidate (not promoted) |

Candidate themes (provider-agnostic): objective/evidence-kind orientation; compare description↔schema↔output shape; argument/schema discipline; published error-class recovery; “new info ≠ progress”; efficiency / strategy change; honest finalization.

## 3. Real A/B evaluation

| Field | Value |
|---|---|
| Model | `qwen/qwen3-14b` / `openrouter_qwen` / pydantic-ai `2.50.0` |
| Egress | allowlisted OpenRouter (`DELIA_EVAL_EGRESS_AUTHORIZED=1`); no localhost proxy |
| Prod untouched | YES |
| Credential residual | shared infra LLM key scope |
| Dataset | P1,P2,P3,G1 + holdouts H1–H4 frozen before candidate run |
| Local comparison artifact | `delia-api/.battery/int1-instruction-ab-eval/ab-comparison.json` (gitignored) |

### Known cases

| Scenario | Baseline | Candidate | Notes |
|---|---|---|---|
| P1 structure | GROUNDED; first `davi:read`; BOM | GROUNDED; first `teo:read`; content drifted to description | **Critical regression** |
| P2 processes | GROUNDED | NON_GROUNDED | **Regression** |
| P3 viz formats | NON_GROUNDED; first `vista:read` | GROUNDED; `vista:get_context`→read; block_types | Improvement |
| G1 reword structure | NON_GROUNDED; 8 calls | GROUNDED BOM; 3 calls | Improvement |

### Holdouts

| Scenario | Baseline | Candidate | Notes |
|---|---|---|---|
| H1 product description | GROUNDED | GROUNDED | Stable |
| H2 missing product | NON_GROUNDED | NON_GROUNDED | Honest empty preserved |
| H3 playlists | GROUNDED | GROUNDED | Stable |
| H4 live dashboard summary | NON_GROUNDED; 0 tools | GROUNDED; `teo:analyze` | Improvement |

Tokens/cost: provider usage fields unavailable in meter (`null` — not presumed zero).

## 4. Promotion decision

**CANDIDATE_PROMOTION_RECOMMENDATION: DO_NOT_PROMOTE**

Reasons:

1. P1 objective regression (structure → description-like answer; wrong first specialist).
2. P2 grounding regression.
3. Gains on P3/G1/H4 do not outweigh critical known-case failure.
4. Default remains `generalist-semantic-v2`.

Process value delivered: versioned instruction resource, fingerprinting, A/B harness, holdout discipline.

## 5. Architecture boundary

Defects that remain after one candidate are not solved by further unbounded prompt iteration in this task. Material remaining gaps may belong to INT-2 (objective/evidence obligations) or INT-3 (coverage acceptance) — **not authorized here**.

## 6. Status

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2_AUTHORIZED=NO
T3_AUTHORIZED=NO
PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_SPECIALIZED_INSTRUCTIONS_INDEPENDENT_REVIEW
```
