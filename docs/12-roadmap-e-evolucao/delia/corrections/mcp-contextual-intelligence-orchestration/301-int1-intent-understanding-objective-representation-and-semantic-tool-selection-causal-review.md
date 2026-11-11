# 301 — INT-1 Intent Understanding, Objective Representation and Semantic Tool Selection Causal Review

**TASK_ID:** `DELIA-C3-T2-INT1-INTENT-UNDERSTANDING-AND-TOOL-SELECTION-CAUSAL-REVIEW-01`  
**Data:** 2026-11-11  
**Tipo:** causal review + minimal EXTEND (no external LLM)  
**REFERENCE_HEAD:** `c04228eec2` (ancestral de `origin/main`)  
**BASE/FINAL:** ver ledger no commit desta task  
**EXTERNAL_LLM_CALLS:** 0  
**FULL_BATTERY:** NOT_RUN  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  

---

## 1. Abstraction Gate

| Campo | Valor |
|---|---|
| RESPONSIBILITY | observação/propagação de intenção e sinais de recuperação no path investigativo |
| OWNER | `PydanticAiInvestigationOrchestrator` + gates plan accept |
| CANONICAL_SOURCE | `declare_investigation_goal` / `SemanticInvestigationPlan` / `_attempt_projection` / MCPToolset |
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | EXTEND (`_attempt_projection`, echo de `business_subject`) |
| NEW_AGENT / ROUTER / PLANNER | NO |

---

## 2. Inventário do fluxo (observável)

| Componente | Responsabilidade | Objetivo explícito? |
|---|---|---|
| User prompt + instructions v2 | orientação textual; “understand objective before tools” | implícito no modelo |
| `declare_investigation_goal` | declaração opcional tipada (`goal_class`, targets, `evidence_needed`, `business_subject`) | **sim, se chamado** |
| `_accept_semantic_investigation_plan` | valida classe; monta `SemanticInvestigationPlan` | persistido em `InvestigationDeps.investigation_plan` |
| MCPToolset / Renamed / Combined / EnvelopeHint | superfície de tools owner | contratos, não intenção |
| `_attempt_projection` + `classify_investigation_progress` | sinais de progresso / cobertura | usa plan se existir |
| `InvestigationAnswer` + finalize | resposta estruturada + grounding | obligations só se plan/`evidence_needed` |

**Achados de inventário:**

- O objetivo **não** é representado estruturalmente a menos que o Agent chame `declare_investigation_goal`.
- A declaração é **opcional** (docstring: not required for simple READ).
- Nos corpora `ctx-rec-1bc5578991` (30 traces) e `stab-v2-5b0e914eb9` (25 traces): **`declare_investigation_goal` aparece em 0 arquivos** → `GOAL_DECLARATION_USAGE_OBSERVED=NO` (PROVEN_IN_SAMPLE).
- Sem plan, `classify_investigation_progress` não aplica obligations tipadas; RELATED só via discovery / uncovered-without-root em SUCCESS business evidence.
- INT-2 obligations tipadas de evidência-por-kind permanecem dependência documentada — **não implementadas**.

---

## 3. Matriz causal (traces persistidos)

Fontes: docs 294–300 + `delia-api/.battery/int1-secure-decision-trace/{ctx-rec-1bc5578991,stab-v2-5b0e914eb9}/`.

### G1 — “árvore de componentes … 90260921”

| Etapa | Evidência | Resultado | Classificação |
|---|---|---|---|
| Intenção | pergunta de produto/BOM; sem declare_goal | interpretação **não observável** estruturalmente | INTENT_REPRESENTATION_GAP (PROVEN) |
| Objeto empresarial | args `entity=decomposition_tree` ou `process` + `id=90260921` | tratado como processo/WBS TEO | TOOL_SELECTION_ERROR + TOOL_CONTRACT_AMBIGUITY (PROVEN_IN_SAMPLE) |
| Evidência necessária | BOM/product structure | não declarada tipada | EVIDENCE_REQUIREMENT_GAP (PROVEN — sem plan) |
| Contratos | TEO lista `decomposition_tree`; DAVI `get_product_structure` na superfície | ambos visíveis | TOOL_CONTRACT_AMBIGUITY owner TEO (PROVEN) |
| Seleção inicial | first MCP = `teo.read` (r1/r2 stab/ctx); r3 ctx recupera DAVI | first divergence vs P1 | TOOL_SELECTION_ERROR (PROVEN_IN_SAMPLE) |
| Resultado | “Processo não encontrado” / erro interno | não é BOM | OWNER_RESULT_INCOMPLETE / wrong-domain (PROVEN) |
| Recuperação | chase TEO/VISTA com mesmo id; às vezes DAVI (r3) | inconsistente | INVESTIGATION_RECOVERY_FAILURE (PROVEN_IN_SAMPLE) |
| Finalização | NON_GROUNDED (falhas) ou GROUNDED parcial (r3) | — | FINALIZATION_COVERAGE_GAP residual |

**Primeira divergência material G1:** `TOOL_SELECTION_ERROR` na primeira chamada MCP (`teo.read` com entity de processo/decomposição), alimentada por `TOOL_CONTRACT_AMBIGUITY` do owner TEO — **não** prova de “Qwen não compreendeu a intenção” (intenção não instrumentada).

