# 298 — INT-1 MCP evaluation authentication lifecycle remediation and v2 stability rerun

**TASK_ID:** `DELIA-C3-T2-INT1-MCP-EVAL-AUTH-LIFETIME-REMEDIATION-AND-V2-STABILITY-RERUN-01`  
**AUTHORIZATION:** PO — harness auth lifecycle remediation + diagnostic rerun of frozen baseline v2 only  
**DEFAULT / TESTED VERSION:** `generalist-semantic-v2` / fingerprint `7dbc94c5035b0f19`  
**INT1_STAGE_ACCEPTANCE:** BLOCKED  
**FUNCTIONAL_AGENT_CODE_CHANGED:** NO  
**INSTRUCTION_CHANGED:** NO  

## 1. Execution identity

| Field | Value |
|---|---|
| BASE_HEAD (task start) | `c39a578eea7e2303d694086ec1ce1329cc4611e3` (REFERENCE_HEAD `4e74d11b…` was ancestral) |
| EVALUATED_SHA | `c39a578eea7e2303d694086ec1ce1329cc4611e3` |
| RUNTIME_IMAGE_DIGEST | `infra-delia-api@sha256:28af603572d67fb62b00abfba02d0216e2df60fa85b45077938a1653b4b2aabe` |
| EVALUATION_ID | `stab-v2-5b0e914eb9` |
| MODEL | `qwen/qwen3-14b` / `openrouter_qwen` |
| MODEL_CONFIG_FINGERPRINT | `b42a0da3f3be8154` |
| PYDANTIC_AI | `2.50.0` |
| REQUEST_LIMIT / TOOL_CALL_LIMIT | 12 / 8 |
| RUBRIC_SHA16 (file bytes) | `268db33af5f24770` — matches Documento 297 freeze |
| RUBRIC_SHA16 (canonical JSON dump used in meta) | `e84ad551ef9cba8c` — same rubric content, different hash input (`json.dumps(sort_keys=True)`); **not content drift** |
| PROD_UNTOUCHED | YES |

Local artifacts (gitignored): `delia-api/.battery/int1-v2-stability-rerun/`  
Prior invalid battery (doc 297): `delia-api/.battery/int1-v2-stability/`

## 2. Auth root cause (proven)

| Item | Value |
|---|---|
| AUTH_ROOT_CAUSE | `SUBJECT_ACCESS_TOKEN_REUSED_BEYOND_EXPIRES_IN` |
| AUTH_FAILURE_BOUNDARY | subject bearer (password grant) → delegated exchange → MCP `tools/list` / catalog |
| TOKEN_ACQUISITION | existing `acquire_subject_access_session` / Portal Keycloak password-grant gateway |
| PRIOR FAILURE TIMING | first catalog auth collapse ≈413s into previous battery (`expires_in=300`) |
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | EXTEND — reacquire subject session **per scenario**; recreate MCP clients with fresh headers; no parallel auth service; no custom refresh grant |

Sanitized timeline (rerun): every scenario recorded `AUTH_ACQUIRED_AT` / `AUTH_EXPIRES_AT` (`expires_in=300`), `subject_session_fresh=true`, unique `auth_token_fingerprint` ×24, and `catalog_auth_result.auth_valid=true` for DAVI/TEO/VISTA before LLM spend.

## 3. Minimal harness diff

| Path | Change |
|---|---|
| `delia-api/scripts/int1_eval_subject_auth.py` | NEW shared helpers: acquire session, expiry metadata, fingerprint (no token logging) |
| `delia-api/scripts/int1_v2_stability_eval.py` | per-scenario reacquire + catalog preflight; artifact dir `int1-v2-stability-rerun`; auth lifecycle meta |
| `delia-api/scripts/run_int1_v2_stability_eval.sh` | task id / artifact path |
| `delia-api/scripts/int1_mcp_auth_probe.py` | lifetime probe + reacquire fingerprint check |
| `delia-api/scripts/native_mcptoolset_direct_eval.py` | re-export shared auth helpers |
| `delia-api/tests/test_int1_eval_subject_token_lifecycle.py` | offline lifecycle: valid / expired / near-expiry / reacquire / denied / no token leak |

