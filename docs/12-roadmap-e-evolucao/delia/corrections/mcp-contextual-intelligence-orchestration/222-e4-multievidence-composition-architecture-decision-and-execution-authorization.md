# 222 — DÉLIA · E4 multi-evidence composition — coordination decision and bounded implementation authorization

**Date:** 2026-11-03. **DECISION_ID:** `DELIA-C3-MULTIEVIDENCE-COMPOSITION-E4-COORDINATION-DECISION-01`. **INPUT_EXECUTION:** `DELIA-C3-FRAMEWORK-NATIVE-CONTEXT-AND-MULTIEVIDENCE-ENDTOEND-DELIVERY-01`. **INPUT_SHA:** `989746ccdb`; `main` may advance concurrently, mandatory reanchor before diff. **Status:** `APPROVE_WITH_CONDITIONS` for additive composition of legitimately accessible evidence only. **Acceptance:** `NOT_YET_ACCEPTED`. **Production deploy:** `NOT_AUTHORIZED`.

## 1. Review verdict, evidence and exact scope

- **FIX-1 acceptance `ACCEPT_WITH_RESIDUAL`:** at evaluated SHA reported by executor, pydantic-ai 2.50.0 wire probe showed nonempty `message_history` + `Agent(system_prompt=...)` omitted current instructions. Replacing with `Agent(instructions=...)` in the infrastructure adapter and arggen was followed by authenticated real Qwen3 local A01/A02 with zero structured-schema retries. This is grounded in executor's repeatable tests and code; coordination verified GitHub code and ledger, not independent local execution.
- **Blocking business gap remains:** A03 had honest clarification / TÉO analysis delegation, single-turn comparison returned non-grounded admission; G04/G05/G07/G12 cannot be PASS.
- **Two full real trees were evaluated against a deterministic oracle:** Qwen3 made at least one false common-item claim and omitted a true common item. LLM suggestion is HYPOTHESIS, never FACT. This disproves direct factual trust.
- **Cancel/disconnect:** in-flight model request cancellation remains residual; deadline/retry cap only bounds eventual stop. Do not treat "no 504 in A02" as proof of cancellation.
- **No authorization changes** to Keycloak/Core/VISTA/TÉO/DAVI. No new planner, provider, store or Domain API owner. No production deploy.

**Decision:** authorize implementation of a small, framework-neutral, typed **composition proposal** through existing `InvokeModel` and **governed deterministic claim verifier** against multiple current/reauthorized `EvidenceFacts` from authorized READ subobjectives. This is DÉLIA-owned reasoning over evidence; it is not a newly created business analytics capability and does not replace the legitimate VISTA/TÉO owners where their exclusive operations are needed.

**Frozen contract:** ADR 58 / §6.145: `MODEL_AUTHORED_FACTUAL_PROSE=NONE`. Model identifies candidate joins/relations only. Final factual values and verdicts come from verified owner evidence and deterministic checks; renderer remains governed selection-only.

## 2. Ownership and contract-first implementation

**Owner:** DÉLIA Application Evidence / orchestration composition. **Data authority:** Domain API through authorized DAVI/MCP. **Consumers:** current interaction application and grounded synthesis / existing Outcome path. **LangGraph:** current state/fan-in of completed subobjectives, only if existing wiring supports it. **Pydantic AI:** existing infrastructure model invocation; no direct unrestricted tools. **Identity/AuthZ:** live Core and Domain checks on reads and revalidation.

Contract candidate: `multi-evidence-composition-proposal-v1`. Before coding, executor MUST freeze exact in-repo types, producer/consumer references, validators, errors, limits and version/compatibility in this document or adjacent contract owned by DÉLIA; prove `EXISTING_EQUIVALENT`/ `REUSE_DECISION` symbol-by-symbol. Do not add an abstraction just to name this contract.

### Input (Application-owned typed projection)

- `goal_ref`, `investigation_ref`, bounded ordered `completed_subobjectives[]`.
- `sources[]`: `source_ref`, `owner`, `capability`, `authoritative_entity_ref`, `fetched_at`/version/validity, `scope`, `authorization_state`, `completeness`, `truncation`, and typed per-record refs with business values verified by current owner result.
- Hierarchical BOM records when applicable: codes **as strings**, parent/path occurrence, type, unit, quantity/decimal precision, repeated rows/cardinality, and semantics of aggregation. If a meaningful field/aggregation rule is missing, explicitly classify insufficiency; never assume product domain units or aggregate repeated items blindly.
- A maximum number of sources/records/claims and token/timeout budget from **existing governed limits**; overflow yields an explicit limitation, not silent evidence loss.
- Client-supplied `prior_turns` are **referential semantic context only**, not `sources[]`.

