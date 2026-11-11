# 303 — INT-1 Minimal Real Intent Understanding vs MCP Tool Selection (G1/P1)

**TASK_ID:** `DELIA-C3-T2-INT1-G1-P1-REAL-QWEN-INTENT-SELECTION-EVAL-02`  
**Data:** 2026-11-11  
**Tipo:** live eval mínima (2 cenários) — diagnóstico; sem rework do Agent  
**REFERENCE_HEAD:** `3d1a44518972ffc0fcdae840fa83c86988488941`  
**EVALUATION_ID:** `or-qwen14b-198e127edee9`  
**FUNCTIONAL_AGENT_CHANGED:** NO  
**INSTRUCTION_CHANGED:** NO  
**HARNESS_EXTEND:** `DELIA_EVAL_SCENARIO_IDS` filter (G1+P1 only)  
**PRODUCTION_UNTOUCHED:** YES  

Supersede o Documento 302 no ponto “live blocked by host Settings”: esta execução usou o **container isolado** OpenRouter existente.

---

## 1. Runtime freeze

| Campo | Valor |
|---|---|
| EVALUATED_SHA | `3d1a44518972ffc0fcdae840fa83c86988488941` (host mount `/app`) |
| MODEL_ID | `qwen/qwen3-14b` |
| MODEL_PROFILE | `openrouter_qwen` |
| MODEL_CONFIG_FINGERPRINT | `e4a5b706a3b3156b` |
| INSTRUCTION_VERSION | `generalist-semantic-v2` |
| INSTRUCTION_FINGERPRINT | `7dbc94c5035b0f19` |
| TOOLSET_FINGERPRINT | `82c1bb2d9b2d9d38` (sha256[:16] of visible tool names) |
| CONTEXT_WINDOW | 40960 |
| PYDANTIC_AI | 2.50.0 |
| EGRESS | `https://openrouter.ai/api/v1` + `DELIA_EVAL_EGRESS_AUTHORIZED=1` |
| SECURE_EVAL_GATE | READY_FOR_ISOLATED_EVAL |
| EVAL_CONTAINER | `delpi-delia-eval-int1-or-qwen14b` (process-separated) |
| SCENARIO_FILTER | `G1_semantic_reword_structure,P1_product_structure_control` |

Local artifacts (gitignored):  
`delia-api/.battery/int1-g1-p1-real-eval-02/` + traces `…/int1-secure-decision-trace/or-qwen14b-198e127edee9/`.

---

## 2. Tool surface (identical both runs)

```text
davi.get_context, davi.knowledge, davi.read, davi.analyze,
teo.analyze, teo.get_context, teo.read, teo.knowledge,
vista.get_context, vista.read, vista.analyze, vista.knowledge
```

Both TEO `read` and DAVI `read`/`get_product_structure` path were model-visible.

---

## 3. G1 — árvore de componentes / item 90260921

| Dimensão | Observado |
|---|---|
| GOAL_DECLARATION | **NOT_OBSERVED** (0 mentions) |
| INTENT_OBSERVABILITY | IMPLICIT_ONLY / NOT_OBSERVED explícito |
| FIRST_MCP | `teo.read` `entity=decomposition_tree` `action=get` `params.id=90260921` |
| OWNER_RESULT (1º) | TEO `success:false` internal error |
| Progress after miss | `SOURCE_UNAVAILABLE` + `uncovered_user_identifiers=["90260921"]` + coverage_note |
| RECOVERY | **SUCCESS**: `davi.get_context` → `davi.read` `capability=get_product_structure` `arguments.code=90260921` |
| ROOT | `90260921` |
| GROUNDING | GROUNDED |
| OBJECTIVE | **PARTIAL** (BOM level-1; `owner_result_incomplete` / unmet subcomponent detail) |

**First material divergence:** `TOOL_SELECTION_ERROR` (+ `TOOL_CONTRACT_AMBIGUITY` TEO) on first MCP call — **not** absence of DAVI capability.

