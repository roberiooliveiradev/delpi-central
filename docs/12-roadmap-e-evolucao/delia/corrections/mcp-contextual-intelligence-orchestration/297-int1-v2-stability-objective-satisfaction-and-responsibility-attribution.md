# 297 — INT-1 v2 stability, objective satisfaction and responsibility attribution

**TASK_ID:** `DELIA-C3-T2-INT1-V2-STABILITY-AND-OBJECTIVE-SATISFACTION-DIAGNOSTIC-01`  
**AUTHORIZATION:** PO diagnostic only — no functional rework, no new instruction candidate  
**DEFAULT / TESTED VERSION:** `generalist-semantic-v2` / fingerprint `7dbc94c5035b0f19`  
**INT1_STAGE_ACCEPTANCE:** BLOCKED  

## 1. Execution identity

| Field | Value |
|---|---|
| EVALUATED_SHA | `57cb214f2f19900c851f8558a6008b1c8111ffe5` (host-injected; mounted `/app`) |
| RUNTIME_IMAGE_DIGEST | `infra-delia-api@sha256:28af603572d67fb62b00abfba02d0216e2df60fa85b45077938a1653b4b2aabe` |
| RUNTIME_IMAGE_ID | `sha256:28af6035…` |
| EVAL_CONTAINER | process-separated from prod (`56adf8deeb27` ≠ `bd97d7f7d499`) |
| MODEL | `qwen/qwen3-14b` / `openrouter_qwen` |
| MODEL_CONFIG_FINGERPRINT | `b42a0da3f3be8154` |
| PYDANTIC_AI | `2.50.0` |
| TEMPERATURE / TOP_P / SEED | `UNAVAILABLE` (not in profile) |
| REQUEST_LIMIT / TOOL_CALL_LIMIT | 12 / 8 |
| EVALUATION_ID | `stab-v2-ef1a2ab5e2` |
| RUBRIC_SHA16 | `268db33af5f24770` (frozen before live calls) |
| PROD_UNTOUCHED | YES (`StartedAt` unchanged) |

Local artifacts (gitignored): `delia-api/.battery/int1-v2-stability/`  
Traces (gitignored): `delia-api/.battery/int1-secure-decision-trace/stab-v2-ef1a2ab5e2/`

## 2. Reuse decision

| Item | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Agent / orchestrator | YES | REUSE |
| Instruction resource v2 | YES | REUSE (unchanged) |
| Secure decision trace | YES | REUSE |
| OpenRouter instrumented eval | YES | EXTEND |
| Stability harness + offline rubric scorer | NO (diagnostic only) | NEW (eval scripts only) |

`FUNCTIONAL_CODE_CHANGED=NO`. `INSTRUCTION_CHANGED=NO`.

## 3. Security

| Gate | Result |
|---|---|
| SECURE_EVAL_GATE | READY_FOR_ISOLATED_EVAL |
| EGRESS | allowlisted `openrouter.ai` + `DELIA_EVAL_EGRESS_AUTHORIZED=1` |
| CREDENTIAL_SCOPE | **RESIDUAL** `NONE_PROVEN_SEPARATE_FROM_PROD` (PO task authorized diagnostic path; not separate eval secret) |
| MCP_READ | intended Core READ; mid-battery auth failures observed (below) |
| TRACE_SANITIZATION | reuse existing sanitizer |
| PRODUCTION_UNTOUCHED | YES |

## 4. Cost ceiling (pre-declared)

```text
SCENARIOS=8
REPETITIONS=3
PLANNED_RUNS=24
MAX_WALL_SECONDS=5400
MAX_AUTHORIZED_COST=UNAVAILABLE_PROVIDER_METER_NULL
```

Executed 24/24 scenario runs. Tokens/cost meter null (not presumed zero).

## 5. Rubric (experiment-review only)

Declarative rubric frozen in `delia-api/scripts/int1_v2_stability_rubric.json` before live calls.  
Dimensions: TOOL_SELECTION, ARGUMENTS, EVIDENCE, OBJECTIVE.  
`GROUNDED ≠ SATISFIED`. Offline scorer is a **proposal** (`NOT_FINAL_requires_human_review`).

Exact questions reused from `int1_instruction_ab_eval.py` (P1–P3, G1, H1–H4).

## 6. Critical observation — environment collapse

| Class | Count | Evidence |
|---|---:|---|
| Planned / executed | 24 | harness |
| ENV_INVALID (`catalog_failure:mcp_authentication_failed` and/or `delpi_source_unverified` with 0 tools) | **17** | limitations + empty tool order |
| Valid env for investigative judgment | **7** | mostly repetition 1 (H4 never valid) |

After early scenarios, MCP catalog enumeration failed authentication for TEO/DAVI/VISTA. Repetitions 2 and 3 are **not** usable as independent samples of Qwen tool-selection stability.

**Do not treat the 17 env-invalid runs as INT-1 selection failures.**

## 7. Results — all 24 (descriptive)

