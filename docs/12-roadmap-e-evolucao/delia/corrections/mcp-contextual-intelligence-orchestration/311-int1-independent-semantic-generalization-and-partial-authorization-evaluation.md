# 311 — INT-1 Independent Semantic Generalization and Partial Authorization Evaluation

**TASK_ID:** `DELIA-C3-T2-INT1-SEMANTIC-GENERALIZATION-AND-PARTIAL-AUTHORIZATION-REAL-EVALUATION-01`  
**Data:** 2026-11-12  
**EXTERNAL_LLM:** AUTHORIZED — EXECUTED  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**FULL_BATTERY:** NOT_RUN  
**NEW_AGENT / ROUTER / PLANNER:** NO  

---

## 1. Reancoragem

| Item | Value |
|---|---|
| REFERENCE_HEAD | `631a3273d6317ba62b315ef0ab1a52bcf89e88a2` |
| WORK HEAD (início) | reanchor em REFERENCE; `origin/main` subsequentemente avançou com commit EVA unrelated (`1d759026e1…`) — WIP controllership preservado |
| PHASE_FROM_16 | C3/T2 INT-1 PENDING_COORDINATION_REVIEW (Doc 310 → 311) |
| Instruction | `generalist-semantic-v2-2-object-authz-continuity` / fp `3692299dac74c26e` MATCH (não alterada antes da 1ª eval) |
| Model / profile | `qwen/qwen3-14b` / `openrouter_qwen` |
| Config fp | `e4a5b706a3b3156b` |
| Pydantic AI | `2.50.0` |
| Isolation | eval container `delpi-delia-eval-int1-or-qwen14b`; `PROD_CONTAINER_UNTOUCHED=YES` |
| WIP preservado | `controllership-finance` docs + artefatos e2e não relacionados |

Baseline Doc 310 reutilizado: evals `or-qwen14b-985d439b1653` (G1/P1/M1) e `or-qwen14b-525ed88ac205` (AUTH-DENY). **Não repetidos** nesta task.

---

## 2. Corpus independente (congelado antes da eval)

Critério: perguntas/identificadores **fora** do conjunto histórico G1/P1/M1/`90260921` usado no desenvolvimento v2/v2-1/v2-2. Dados verificados ao vivo (SpecialistInterop) antes da freeze.

| ID | Pergunta | Objeto | Classe esperada (oráculo) | Dado live |
|---|---|---|---|---|
| IG1 | Qual é a estrutura de componentes do produto 90260147? | product_structure | DAVI BOM | root+2 items |
| IG2 | Mostre a árvore de decomposição do processo PROC-0034 (DELPI Indicadores). | process_decomposition | TEO WBS | processo_id `29157fc0-…`, decomp_nodes=20 |
| IG3 | Qual o estoque disponível do produto 90260148? | product_stock | DAVI stock | COMPLETED |
| IG4 | Mostre a árvore do item 90264135. | ambiguous_item_tree | prefer DAVI product | root+50 items |
| PARTIAL | Mostre a decomposição do processo PROC-0034 e a estrutura do produto 90260147. | process+product | TEO allow + DAVI deny (`e2e-delia`) | sujeto sem `api-delpi.access` |

Oráculos **não** entram no prompt do modelo.

Corpus versionado: [`evidence/int1-independent-generalization-311/corpus-frozen.json`](../../evidence/int1-independent-generalization-311/corpus-frozen.json) (cópia canônica; raw `.battery` permanece local/gitignored).

---

## 3. Preflight

| Check | Result |
|---|---|
| ENV | `infra/.env` |
| SUBJECT allow | `ti_delpi` — `api-delpi.access`,`transformometro.access`,`delia.access`,`tv-dashboard.read` |
| SUBJECT restrict | `e2e-delia` — Core grants pré-existentes (sem `api-delpi.access`; com `transformometro.access`+`delia.access`); senha Keycloak DEV resetada localmente (sem mudança de grants) |
| Instruction fp | `3692299dac74c26e` MATCH |
| Model config | `e4a5b706a3b3156b` / openrouter_qwen |
| MCP | DAVI/TEO/VISTA enabled no harness |

---

## 4. Testes determinísticos — autorização parcial

Novo: `tests/test_int1_partial_authorization_finalize.py` (+ extensão `_preserve_authorized_with_denial` em `semantic_capability_support.py`).

| Caso | Resultado |
|---|---|
| A SUCCESS→DENIED | PASS — SUCCESS + conteúdo autorizado + `authorization_denied_partial` |
| B DENIED→SUCCESS | PASS — evidência autorizada preservada; retry AUTHZ bloqueado |
| C DENIED só | PASS — terminal `AUTHZ_DENIED` / `mcp_authorization_denied` |
| D NOT_FOUND / owner_query_miss | PASS — ≠ AUTHZ_DENIED |
| E SOURCE_UNAVAILABLE / timeout | PASS — ≠ AUTHZ_DENIED |