### P1 — controle “estrutura do produto”

| Etapa | Evidência | Resultado |
|---|---|---|
| Seleção | `davi.get_context` → `davi.read` `get_product_structure` `code=90260921` | path adequado (PROVEN) |
| Primeira divergência | (controle) | — |

Mesmo toolset/modelo que G1 → falha G1 **não** é ausência de capability.

### P3 — formatos de visualização

| Etapa | Evidência (ctx-rec r1) | Classificação |
|---|---|---|
| Seleção | `vista.read` first (doc 299 melhoria vs teo.analyze) | TOOL_SELECTION adequado parcial |
| Recuperação | knowledge follow-up; alguns SOURCE_UNAVAILABLE | PARTIAL / INCONCLUSIVE para “formatos” vs métricas |
| First divergence histórica (doc 294) | vista.read 422 vs analyze esperado | TOOL_SELECTION / ARGUMENT_BINDING (histórico) |

### P2 — registros de processos

| Etapa | Evidência | Classificação |
|---|---|---|
| Seleção | `teo.read` | adequado ao domínio |
| Continuidade | paginação (doc 299) | CONTINUITY residual PARTIAL |

---

## 4. Contratos MCP (G1)

| Capability | BUSINESS_OBJECT | APPLICABILITY | Distinção suficiente? |
|---|---|---|---|
| TEO `read` / `decomposition_tree` | WBS / decomposição de **processo** | process id | **NO** para paraphrase “árvore de componentes” de item — não declara ≠ product BOM |
| DAVI product structure | BOM / estrutura de **produto** | `product_code` / `code` | YES (“product structure/BOM”) |

`OWNER_CHANGE_REQUIRED=YES` (TEO). Sem tradução local DÉLIA. Sem hardcode `if product: DAVI`.

---

## 5. Auditoria `declare_investigation_goal`

| # | Achado |
|---|---|
| Disponibilidade | tool Application no FunctionToolset do orchestrator |
| Opcional | YES |
| Uso em evals 298–299 | **0/55 traces** |
| Validação | `_GOAL_CLASSES`; `business_subject` ≤240 no plan |
| Eco ao modelo (antes) | **ausente** — write-only |
| Influência em progress | só se `evidence_needed` preenchido |
| Benefício se obrigatório | **não comprovado** nesta task → **não** tornado obrigatório |

---

## 6. Defeitos comprovados vs hipóteses

| ID | Tipo | Ação |
|---|---|---|
| Uncovered/coverage só pós-`_attempt_projection` | PROVEN (código + traces null) | **EXTEND** — projetar dentro de `_attempt_projection` |
| `business_subject` write-only no declare | PROVEN (código) | **EXTEND** — echo no resultado ACCEPTED |
| TEO decomposition atrator | PROVEN_IN_SAMPLE | OWNER_CHANGE; sem workaround local |
| Modelo “não entendeu intenção” | INCONCLUSIVE | intenção não observável sem declare |
| Obrigar declare_goal | NOT_PROVEN_BENEFIT | não feito |
| INT-2 typed evidence kinds | TO_INVENTORY / dependency | não implementado |

---

## 7. Correções pontuais

1. `_attempt_projection`: se `uncovered_after`, inclui `uncovered_user_identifiers` + `coverage_note` de recuperação (fonte única).
2. `declare_investigation_goal`: ecoa `business_subject` aceito.

**Não:** novo Agent/router/planner; hardcode DAVI/TEO; mudança InvestigationAnswer; live LLM.

---

## 8. Testes (política respeitada)

| Camada | Resultado |
|---|---|
| RED/GREEN `test_int1_intent_goal_projection_signals.py` | PASS |
| Adjacentes: pagination projection, investigative progress, full-context, final bounded | PASS |
| FULL_BACKEND_SUITE | NOT_RUN |
| EXTERNAL_LLM_CALLS | 0 |
| LIVE_VALIDATION | PENDING_PO_AUTHORIZATION |

### Proposta mínima de live (não executar)

```text
EXACT_QUESTIONS: G1 + P1 control + 1 sibling paraphrase + 1 negative (process WBS real)
NUMBER_OF_MODEL_CALLS: ≤ 4 scenarios × 1–2 reps (≤8 turns)
MODEL_ID: qwen/qwen3-14b / openrouter_qwen
EXPECTED_EVIDENCE: first_tool / args entity|capability; declare_goal usage rate; uncovered in traces; DAVI structure path on G1 recovery
COST_CEILING: ≤8 turns × request_limit profile
SECURITY_GATES: DELIA_EVAL_EGRESS_AUTHORIZED + credential scope + prod untouched
```

---

## 9. Residuais

| ID | Estado |
|---|---|
| INT1-G1-TEO-DECOMPOSITION-ATTRACTOR | OPEN / OWNER_CHANGE_REQUIRED |
| INT1-GOAL-DECLARATION-UNUSED | OPEN (opcional; usage=0 em sample) |
| INT1-INTENT-NOT-OBSERVABLE-WITHOUT-DECLARE | OPEN |
| INT1-LIVE-INTENT-SELECTION-RERUN | PENDING_PO_AUTHORIZATION |
| INT1-STAGE | BLOCKED |

**NEXT:** `COORDINATION_INT1_INTENT_SELECTION_INDEPENDENT_REVIEW`