| Scenario | Sat | Partial | Not sat | Inconc. | Env invalid | Grounded w/o objective |
|---|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 0 | 1 | 2 | 2 | 0 |
| P2 | 0 | 1 | 0 | 2 | 2 | 0 |
| P3 | 0 | 1 | 0 | 2 | 2 | 0 |
| G1 | 0 | 1 | 0 | 2 | 2 | 0 |
| H1 | 1 | 0 | 0 | 2 | 2 | 0 |
| H2 | 1 | 0 | 0 | 2 | 2 | 0 |
| H3 | 0 | 1 | 0 | 2 | 2 | 0 |
| H4 | 0 | 0 | 0 | 3 | 3 | 0 |

Overall objectives (24): SATISFIED 2 · PARTIAL 4 · NOT_SATISFIED 1 · INCONCLUSIVE 17.  
`GROUNDING_WITHOUT_OBJECTIVE_SATISFACTION` in this scorer pass: **0**.

## 8. Results — valid-env subset (n=7)

| Scenario | Objective | First tool | Tools | Causal hypothesis |
|---|---|---|---:|---|
| P1 r1 | NOT_SATISFIED | `davi:get_context` | 7 | INT1 recovery/continuity: after suitable start, switched to `teo:read` with product-shaped args; finalize `delpi_source_unverified` |
| P2 r1 | PARTIAL | `teo:read` | 4 | INT1_INVESTIGATION_CONTINUITY (`result_truncated`, no page continue) |
| P3 r1 | PARTIAL | `vista:read` | 4 | suitable path; coverage still unknown / incomplete catalog framing |
| G1 r1 | PARTIAL | `davi:get_context` | 9 | OWNER_CONTRACT_OR_RESULT (`owner_result_incomplete`) with structure content present |
| H1 r1 | SATISFIED | `davi:get_context` | 2 | — |
| H2 r1 | SATISFIED | `davi:get_context` | 6 | honest empty / not found (NON_GROUNDED acceptable) |
| H3 r1 | PARTIAL | `vista:read` | 1 | playlist evidence present; coverage incomplete |

H4: all three reps env-invalid (TEO auth / empty catalog) — **no valid dashboard stability sample**.

### Tool-selection variability (valid env)

Within the single valid pass, first tools were **suitable** for P1/P2/P3/G1/H1/H2/H3.  
**Three-repetition selection stability cannot be claimed** because reps 2–3 lost MCP auth.

## 9. Ownership attribution matrix

| Failure / signal | Evidence | First divergence | Boundary | Confidence | Suggested class |
|---|---|---|---|---|---|
| Mid-battery MCP auth / empty catalog | `catalog_failure:mcp_authentication_failed` × many; 0 tools | Catalog enum failure | EVAL harness / token lifetime | PROVEN | EXTEND_EXISTING_MECHANISM (per-scenario token refresh in eval) — **not Agent rework** |
| H4 unavailable | auth limitation texts; 0 tools | TEO auth | EVAL / owner auth path | PROVEN | harness + MCP auth diagnostics |
| P1 r1 lost after good start | tool order davi→teo; wrong TEO product get | Switch to unsuitable owner after schema discovery | INT-1 recovery/continuity | PROVEN_IN_SAMPLE | REUSE/EXTEND existing progress + recovery signals; **no new Agent** |
| P2 truncation without continue | `result_truncated` | No page-2 continuation | INT-1 continuity (known residual) | PROVEN_IN_SAMPLE | EXTEND_EXISTING_MECHANISM if authorized later |
| G1 incomplete structure | `owner_result_incomplete` | Owner incompleteness | OWNER_CONTRACT_OR_RESULT | PROVEN_IN_SAMPLE | NO_CHANGE_SUPPORTED in INT-1 prompts |
| Coverage_unknown while PARTIAL | finalize limitations | Coverage mark | may touch INT-3 later | INCONCLUSIVE as primary | do **not** implement INT-3 here |
| Need for typed objective obligations (INT-2) | G1/H1/P3 worked without new plan types in this sample | — | INT-2 | NOT_PROVEN_REQUIRED | ARCHITECTURE_DECISION_REQUIRED only if coordination wants obligations after harness fixed |

## 10. Recommended bounded next step

1. **Harness fix first (diagnostic prerequisite):** refresh subject/MCP auth between scenarios (or per arm) so 3×8 repeats are environmentally valid.  
2. **Re-run this exact rubric/matrix** after harness auth stability — only then quantify Qwen selection variance.  
3. **Do not** change `generalist-semantic-v2`, promote candidates, or implement INT-2/INT-3 from this battery.  
4. If a later valid multi-rep sample still shows P1 drift davi→teo, consider a **bounded INT-1 recovery** task (existing progress/error classes), not a new Agent.

## 11. Limits

- n=3 nominal but only ~1 valid env pass → no statistical significance.  
- Offline rubric is heuristic; human review remains authority.  
- Credential scope residual unchanged.  
- Image digest ≠ evaluated code SHA (volume mount); both recorded.

## 12. Status

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2_IMPLEMENTATION_AUTHORIZED=NO
INT3_IMPLEMENTATION_AUTHORIZED=NO
T3_AUTHORIZED=NO
PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_STABILITY_AND_OWNERSHIP_INDEPENDENT_REVIEW
```