**Recovery:** Agent did recognize insufficiency (open identifier + failed TEO) and switched to DAVI structure — **PROVEN_IN_SAMPLE** this run.

---

## 4. P1 — estrutura do produto 90260921 (controle)

| Dimensão | Observado |
|---|---|
| GOAL_DECLARATION | **NOT_OBSERVED** |
| FIRST_MCP | `davi.get_context` `action=catalog` |
| NEXT | `davi.read` `get_product_structure` `code=90260921` |
| TEO used | NO |
| GROUNDING | GROUNDED |
| OBJECTIVE | **PARTIAL** (same owner incompleteness class) |
| RECOVERY | NOT_REQUIRED |

---

## 5. Comparative matrix

| Dimensão | G1 | P1 |
|---|---|---|
| Interpretação explícita | NOT_OBSERVED | NOT_OBSERVED |
| Tools disponíveis | 12 (iguais) | 12 (iguais) |
| Primeira ferramenta | **teo.read / decomposition_tree** | **davi.get_context** |
| Argumentos iniciais | process-WBS entity + product id | catalog discovery |
| Resultado 1º owner | TEO error | DAVI discovery |
| Recuperação | DAVI BOM | n/a |
| Evidência BOM | YES (após recovery) | YES |
| Satisfação | PARTIAL | PARTIAL |

### Pergunta central

**Compreensão explícita do objetivo não foi observada** (sem `declare_investigation_goal`).

Comportamento externo: em G1 a **seleção inicial foi inadequada** (TEO decomposition) **apesar** da superfície correta; a **recuperação investigativa funcionou** nesta amostra e alcançou BOM DAVI. Em P1 a seleção inicial já foi adequada. Não generalizar estabilidade a partir de n=1.

---

## 6. Classification

| | G1 | P1 |
|---|---|---|
| INTENT_OBSERVABILITY | NOT_OBSERVED | NOT_OBSERVED |
| TOOL_SELECTION (first) | UNSUITABLE | SUITABLE |
| ARGUMENT_VALIDITY (first) | VALID schema / wrong business object | VALID |
| RECOVERY | SUCCESS | NOT_REQUIRED |
| OBJECTIVE | PARTIAL | PARTIAL |

**CAUSAL_CONCLUSION (PROVEN_IN_SAMPLE):**  
G1 first divergence = tool selection under TEO contract attractor (`decomposition_tree`), not missing MCP tools and not proven “intent misunderstood”. Recovery to DAVI BOM succeeded this run. P1 control selected DAVI first. Objective partiality is largely `owner_result_incomplete` / depth coverage — shared with P1.

**UNPROVEN:** statistical stability of recovery; whether forcing declare_goal would change first-tool distribution.

---

## 7. Usage

| Metric | Value |
|---|---|
| EXECUTED_SCENARIOS | 2 |
| MODEL_REQUESTS (metered runs) | 2 |
| TOOL_CALLS (MCP invokes) | 5 (G1:3 + P1:2) |
| TOKEN_USAGE | UNAVAILABLE (provider meter 0 in capture) |
| LATENCY | G1 ~31.6s; P1 ~19.3s; LLM meter ~47.5s total |
| COST | UNAVAILABLE |

---

## 8. Harness notes / tests

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND  # DELIA_EVAL_SCENARIO_IDS filter only
```

Targeted tests: `test_int1_secure_decision_trace.py`, `test_int1_openrouter_scenario_filter.py` PASS.

No Agent/instruction/owner contract change during the experiment.

---

## 9. Recommended bounded next fix (NOT implemented here)

1. **Owner TEO:** clarificar na descrição publicada que `decomposition_tree` é WBS de **processo**, não estrutura/BOM de produto (docs 300–301).  
2. **Optional later INT-1:** avaliar se sinais de recovery pós-TEO-miss precisam de reforço não acoplado a specialist names — só após decisão de coordenação.  
3. **Não** hardcodar `if product → DAVI`.

---

## 10. Stage

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2/INT3/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_G1_P1_REAL_EVAL_REVIEW
```