Suíte pontual no container eval (bind `/app`): **10 PASS** (parcial + authz denial communication).

---

## 5. Avaliação real Qwen — semântica (`or-qwen14b-99d36aa86540`)

Sujeito `ti_delpi`. TOTAL_INVESTIGATIONS=4. LATENCY≈135578 ms. TOKEN_USAGE/COST=UNAVAILABLE.

| Cenário | First tool | Suitability | Continuity | Objective |
|---|---|---|---|---|
| IG1 | `davi.get_context` → `get_product_structure` | PASS | OK | **SATISFIED** GROUNDED |
| IG2 | `teo.read` `decomposition_tree` | PASS (objeto processo) | recuperação UUID após id código; tour analyze parcial | **NOT_SATISFIED** NON_GROUNDED (truncation/coverage) |
| IG3 | `davi.get_context` → `get_product_stock` | PASS | OK | **SATISFIED** GROUNDED |
| IG4 | `davi.get_context` → `get_product_structure` | PASS (item→produto; sem TÉO) | OK | **PARTIAL/SATISFIED** GROUNDED (owner truncated) |

**Seleção semântica in-sample:** 4/4 first-tool suitability. Sem keyword router. Sem atrator TÉO em IG4 (“árvore”+item).

**Continuidade:** IG2 evidencia residual de argumentos/id de processo (código vs UUID) e fan-out analyze — não é seleção de objeto errado.

---

## 6. Avaliação real — autorização parcial (`or-qwen14b-195dc9cf3bb6`)

Sujeito `e2e-delia`. Pergunta composta processo+produto.

| Campo | Observado |
|---|---|
| Tool surface | DAVI+TEO+VISTA visíveis (B3) |
| MCP invokes | **0** |
| Attempts | 7× `arguments_schema_rejected` / NOT_APPLICABLE |
| Final | NON_GROUNDED, insufficient_evidence, tool_calls_limit |
| AUTHZ_DENIED observado | **NO** (owner nunca alcançado) |
| Data leak / bypass | **NO** |
| Evidência autorizada preservada | **NO** (TEO não executou com sucesso) |

**PARTIAL_AUTHZ_REAL_EVAL=`INCONCLUSIVE`** — fixture/runtime: o Agent esgotou o orçamento em rejeições de schema locais antes de uma READ TEO bem-sucedida e antes de uma DENY DAVI observável. Contratos determinísticos A–E PASS; e2e parcial composto **não** comprovado nesta amostra.

Não houve segunda rodada: sem correção funcional comprovada além do finalize já coberto pelos testes determinísticos; não repetir só para resultado favorável.

---

## 7. Correções desta task

| Mudança | Motivo |
|---|---|
| `_preserve_authorized_with_denial` / `authorization_denied_partial` em retornos SUCCESS com denial no collected | Case A/B: evidência autorizada não pode ser apagada por denial paralelo |
| Cenários IG*/PARTIAL no harness INT-1 | EXTEND mínimo do harness existente |
| Testes `test_int1_partial_authorization_finalize.py` | RED/GREEN A–E |

Instrução v2-2 **inalterada** nesta task (conforme §12).

---

## 8. Generalização

```text
GENERALIZATION_PROVEN_IN_SAMPLE (seleção first-tool / object match)
GENERALIZATION_LIMITATIONS: n=4; IG2 objective not satisfied (owner id/args continuity);
  partial-authz composed e2e inconclusive; no statistical claim
```

---

## 9. Residuais

| ID | Status |
|---|---|
| INT1-GENERALIZATION-SELECTION | MITIGATED_IN_SAMPLE (IG1–IG4 first-tool) |
| INT1-PROCESS-CODE-VS-UUID | OPEN (IG2) |
| INT1-PARTIAL-AUTHZ-E2E-COMPOSED | INCONCLUSIVE (schema-reject loop) |
| INT1-PARTIAL-AUTHZ-DETERMINISTIC | PASS |
| INT1-DAVI-NONEXECUTABLE-CAPS | OPEN (herdado 310) |
| INT1-STAGE | PENDING_COORDINATION_REVIEW |
| INT1-CLOSED | NO |

---

## 10. Próximo passo

`COORDINATION_INT1_GENERALIZATION_AND_PARTIAL_AUTHZ_INDEPENDENT_REVIEW`

Opcional bounded: diagnosticar `arguments_schema_rejected` sob sujeito restrito antes de nova eval parcial composta; ownership TEO id binding (código↔UUID) separado.
