# 08 — I02-R1 Independent Diagnostic Acceptance

**DATE:** 2026-10-17. **REVIEWED_HEAD:** `0dbca64e6a78f43881a8228d9d2168dfa85723f5`. **VERDICT:** `ACCEPT_WITH_RESIDUAL` for diagnosis ONLY; `I02_ACCEPTED=NO`.

## Evidence
Independent GitHub review of [07](./07-i02r1-post-fix-validation-and-latency-diagnosis.md) and `OperationalCapabilityOrchestrator` index paths. Executor reported live at deployed `abc6e28e322b47bb4bb06e99c5c7463c52a23862`, model `moonshotai/kimi-k3`, config `5062d3b7f10fecaa`: K3 `index_probe` model 19289ms, owner READ 0, total 30024ms, terminal `model_timeout`; nested guide projection **NOT_REACHED**, hence `NESTED_FIX_LIVE_VALIDATED=INCONCLUSIVE`. K1 TÉO 17816ms successful but pre-owner model sequence remains costly. Telemetry/tests are executor-reported, not independently reexecuted.

## Architecture review: what is and is not authorized
**Proven observed K3 cause:** sequential pre-owner model proposals, especially optional self-index model probe, exhausted 30s before owner READ. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND_CANDIDATE` of existing `TurnDeadline`, `_eligible_self_index_probe`, owner index contract, `_propose_index_probe`, schema validation, and argument planner.

**Not approved as formulated:** catch `_StageDeadlineExceeded` after global deadline exhaustion and proceed to owner READ. A fully expired shared deadline is terminal, and a schema-valid empty READ is not automatically semantically sufficient. A guide call without topic may only return an index, not the user's requested guidance.

**Recommended I02-R2 direction:** before invoking model-driven self-index, determine from live owner contract whether omitted optional identifier deterministically returns an index. Preserve that existing owner-declared path when needed; if index necessity cannot be established, do not assume direct empty READ yields the answer. Allocate bounded probe/stage headroom **before** invoking the model so any probe timeout is recoverable only if overall TurnDeadline remains positive and subsequent validated READ plus presentation are viable. Otherwise skip optional probe when safe, degrade to clarification/insufficiency or terminate on exhausted global budget. No fixed provider names, no AuthZ bypass, no synthetic identifier, no automatic ACT. Precisely profile/retest in RED/GREEN; the behavior is a design candidate, not implemented/accepted.

**Remaining gaps:** nested fix not live exercised; topic/index selection quality; successful K1→K2→K3 user outcomes; provider-neutral holdouts; possibility that four other model stages still consume excessive time. All remain I02, not I03/Q phase.

```text
I02_R1_DIAGNOSTIC_REVIEW=ACCEPT_WITH_RESIDUAL
I02_ACCEPTED=NO
K3_PRE_OWNER_LATENCY_CAUSE=PROVEN_FOR_EVALUATED_PATH
NESTED_FIX_LIVE_VALIDATED=INCONCLUSIVE
TIMEOUT_TO_UNBOUNDED_READ=REJECTED
I02_R2_DIRECTION=PRE_PROBE_HEADROOM_AND_OWNER_CONTRACT_FIRST
I02_R2_IMPLEMENTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
NEXT=I02_R2_CONTRACT_AND_RED_GATE
```