### Output (untrusted typed model proposal)

- `proposed_pairs[]`: left/right `source_ref`, `record_ref`, optional occurrence/path references, named comparison dimension, candidate relationship, explicit limitations.
- `requested_missing_evidence[]` or `abstain`.
- NO authority, no new source facts, no final verdict, no self-asserted authorization and no free factual prose.

### Deterministic governed verifier (Application-owned)

- Re-resolve proposal references strictly against input evidence set; reject out-of-range, fabricated, mismatched or unauthorized refs and unrecognized dimension.
- Validate equality/difference/common/exclusive **on evidence-backed fields** with verified scope and comparison rules; precise numeric/decimal handling with unit equivalence, cardinality and structural position. Distinguish identical item codes at different BOM occurrences from genuine absence; compare totals only under an authorized typed aggregation policy.
- For claims unsupported by two complete compatible structures, mark `INCONCLUSIVE` with reason. Detect omission risk: model-selected subsets must not be marketed as exhaustive common/exclusive sets. Use deterministic coverage of all eligible records to determine completeness or explicitly state partial result.
- Enforce per-claim provenance, trust labels, auth, model hypothesis vs FACT separation, no model-authored factual answer prose. Outcomes `GROUNDED | INCONCLUSIVE` are determined by existing legitimate Outcome gate, not SDK output.
- No new permissions from model/agent metadata; no hidden auto-reads/writes. Only existing legitimate read capability calls and orchestration contracts.

### Negative behavior/errors

`SOURCE_UNAVAILABLE`, `OWNER_AUTHZ_DENIED`, `EVIDENCE_PARTIAL`, `SCOPE_MISMATCH`, `UNIT_NOT_COMPARABLE`, `DUPLICATE_OCCURRENCE_AMBIGUOUS`, `UNSUPPORTED_PROPOSAL`, `MODEL_SCHEMA_REJECTED`, `TURN_BUDGET_EXHAUSTED`, `CANCELLED` should map to existing error taxonomy when equivalent; avoid inventing a competing public taxonomy. No invented business facts and no silently merged data.

**Compatibility:** preserve public interaction schema, existing scalar compare contract where valid, legacy rollback, Pydantic AI provider-neutral port, current LangGraph sequencing, CRI factual renderer, authorized MCP paths. Add only required internal typed projection; an external contract change triggers the established versioning/OpenAPI gate.

## 3. Existing planner: the required orchestration behavior (without new planner)

Two supported paths must converge on **the same evidence composition boundary**:

1. **Single turn:** `Compare structures of X and Y` → existing semantic goal/subobjective selection proposes two authorized READs when necessary → actual DAVI/Domain data obtained for both → existing fan-in supplies verified evidence → bounded typed comparison proposal → deterministic verification → Outcome/render. Discovery is not itself business evidence; don't stop at `davi.discover` with no corresponding substantive read if the real goal requires two source results. Never hardcode codes, question patterns, owner names or provider branches.
2. **Same session:** user reads X; reads Y; asks `compare the two` → referents are resolved from bounded semantic context; any required business evidence is fetched or live-reauthorized; same fan-in and verifier. Do not replay old answer text as FACT and do not assume a text mention proves an identifier. If confidence/authorization cannot be established, ask targeted clarification.

**Existing foreign owner selection:** choose VISTA/TÉO if a *distinct*, legitimate owner-specific analytical operation is requested and authorized. A DÉLIA comparison of two read-authorized evidence sets must not be forcibly blocked solely because the user lacks optional VISTA/TÉO analytics. At the same time, do not invent equivalent capabilities or bypass a frozen owner routing contract. If the current `skip_comparison_declared` or owner selection contract categorically forbids an internal evidence comparison, STOP affected part and escalate precise `ARCHITECTURE_DECISION_REQUIRED`; do not mutate frozen semantic ownership silently. Continue independent contract/verifier work.

## 4. Implementation tasks — bounded, complete

**TASK_ID:** `DELIA-C3-GOVERNED-MULTIEVIDENCE-E4-IMPLEMENTATION-01`

