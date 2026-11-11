# 302 — INT-1 Minimal Real Intent Understanding vs MCP Tool Selection Causal Evaluation

**TASK_ID:** `DELIA-C3-T2-INT1-INTENT-VS-TOOL-SELECTION-MINIMAL-REAL-QWEN-EVAL-01`  
**Data:** 2026-11-11  
**Tipo:** minimal real eval attempt — **LIVE BLOCKED by security/credential gate**  
**REFERENCE_HEAD:** `9608b1d4f7` (ancestral)  
**EVALUATED_SHA (freeze):** `a4af0939110f83fd6b4ca29f95253d82e9e9dab7`  
**FUNCTIONAL_CODE_CHANGED:** NO  
**INSTRUCTION_CHANGED:** NO  
**EXTERNAL_LLM / MODEL_REQUESTS:** **0**  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  

---

## 1. PO scope vs security authority

PO authorized **exactly two** scenarios (G1 + P1), 1 rep each, no functional rework.

PO authorization **does not** replace credential-owner approval for shared infra secrets.

Residual from docs 294–301 remains:

```text
EVALUATION_CREDENTIAL_SCOPE=NONE_PROVEN_SEPARATE_FROM_PROD
```

Task rule: without legitimate credential-scope approval → **do not call external LLM**.

---

## 2. Security gate (host session)

Artifact: `delia-api/.battery/int1-minimal-intent-vs-selection/security-gate.json` (local/gitignored).

| Check | Result |
|---|---|
| SECURE_EVAL_GATE | **BLOCKED** |
| DELIA_EVAL_EGRESS_AUTHORIZED | false / absent |
| CURRENT_LLM_HOST_CLASS | empty |
| CONFIGURED_MODEL (Settings default) | `qwen3:8b` ≠ `qwen/qwen3-14b` |
| MODEL_EGRESS_AUTHORIZED | NOT_PROVEN |
| CREDENTIAL_ISOLATION | NOT_PROVEN |
| MCP_READ_AUTHORIZED | NOT_PROVEN |
| NETWORK_ACCESS_AUTHORIZED | NOT_PROVEN |
| POLICY_EXTERNAL_LLM_NONPROD | REFUSED |
| PRODUCTION_UNTOUCHED | NOT_OBSERVED_THIS_SCRIPT (no eval container started) |

**LIVE_EVAL=BLOCKED.** No OpenRouter calls. No MCP subject token acquire for this task.

---

## 3. Freeze (config intended — not live-applied)

From checked-in `pydantic_ai.runtime.delpi.json` profile `openrouter_qwen` + instructions resource:

| Field | Value |
|---|---|
| MODEL_ID (target) | `qwen/qwen3-14b` |
| MODEL_PROFILE | `openrouter_qwen` |
| INSTRUCTION_VERSION | `generalist-semantic-v2` |
| INSTRUCTION_FINGERPRINT | `7dbc94c5035b0f19` (resource match) |
| CONTEXT_WINDOW (profile) | 40960 |
| REQUEST_LIMIT | 12 |
| TOOL_CALL_LIMIT | 8 |
| MAX_TOTAL_MODEL_REQUESTS ceiling | 24 |
| MAX_TOTAL_TOOL_CALLS ceiling | 16 |
| IMAGE_DIGEST | NOT_STARTED_EVAL_CONTAINER |
| MODEL_CONFIG_FINGERPRINT | UNAVAILABLE (live not run) |
| TOOLSET_FINGERPRINT | UNAVAILABLE (live not run) |
| PYDANTIC_AI_VERSION | 2.50.0 expected from prior evals; not re-proven this session |

Authorized questions (not executed):

1. G1 — `Mostre a árvore de componentes e relações do item 90260921.`
2. P1 — `Qual é a estrutura do produto 90260921.`

---

## 4. Intent observability (code/prior traces — not this live)

From Documento 301 + harness units (no new live):

| Item | Status |
|---|---|
| `declare_investigation_goal` optional | YES |
| Usage in prior 55 traces | 0 |
| This live capture | **NOT_RUN** |
| GOAL_DECLARATION_G1/P1 | **NOT_OBSERVED** (eval blocked) |

No prompt change to force declaration.

---

## 5. Scenario results

| Scenario | Executed | First tool | Objective |
|---|---|---|---|
| G1 | **NO** | UNAVAILABLE | UNAVAILABLE |
| P1 | **NO** | UNAVAILABLE | UNAVAILABLE |

```text
EXECUTED_SCENARIOS=0
MODEL_REQUESTS=0
TOOL_CALLS=0
TOKEN_USAGE=UNAVAILABLE
COST=0
LATENCY=UNAVAILABLE
```

Comparative matrix G1 vs P1: **NOT_POPULATED** (no live observations this task).

Causal conclusion for *this* task:

```text
FIRST_MATERIAL_DIVERGENCE=SECURITY_GATE_BLOCK
CAUSAL_CONCLUSION=LIVE_NOT_EXECUTED_CREDENTIAL_AND_EGRESS_GATES
```

Historical causal hypotheses from docs 298–301 (G1 TEO-first / owner ambiguity) remain **prior evidence**, not re-proven here.

---

## 6. Targeted tests (engineering only)

```text
tests/test_int1_secure_decision_trace.py
tests/test_int1_intent_goal_projection_signals.py
tests/test_pydantic_ai_runtime_config.py::test_profile_selector_resolves_named_profile
→ PASS
```

No full suite. No instruction/Agent change.

---

## 7. Unblocking requirements (for a future authorized rerun)

1. Credential-owner approval for eval identity/scope **separate from** or explicitly accepted residual vs prod LLM key.
2. `DELIA_EVAL_EGRESS_AUTHORIZED=1` on isolated eval path with `llm_base_url` host `openrouter.ai`.
3. Profile `openrouter_qwen` / model `qwen/qwen3-14b` active in eval container Settings.
4. MCP subject auth lifetime harness (doc 298) + READ authorization for DAVI/TEO/VISTA.
5. Isolated eval container; prove `PRODUCTION_UNTOUCHED`.
6. Then execute **only** G1 + P1 (1 rep), capture declare_goal / first tool / args / recovery / objective.

---

## 8. Recommendation

| Item | Recommendation |
|---|---|
| Bounded correction code | **NONE in this task** (eval blocked; functional rework NOT_AUTHORIZED) |
| Owner TEO | Still recommended from docs 300–301: clarify `decomposition_tree` ≠ product BOM |
| Next eval | Re-authorize after credential/egress gates READY; same two questions only |
| INT-1 stage | Remains **BLOCKED** |

**NEXT:** `COORDINATION_INT1_MINIMAL_REAL_INTENT_EVAL_REVIEW`