Not changed: Agent, instructions JSON, MCP descriptions, Owner APIs, Core permissions, Keycloak prod config.

## 4. Security

| Gate | Result |
|---|---|
| SECURE_EVAL_GATE | READY_FOR_ISOLATED_EVAL (PO-authorized diagnostic path + allowlist) |
| EGRESS | `openrouter.ai` + `DELIA_EVAL_EGRESS_AUTHORIZED=1` |
| CREDENTIAL_SCOPE | **RESIDUAL** `NONE_PROVEN_SEPARATE_FROM_PROD` |
| MCP_READ probe | LIST_OK DAVI/TEO/VISTA; reacquire fingerprint changed; LIST_OK after reacquire |
| TRACE_SANITIZATION | no bearer/JWT in published comparison JSON |
| PRODUCTION_UNTOUCHED | YES |

PO authorization for this diagnostic **does not** close the credential-isolation residual.

## 5. Auth lifetime validation (before 24× LLM)

| Check | Result |
|---|---|
| Offline pytest lifecycle | PASS (5) |
| Probe LIST_OK davi/teo/vista | PASS |
| Probe reacquire FP change | PASS |
| Probe LIST after reacquire | PASS |
| Battery catalog preflight | 24/24 `auth_valid` + MCP catalog available |

## 6. Frozen evaluation surface

```text
INSTRUCTION_VERSION=generalist-semantic-v2
INSTRUCTION_FINGERPRINT=7dbc94c5035b0f19
MODEL=qwen/qwen3-14b
PROFILE=openrouter_qwen
RUBRIC=delia-api/scripts/int1_v2_stability_rubric.json (Documento 297)
SCENARIOS=8 × REPETITIONS=3 → PLANNED_RUNS=24
```

Questions P1/P2/P3/G1/H1–H4 unchanged. Scorer remains a **proposal** (`NOT_FINAL_requires_human_review`).

## 7. Battery validity

| Metric | Value |
|---:|
| PLANNED_RUNS | 24 |
| EXECUTED_RUNS | 24 |
| VALID_ENV_RUNS | **24** |
| ENV_INVALID_RUNS | **0** |
| Unique auth fingerprints | 24 |
| Wall elapsed (sum scenario) | 914.3 s (< 5400) |
| Tool calls (sum) | 68 |
| LLM request count (sum recorded) | 23 |
| Token usage / cost | UNAVAILABLE (provider meter null; not presumed zero) |

**STABILITY_EVAL_COMPLETE** for environmental validity. This does **not** auto-accept INT-1.

## 8. Objective matrix (all 24 valid-env)

| Scenario | SAT | PARTIAL | NOT_SAT | INCONCLUSIVE | First-tool distribution | Causal (scorer proposal) |
|---|---:|---:|---:|---:|---|---|
| P1 | 0 | 2 | 1 | 0 | `davi:read`×1, `davi:get_context`×2 | OWNER_CONTRACT×2; INT1_SELECTION×1 |
| P2 | 0 | 3 | 0 | 0 | `teo:read`×3 | INT1_INVESTIGATION_CONTINUITY×3 |
| P3 | 0 | 1 | 2 | 0 | `vista:read`×1, `teo:analyze`×1, `vista:get_context`×1 | INT1_SELECTION×2; EVIDENCE_COVERAGE×1 |
| G1 | 0 | 1 | 2 | 0 | `teo:read`×3 | INT1_SELECTION×2; OWNER_CONTRACT×1 |
| H1 | 3 | 0 | 0 | 0 | `davi:read`×1, `davi:get_context`×1, `teo:read`×1 | UNDETERMINED×3 (objective met) |
| H2 | 3 | 0 | 0 | 0 | `davi:get_context`×3 | UNDETERMINED×3 |
| H3 | 0 | 2 | 0 | 1 | `vista:read`×3 | UNDETERMINED×3 |
| H4 | 0 | 3 | 0 | 0 | `teo:analyze`×3 | UNDETERMINED×3 |

