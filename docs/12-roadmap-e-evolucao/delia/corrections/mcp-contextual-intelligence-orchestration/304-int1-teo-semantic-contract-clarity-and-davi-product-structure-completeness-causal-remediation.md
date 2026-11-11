# 304 — INT-1 TEO Semantic Contract Clarity and DAVI Product Structure Completeness Causal Remediation

**TASK_ID:** `DELIA-C3-T2-INT1-TEO-SEMANTIC-CONTRACT-AND-DAVI-BOM-COMPLETENESS-REMEDIATION-01`  
**Data:** 2026-11-11  
**REFERENCE_HEAD:** `ab1d59557fbc36ad49822a09d66110555af47ab1`  
**EVAL_BASELINE:** `or-qwen14b-198e127edee9` (Documento 303)  
**EXTERNAL_LLM_CALLS:** 0  
**AGENT_CHANGED:** NO  
**INSTRUCTION_CHANGED:** NO  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  

---

## Abstraction Gate

| Frente | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| A TÉO | YES — `ENTITY_DESCRIPTIONS[DECOMPOSITION_TREE]` / registration_guide concepts | EXTEND — ecoar wording canônico na description MCP `read` (`server.py`) |
| B DAVI | YES — `ListProductStructureUseCase` + `classify_source_pagination` / `derive_response_completeness` | EXTEND — omitir nulls no full-mode; tratar JSON null como ausência no classificador |

Sem NEW_AGENT / NEW_ROUTER / NEW_BOM_ENGINE.

---

## A. TÉO — `decomposition_tree`

### Semântica empresarial (PROVEN)

`decomposition_tree` = **WBS / mapeamento macro de processo** (`id = processo_id`).  
Fontes: ADR decomposição, Playbook 20, schema `decomposition_tree_v1`, `ENTITY_DESCRIPTIONS`, domain levels `processo_chave`/`tarefa`/`sub_tarefa`.  
**Não** é BOM / estrutura de materiais de produto.

### Contrato original (tools/list)

`@mcp.tool(name="read")` em `transformometro-api/tm_app/interface/mcp/server.py` listava o token `decomposition_tree` **sem** clarificar WBS de processo.  
`ENTITY_DESCRIPTIONS` já tinha `"Process WBS/decomposition tree (id = processo_id)."` — mas só via `get_context` catalog, **não** na description model-visible da tool `read` (atrator G1).

### Causa raiz Front A

```text
TOOL_CONTRACT_AMBIGUITY (PROVEN)
```

Descrição MCP de `read` insuficiente para distinguir objeto empresarial processo vs produto; surface DAVI BOM estava disponível.

### Correção

Extensão aditiva na description publicada de `read`:

```text
decomposition_tree (process WBS/decomposition tree; id=processo_id —
hierarchical process mapeamento macro, not a materials/product bill-of-materials)
```

Sem menção a DAVI, roteamento, códigos de teste ou Qwen.

### Publicação MCP

Verificada via `asyncio` `list_tools()` → `tools["read"].description` contém `Process WBS` / `processo_id` / distinção materials/product.

### Testes

- `test_read_description_publishes_decomposition_tree_as_process_wbs` PASS  
- adjacent: `test_read_description_documents_search_get…`, metadata alignment, surface_v2 PASS  

### Residuais A

- Live Qwen re-seleção após clarificação: **TEST_NOT_RUN** (LLM externo não autorizado nesta task).  
- Overlay/scope entities (`instance_decomposition_scope`, …) ainda só listadas por nome — fora do escopo G1.

---

## B. DAVI — `get_product_structure`

### Contrato

`operationId=get_product_structure` → `ListProductStructureUseCase` → `BomTreeBuilder` → CTE recursiva SG1 (`max_depth` default 999).  
Args G1/P1: `{code: "90260921"}` sem page/max_depth.

### Resultado original (doc 303)

| Campo | G1/P1 |
|---|---|
| ROOT | 90260921 |
| COMPONENTS | 1 × `10020003` qty 175 |
| DEPTH | 1 (folha MP; `components: []`) |
| pagination | page/page_size/total_pages **null**, total=1 |
| is_complete | **false** |
| DÉLIA | `owner_result_incomplete` → OBJECTIVE **PARTIAL** |

### Matriz de perda

| Etapa | Componentes | Profundidade | Completude |
|---|---|---|---|
| Fonte empresarial (SG1 CTE) | TO_INVENTORY live SQL; obs MCP + docs = 1 MP | multilível **suportado**; neste SKU depth=1 | — |
| Domain / BomTreeBuilder | 1 | 1 | árvore íntegra |
| DAVI Application full-mode | 1 | 1 | **emitia page/page_size/total_pages=null** |
| DAVI MCP projection | 1 | 1 | null → pagination **UNKNOWN** → `is_complete=false` |
| DÉLIA observation | 1 | 1 | propaga `owner_result_incomplete` |
| Finalização | GROUNDED | — | PARTIAL (falso incomplete + overclaim de truncamento) |

### Causa raiz Front B (PROVEN)

```text
FIRST_INFORMATION_LOSS = DAVI full-mode null pagination → classify UNKNOWN → is_complete=false
```

**Não** é “DAVI só busca 1º nível”.  
**Não** é perda de nós multilível neste SKU (fonte flat PA→MP).  
Rubrica/Agent interpretaram incomplete como truncamento hierárquico.

### Correção

1. `ListProductStructureUseCase` full-mode/empty: **omitir** chaves `page`/`page_size`/`total_pages` nulas; manter `total` + `items`.  
2. `classify_source_pagination`: JSON **null** trata-se como ausência da chave (defesa genérica).

Paged mode preservado (`page`/`page_size` explícitos).

### Testes

- `test_hierarchy_full_mode_null_pagination_does_not_force_incomplete` PASS  
- `test_list_product_structure_full_mode_completeness.py` (full/empty/paged) PASS  
- `test_davi_pagination_completeness.py` + bom tree builder PASS (47)  

### Residuais B

- Live SQL probe do SKU 90260921 além do MCP: **TO_INVENTORY** (sem credencial enterprise nesta execução).  
- Live Qwen re-eval G1/P1 após fix: **NOT_AUTHORIZED**.  
- Overclaim do modelo (“falta navegação recursiva”) é comportamento Agent — fora desta correção de contrato/completude.

---

## Arquivos

```text
transformometro-api/tm_app/interface/mcp/server.py
transformometro-api/tests/test_teo_mcp_contract.py
api-delpi/app/application/use_cases/product/list_product_structure_use_case.py
api-delpi/app/application/external_capabilities/dynamic_information/projection.py
api-delpi/tests/test_davi_pagination_completeness.py
api-delpi/tests/test_list_product_structure_full_mode_completeness.py
```

## Não executado

```text
FULL_TEST_BATTERY
EXTERNAL_LLM / G1+P1 live
PRODUCTION_DEPLOY
```

## Próxima validação mínima recomendada

PO-autorizar 1× G1 + 1× P1 OpenRouter Qwen14B no harness isolado filtrado (`DELIA_EVAL_SCENARIO_IDS`) para observar: (1) first-tool G1 pós-clarificação TEO; (2) ausência de `owner_result_incomplete` quando BOM flat completa.

## Stage

```text
INT1_STAGE_ACCEPTANCE=BLOCKED
INT1_CLOSED=NO
INT2/INT3/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED
NEXT=COORDINATION_INT1_TEO_DAVI_INDEPENDENT_REVIEW
```
