# 306 — INT-1 G1 First-Tool Semantic Selection: Model-Visible Context and Objective Representation Causal Investigation

**TASK_ID:** `DELIA-C3-T2-INT1-G1-FIRST-TOOL-SEMANTIC-SELECTION-ROOT-CAUSE-INVESTIGATION-01`  
**Data:** 2026-11-12  
**REFERENCE_HEAD:** `d9c63b66ad09c8d17935490c78b724fe89bee415`  
**EXTERNAL_LLM_CALLS:** 0  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**AGENT_CHANGED:** NO  
**INSTRUCTION_CHANGED:** NO  

---

## 1. Evidence pair

| | BEFORE (doc 303) | AFTER (doc 305) |
|---|---|---|
| EVAL_ID | `or-qwen14b-198e127edee9` | `or-qwen14b-3863d58c5327` |
| SHA (runtime) | `3d1a445189…` (eval) | `e2b341d877…` (owners+eval) |
| config_fp | `e4a5b706a3b3156b` | `e4a5b706a3b3156b` |
| instruction | `generalist-semantic-v2` / fp `7dbc94c5035b0f19` | same |
| Toolset names | 12 MCP (fp `82c1bb2d9b2d9d38`) | **identical** |
| TEO desc WBS in capture | **False** (pré-304; capture also `[:500]`) | **True** (WBS + bill-of-materials in prefix) |
| G1 first tool | `teo.read` `decomposition_tree` get | `teo.read` `process` search → then `decomposition_tree` |
| P1 first tool | `davi.get_context` | `davi.get_context` |
| G1 recovery | DAVI BOM SUCCESS | DAVI BOM SUCCESS |
| owner_result_incomplete | True (false incomplete) | **False** |
| Objective | PARTIAL | SATISFIED (residual coverage_unknown) |

---

## 2. Model-visible pipeline (PROVEN)

```text
Owner tools/list
→ catalog projection (_project_semantic_tool_catalog)
→ MCPToolset.filtered → RenamedToolset → _EnvelopeHintedToolset (append-only)
→ CombinedToolset([FunctionToolset, *mcp])
→ Agent(instructions=v2)
→ native provider tool call
```

- EnvelopeHint **does not** truncate owner descriptions (doc 299).
- Catalog DTO **does not** slice descriptions.
- Trace harness previously sliced `description[:500]` **and** sanitizer capped strings at 500 — observability defect only; Agent path still had full owner text + WBS after doc 304.
- No deterministic first-tool router (`tool_choice` / ForcedTool absent).
- Catalog/toolset order lists **davi before teo** — cannot explain TEO-first bias by presentation order alone.

---

## 3. Goal representation

| Item | Status |
|---|---|
| `declare_investigation_goal` model-visible | YES (FunctionToolset) |
| Instructions v2 | OPTIONAL; skip for simple single READ |
| Used in 198e / 3863 G1+P1 | **0/4** NOT_OBSERVED |
| Gates MCP selection? | **NO** — only sets plan for coverage/finalize |
| Observable objective to model | User question text + instructions + tool contracts (no prior business context) |

Linguistic difference G1 (“árvore de componentes e relações do **item**”) vs P1 (“estrutura do **produto**”) is **correlated** with first-tool divergence. Internal lexical association is **NOT_OBSERVABLE** (no CoT).

---

## 4. Hypothesis matrix

| H | Claim | Result | Evidence |
|---|---|---|---|
| H1 | Information loss before model (WBS missing) | **REJECTED** for post-fix sample | 3863 capture has WBS+BOM-neg; EnvelopeHint preserves; owner publishes |
| H2 | Objective mal-represented | **OBJECTIVE_REPRESENTATION_GAP** (not proven causal) | declare unused; optional by design; no parallel “business object” channel |
| H3 | Model selects incompatible tool despite intact surface | **PROVEN_IN_SAMPLE** | Same toolset/fp; WBS present; G1 still TEO-first then recovery |
| H4 | Application forces first tool | **REJECTED** | Native tool calling; no forced router |
| H5 | Evidence insufficient for wire payload | **PARTIAL** | Provider `tools[]` raw request TO_INVENTORY; catalog capture ≠ EnvelopeHinted get_tools (documented) |

### First material divergence

```text
G1 vs P1 first MCP owner choice under identical tool surface
```

### Causal root cause (this investigation)

```text
MODEL_TOOL_SELECTION_ERROR=PROVEN_IN_SAMPLE
INFORMATION_DELIVERY_FAILURE=REJECTED (post-304)
APPLICATION_ROUTING_ERROR=REJECTED
OBJECTIVE_REPRESENTATION_GAP=PRESENT (declare unused; not proven necessary)
```

Internal “why Qwen mapped G1 wording to TEO” remains **NOT_OBSERVABLE**.

---

## 5. Deterministic corrections (observability only)

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
```

1. `int1_secure_decision_trace.sanitize_mapping` — `description` keys keep up to 4000 chars.
2. `_catalog_snapshot` — stop hard `[:500]`; emit `description_len` + WBS/BOM markers + `capture_boundary`.
3. Tests: `test_int1_g1_model_visible_surface_integrity.py` PASS.

No Agent/instruction/owner rewrite. No keyword routing.

---

## 6. Recommended minimal next step

PO-authorize **one** bounded live probe (optional A/B) only if coordination wants more than n=1 on selection:

- Same SHA/tool surface; G1 only × N small; **or**
- Compare wording metamorphic siblings without instruction change.

Do **not** force `declare_investigation_goal`, hardcode DAVI, or rewrite instructions before that decision.

---

## 7. Stage

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
NEXT=COORDINATION_INT1_G1_SELECTION_CAUSAL_REVIEW
```