1. Reanchor HEAD/status and authority order 16→50→17→49→51→52→21→20→25, ADR58, doc103, 219,220,221 R1, this doc222, ledger. Confirm current phase/CP/RQ and source/consumer contracts. No broad repeated inventory.
2. RED tests of both orchestration paths and claim validation, including Qwen3 pair-oracle errors, repeated hierarchy units and multi-owner scope; preserve actual negative safety cases.
3. Freeze minimal internal typed schema in Application, reuse `EvidenceFacts`, `OutcomeVerdict`, `InvokeModel`/Pydantic AI and existing graph state/fan-in; prove `REUSE/EXTEND`, no second planner.
4. Implement semantic subobjective evidence availability using existing planner plus authorized live READs. Ensure no accidental foreign dependency when direct authorized evidence legitimately suffices. Preserve explicit denial where owner truly requires permission.
5. Implement bounded typed comparison proposal and deterministic verifier with mandatory **coverage/completeness validation** and per-claim provenance. Test the known Qwen3 error (code `10030012` falsely common) and omission (`10030015`) as negative regression. The verdict must NEVER trust model candidate claims without checking owner evidence.
6. Integrate selected verified claims with current no-free-factual-prose synthesis and outcome, including clear natural PT-BR differences, units and missing-data limitations. No raw JSON dump.
7. Verify E3 residual cancellation and E5 cross-turn continuity within scope; any independent unfinished E2/E3/E5/E6 items from doc221 should be carried into coordinated completion, not marked PASS by implication.
8. Real local Qwen3 + Keycloak test `user@local.com` + live DAVI/Domain, **on final evaluated SHA**. Repeat A01→A02→A03/A04 in the same `conversation_id`; single-turn compound comparison; unrelated sibling owner questions; unknown product; revocation/AuthZ denial; injection; slow/timeout; model refusal; partial evidence; disconnected client.
9. Full relevant backend, SDK adapter, LangGraph, Evidence/CRI, interaction/stream and safety regression. Report tests `PASS|FAIL|INCONCLUSIVE|TEST_NOT_RUN` per gate and model variability. No tests removed to hide failures.
10. Remove actual redundant custom code with producer/consumer verification and before/after counts; no obligation to delete legitimate nine-consumer `ConversationContextTurn` merely for aesthetics.
11. Publish code, test traces, independent deterministic oracle, claims/provenance, compliance matrix, modifications/deletions and ledger. Push safely on main, preserving concurrent other-owner changes; no production deploy.

## 5. Mandatory acceptance — NO false completion

- `G04` multi-turn full comparison grounded, not just clarification.
- `G05` single-turn complete comparison grounded, not just truthful insufficiency when both structures were accessible.
- `G06` oracle's full tree pair used to *verify* content, not just model attempt.
- `G07` complete, unit/hierarchy-aware and provenance-backed verified common/exclusive/quantities.
- `G12` useful comprehensible PT-BR business comparison, no unsupported claims.
- `G01-G03,G08-G11` non-regression (and E3 cancellation tracked as residual if transport cannot prevent already in-flight work without redesign).
- Model not robust enough alone is NOT a reason to waive deterministic checks. The known wrong Qwen3 output must be rejected or corrected from verified data, not reproduced as fact.

**Final status:** `FUNCTIONAL_ACCEPTANCE_CANDIDATE` only after all applicable mandatory gates PASS. Otherwise `REWORK`, `BLOCKED_WITH_EVIDENCE` or `INCONCLUSIVE`, with exact blocking authority/test and completed independent safe work. Reviewer retains final decision. No phase advance or production deployment from a code push.

## 6. Decision guard

`ARCHITECTURE_DECISION=APPROVE_WITH_CONDITIONS`; `CONTRACT=multi-evidence-composition-proposal-v1` (internal additive typed proposal only); `EXISTING_EQUIVALENT=YES` for port/Evidence/graph/scalar verification; `TREE_COMPOSITION=EXTEND` with no proven full equivalent. `OWNER=DÉLIA Application`; `REUSE_DECISION=REUSE/EXTEND`; `MODEL_PROPOSAL_NOT_FACT=TRUE`; `MODEL_AUTHORED_FACTUAL_PROSE=NONE`; `CROSS_TURN_PRIOR_TEXT_NOT_FACT=TRUE`; `NO_NEW_PLANNER=TRUE`; `NO_NEW_PROVIDER=TRUE`; `PRODUCTION_DEPLOY=NOT_AUTHORIZED`.

This approval does not supersede a frozen owner/route/ADR. If evidence proves a conflict, mark `EXECUTION_DRIFT` or `ARCHITECTURE_DECISION_REQUIRED` and request scoped coordination, not silent reconciliation.