Overall (24): SATISFIED **6** · PARTIAL **12** · NOT_SATISFIED **5** · INCONCLUSIVE **1**.  
`GROUNDING_WITHOUT_OBJECTIVE_SATISFACTION`: **2** (P1 r2 description≠structure; P3 r1 dashboard metrics as “formats”).  
TOOL_SELECTION: SUITABLE 19 · PARTIALLY_SUITABLE 2 · UNSUITABLE 3.  
ARGUMENT_VALIDITY: VALID 24 (no invalid-arg class in this pass).

### Per-run first tools (selection variability)

| Scenario | r1 | r2 | r3 |
|---|---|---|---|
| P1 | davi:read | davi:get_context | davi:get_context |
| P2 | teo:read | teo:read | teo:read |
| P3 | vista:read | **teo:analyze** | vista:get_context |
| G1 | **teo:read** | **teo:read** | teo:read |
| H1 | davi:read | davi:get_context | teo:read |
| H2 | davi:get_context | davi:get_context | davi:get_context |
| H3 | vista:read | vista:read | vista:read |
| H4 | teo:analyze | teo:analyze | teo:analyze |

## 9. Ownership attribution (valid battery)

| Signal | Evidence | Class | Owner / next |
|---|---|---|---|
| Prior 17 ENV_INVALID | doc 297 | EVAL_ENVIRONMENT (closed by this remediation) | harness — **remediated** |
| G1 first tool TEO (2–3/3) | never DAVI structure path on r1/r2; NON_GROUNDED×2 | INT1_SELECTION | bounded INT-1 selection/recovery candidate |
| P3 teo:analyze once | dashboard metrics framed as formats; also vista paths unstable | INT1_SELECTION (+ coverage gap once) | INT-1 selection; INT-3 **not** auto-required |
| P2 always teo:read PARTIAL | truncation / no page continue | INT1_INVESTIGATION_CONTINUITY | EXTEND existing continuity if authorized |
| P1 DAVI-start but description≠structure (r2) | GROUNDED w/o objective | INT1_SELECTION / owner completeness mix | INT-1 + owner contract review |
| H4 consistent teo:analyze PARTIAL | dashboard summary retrieved; objective depth incomplete | UNDETERMINED / objective representation residual | may touch INT-2 later — **NOT_PROVEN_REQUIRED** to implement now |
| H1/H2 stable SATISFIED | honest empty on H2 | — | positive control |
| OBJECTIVE_REPRESENTATION_GAP | H4/P3 partial framing | **NOT_PROVEN_REQUIRED** as mandatory INT-2 now | architecture decision only if coordination wants typed obligations |
| COVERAGE_ASSESSMENT_GAP | P3 r1 Gwo | observed once | inventory before INT-3 |

## 10. Recommended next step

```text
RECOMMENDED_NEXT_OWNER=COORDINATION
RECOMMENDED_BOUNDED_NEXT_STEP=INT1_BOUNDED_REWORK_CANDIDATE
  (selection/recovery/continuity on G1/P3/P2 after this valid multi-rep sample;
   reuse existing orchestrator mechanisms — no new Agent)
OBJECTIVE_REPRESENTATION_GAP=NOT_PROVEN_REQUIRED
INT3_IMPLEMENTATION=NOT_AUTHORIZED / NOT_AUTO_JUSTIFIED
EVAL_ENVIRONMENT_REWORK=COMPLETE_FOR_SUBJECT_TOKEN_LIFETIME (credential isolation residual remains)
ARCHITECTURE_DECISIONS_REQUIRED=none forced by this battery; optional INT-2/INT-3 only after coordination
```

Do **not** promote instruction candidates. Do **not** treat PARTIAL majority as stage acceptance.

## 11. Limits

- n=3 descriptive only — no statistical significance.  
- Offline scorer is heuristic; independent human review remains authority.  
- Credential isolation residual unchanged.  
- Provider token/cost meters UNAVAILABLE.  
- Image digest may differ from host-mounted evaluated SHA; both recorded.

## 12. Status

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2_IMPLEMENTATION_AUTHORIZED=NO
INT3_IMPLEMENTATION_AUTHORIZED=NO
T3_AUTHORIZED=NO
PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_VALID_STABILITY_INDEPENDENT_REVIEW
```
