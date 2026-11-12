# 307 — INT-1 Provider Request Integrity and Real Qwen Semantic Tool Selection Causal Evaluation

**TASK_ID:** `DELIA-C3-T2-INT1-PYDANTIC-AI-PROVIDER-WIRE-AND-REAL-SEMANTIC-SELECTION-REMEDIATION-01`  
**Data:** 2026-11-12  
**EXTERNAL_LLM:** AUTHORIZED — EXECUTED (G1+P1+M1 ×2 rounds ≤6)  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**FULL_BATTERY:** NOT_RUN  
**NEW_AGENT / ROUTER / PLANNER:** NO  
**INSTRUCTION_CHANGED:** NO  

---

## 1. Reanchor

| Item | Value |
|---|---|
| REFERENCE_HEAD (task) | `485077b9d2…` |
| EVALUATED / work HEAD | `183097786b…` (ff `origin/main` during task) |
| Instruction | `generalist-semantic-v2` / fp `7dbc94c5035b0f19` MATCH |
| Model / profile | `qwen/qwen3-14b` / `openrouter_qwen` |
| Pydantic AI | `2.50.0` |
| Isolation | `delpi-delia-eval-int1-or-qwen14b`; `PROD_CONTAINER_UNTOUCHED=YES` |

Prior evidence reused: `or-qwen14b-198e127edee9` (303), `or-qwen14b-3863d58c5327` (305), doc 306 offline.

---

## 2. Composition inventory

```text
Owner MCP tools/list
→ MCPToolset.filtered → RenamedToolset → _EnvelopeHintedToolset
→ CombinedToolset([FunctionToolset, *mcp])
→ Agent(instructions=v2)
→ Model.prepare_request → ModelRequestParameters.declared_function_tools  (=B3)
→ OpenAI-compatible HTTP (NOT_OBSERVED)
→ Qwen 14B native tool selection
```

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

Reuse: `WrapperModel`, `FunctionModel`/`AgentInfo`, `ModelRequestParameters`, harness `int1_openrouter_qwen14b_instrumented_eval`.

---

## 3. B1 / B2 / B3

| Boundary | Status |
|---|---|
| B1 owner tools/list | PROVEN (live + stub) |
| B2 rename + EnvelopeHint | PROVEN after remediation |
| B3 provider request pre-HTTP | PROVEN via `WrapperModel.request` MRP / FunctionModel |
| HTTP wire bytes | **NOT_OBSERVED** |

Live B3 (post-fix round `or-qwen14b-118289112bdf`):

| Tool | len | Integrity |
|---|---|---|
| `teo.read` | 2225 | WBS + bill-of-materials + Object-typed hint |
| `davi.read` | 918 | `get_product_structure` + arguments-object hint |
| tool_choice | UNFORCED | no forced router |
| tool_order | davi before teo | identical across G1/P1/M1 |

G1/P1/M1 differ only in `user_prompt` at B3 (tool+instruction fingerprints equal when prompt zeroed).

---

## 4. Deterministic defects remediated

### D1 — EnvelopeHint dropped before B3

**Cause:** duck-typed `_EnvelopeHintedToolset` forwarded `for_run`/`for_run_step` to the inner MCP leaf; `WrapperToolset.replace` discarded the hint layer.

**Fix:** subclass `pydantic_ai.toolsets.WrapperToolset`.

### D2 — Live schemas silent for hints

**Cause:** owner schemas publish nullable objects as `anyOf: [{type:object},{type:null}]`; naive `prop["type"]=="object"` missed them.

**Fix:** `_schema_declares_object` recognizes `anyOf`/`oneOf`.

**Tests:** `test_int1_provider_request_boundary_integrity.py`, `test_envelope_hint_recognizes_nullable_object_anyof_live_schema`, adjacent description/pagination tests — PASS.

These fixes restore schema-derived argument guidance. They do **not** force owner selection.

---

## 5. Real Qwen evaluations

### Round 1 — `or-qwen14b-303e1f9f4ed3` (pre anyOf-hint on live B3)

| | G1 | P1 | M1 |
|---|---|---|---|
| First tool | `teo.read` decomposition_tree get | `davi.get_context` catalog | `davi.get_context` catalog |
| Recovery | → DAVI `get_product_structure` | direct BOM | drifted (TEO + invalid caps) |
| Objective | SATISFIED (GROUNDED) | SATISFIED | NOT_SATISFIED |

### Round 2 — `or-qwen14b-118289112bdf` (EnvelopeHint live at B3)

| | G1 | P1 | M1 |
|---|---|---|---|
| First tool | `teo.read` process get | `davi.get_context` catalog | `teo.read` process get |
| Recovery | → DAVI BOM SUCCESS | direct BOM | VISTA/guide detours FAIL |
| Objective | SATISFIED | SATISFIED | NOT_SATISFIED |

`declare_investigation_goal`: visible, unused in all six runs.

---

## 6. Hypothesis matrix

| H | Claim | Result |
|---|---|---|
| H1 information delivery (owner WBS/BOM) | lost before model | **REJECTED** (B3 intact both rounds) |
| H1b EnvelopeHint delivery | hint layer missing | **PROVEN → REMEDIATED** |
| H2 objective representation gap | declare unused / no parallel object channel | **PRESENT**, not proven causal |
| H3 model selection error | incompatible first tool despite intact surface | **PROVEN_IN_SAMPLE** (G1 both rounds) |
| H4 contract semantic competition | TEO tree/WBS wording attracts | **INCONCLUSIVE** (correlated; not isolated) |
| H5 application routing | forced tool_choice | **REJECTED** (UNFORCED) |
| H6 recovery failure | continuity fails after bad first tool | **G1 recovery OK**; **M1 PROVEN_IN_SAMPLE fail** (both rounds diverge after first tool) |

`WORDING_SENSITIVITY`: round1 M1 DAVI-first vs G1 TEO-first → **PROVEN_IN_SAMPLE**; round2 M1 TEO-first → not stable across n=2 → **do not treat as fixed lexical rule**.

---

## 7. Causal conclusion

```text
FIRST_MATERIAL_DIVERGENCE = native first MCP owner choice under identical B3 tool surface
CAUSAL_CONCLUSION = MODEL_TOOL_SELECTION_ERROR (PROVEN_IN_SAMPLE) for G1
                    + EnvelopeHint delivery defects REMEDIATED (not selection cure)
INFORMATION_DELIVERY_FAILURE (owner contracts) = REJECTED
APPLICATION_ROUTING_ERROR = REJECTED
```

Internal Qwen rationale remains **NOT_OBSERVABLE** (no CoT).

No Case-C instruction rewrite, keyword router, forced declare, or second Agent (not authorized).

---

## 8. Stage / next

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2/INT3/T3=NOT_AUTHORIZED
PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_REAL_SEMANTIC_SELECTION_INDEPENDENT_REVIEW
```

Recommended bounded next step (coordination): decide whether to authorize a **provider-neutral** instruction/policy evolution for semantic object matching — still without keyword owner routing — after independent review of this evidence.
