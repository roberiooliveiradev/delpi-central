# 300 — INT-1 Full Context Delivery, MCP Contract Semantics and Model Context Configuration Remediation

**TASK_ID:** `DELIA-C3-T2-INT1-FULL-CONTEXT-AND-MCP-SEMANTIC-CONTRACT-REMEDIATION-01`  
**Data:** 2026-11-11  
**Tipo:** INT-1 bounded remediation (context completeness + MCP semantic audit)  
**REFERENCE_HEAD (task):** `90af103cb66c298be8b570788e7525c212da4569` (ancestral)  
**BASE_HEAD (reanchor):** `6b89c452c3` → concurrent docs then `61a60b25cd`  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED  
**NEW AGENT / ROUTER / INT-2 / INT-3:** NOT_AUTHORIZED  

---

## 1. Objetivo e escopo

Prioridade: capacidade de investigação (completude informacional autorizada) antes de economia de tokens.

Separação aplicada:

| Classe | Política |
|---|---|
| A — essencial | contratos, nomes, descrições owner, schemas, ids, proveniência, erros, cobertura, continuação — sem truncamento silencioso |
| B — volumosa | registros empresariais / páginas — recuperável; incompletude explícita |
| C — proibida | secrets/JWT/não autorizados — redaction obrigatória preservada |

---

## 2. Abstraction Gate

| Campo | Valor |
|---|---|
| RESPONSIBILITY | context projection + runtime profile config (investigation path) |
| OWNER | `delia-api` / `PydanticAiInvestigationOrchestrator` + `OperationalCapabilityOrchestrator` catalog projection |
| CANONICAL_SOURCE | runtime JSON `pydantic_ai.runtime.delpi.json` + MCPToolset owner descriptions |
| CONSUMERS | Agent run (MCP tools), pre-call context budget, eligibility catalog DTO |
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | EXTEND (`_bounded_json`, `_project_semantic_tool_catalog`, profile `openrouter_qwen`) |
| NEW_ROUTER / NEW_AGENT | NO |

---

## 3. Inventário de limites (escopo relevante)

| FILE / SYMBOL | CURRENT → DECISION | CLASS |
|---|---|---|
| `_EnvelopeHintedToolset` desc `[:500]` | já REMOVED (doc 299) | REMEDIATED |
| `_project_semantic_tool_catalog` `description[:320]` | REMOVE → descrição owner integral | REMOVE |
| catalog prop `description[:160]` + props/required `[:24]` | REMOVE cortes; preservar `enum` | REMOVE |
| `catalog[:80]` | safety ceiling 256 + log `catalog_overflow` | MAKE_CONFIGURABLE residual / safety |
| `_attempt_projection` `content[:2000]` | REMOVE; política só em `_bounded_json` | REMOVE |
| compose pair `content[:2000]` | REMOVE idem | REMOVE |
| `_bounded_json` overflow stub (status/content only) | EXTEND essential-field-first + coverage_note | REMOVE silent loss |
| `_bounded_json` str 1200 / list 40 | scale com `limit` | MAKE_CONFIGURABLE (via projection budget) |
| `openrouter_qwen` window 32768 | → **40960** (capacidade OpenRouter qwen3-14b) | MAKE_CONFIGURABLE |
| `openrouter_qwen` `prior_turns_limit` 4 | → **32** (range max 64) | MAKE_CONFIGURABLE |
| `openrouter_qwen` `max_projection_chars` 6000 | → **20000** (teto validator) | MAKE_CONFIGURABLE |
| `hint[:280]` schema-derived | PRESERVE (não é texto owner) | PRESERVE_CONTRACT_LIMIT |
| candidate summary slices | PRESERVE (discovery summary) | PRESERVE_CONTRACT_LIMIT |
| security redaction / JWT | PRESERVE | PRESERVE_SECURITY_LIMIT |
| ProcessHistory token trim | PRESERVE (overflow explícito via window) | PRESERVE_CONTRACT_LIMIT |
| `investigation_context_overflow` fail-closed | PRESERVE (não trunca silencioso) | PRESERVE_CONTRACT_LIMIT |

---

## 4. Configuração de contexto

| Campo | Antes (`openrouter_qwen`) | Depois |
|---|---|---|
| MODEL_ID | `qwen/qwen3-14b` | inalterado |
| MODEL_CONTEXT_CAPACITY (provider) | 40960 (anunciado) | **efetivo 40960** |
| effective_context_window_tokens | 32768 | **40960** |
| max_output_tokens | 8192 | 8192 (reserva estruturada) |
| prior_turns_limit | 4 | **32** |
| max_projection_chars | 6000 | **20000** |
| prior_turns_limit validator max | 16 | **64** |

`local_ollama` / `openrouter_kimi` **não** alterados indiscriminadamente.

Overflow pre-call: permanece `investigation_context_overflow` (explícito). Durante o run, `ProcessHistory` + `_select_surviving_messages` continuam a limitar por janela — não inventa contexto ilimitado.

---

## 5. Auditoria semântica MCP (DAVI / TÉO / VISTA)

Fontes: contratos publicados nos owners (não síntese DÉLIA).

### G1 — árvore de componentes vs decomposition_tree

| Capability | Owner meaning | MODEL_VISIBLE (MCPToolset) |
|---|---|---|
| TEO `read` entity=`decomposition_tree` | **WBS / decomposição de processo** (Transformômetro), não BOM de produto | descrição longa lista `decomposition_tree` entre entidades de processo sem disclaim explícito “≠ product BOM” |
| DAVI `get_product_structure` / product structure | **BOM / estrutura de produto** por `product_code` | “READ-only product structure/BOM…” |

| Campo | Valor |
|---|---|
| CONTRACT_SUFFICIENT (TEO desc for product BOM paraphrase) | **NO** (ambígua para “árvore de componentes” de item) |
| MODEL_VISIBLE_PARITY (após remoção [:500]/[:320]) | **PASS** no path DÉLIA (owner text preservado) |
| OWNER_CHANGE_REQUIRED | **YES** — TEO: esclarecer que `decomposition_tree` = process WBS, não estrutura de produto/BOM |
| DÉLIA local translation | **FORBIDDEN** (não criada) |

### P2 — processos / paginação

Contratos TEO `process` search expõem `page`/`page_size`. Continuação depende de (1) pagination na observação (doc 299) e (2) payload não silenciado por `_bounded_json` overview (corrigido nesta task). Live multi-rep **não reexecutada** (security gate BLOCKED neste ambiente).

### P3 — formatos / dashboards / playlists

VISTA vs TEO analyze: diferença de contrato permanece owner-side. Sem roteamento fixo. Doc 299 já mostrou melhoria de first-tool VISTA; esta task não reivindica novo live P3.

---

## 6. Correções implementadas

1. Catálogo semântico: descrição owner completa; enums e descriptions de propriedades preservados; cap de segurança 256 com log de overflow.
2. `_bounded_json`: prioriza chaves essenciais; escala caps com budget; overflow final preserva pagination/limitations/continuation/proveniência + `coverage_note`.
3. Remoção de `content[:2000]` em `_attempt_projection` e compose-pair.
4. Perfil `openrouter_qwen` alinhado a 40960 / projection 20k / history 32.

---

## 7. Testes

| Suite | Resultado |
|---|---|
| RED/GREEN `tests/test_int1_full_context_projection_remediation.py` | PASS |
| `test_int1_tool_description_and_pagination_projection.py` | PASS |
| `test_pydantic_ai_runtime_config.py` | PASS |
| investigation / native MCP / secure gate unit | PASS |

Live Qwen 8×3 + generalização: **TEST_NOT_RUN** — `SECURE_EVAL_GATE=BLOCKED` neste host (sem `DELIA_EVAL_EGRESS_AUTHORIZED`, model mismatch `qwen3:8b`, credential scope residual `NONE_PROVEN_SEPARATE_FROM_PROD`). Não contornar o gate.

---

## 8. Observabilidade (eval)

| Métrica | Estado nesta execução |
|---|---|
| MODEL_CONTEXT_CAPACITY | 40960 (config + provider contract) |
| ACTUAL_CONTEXT_TOKENS | UNAVAILABLE (sem live) |
| MODEL_VISIBLE_TOOL_COUNT | UNAVAILABLE (sem live) |
| TOOL_DESCRIPTION_COMPLETENESS | unit PASS (parity markers) |
| SCHEMA_COMPLETENESS | unit PASS (enums) |
| OBSERVATION_COMPLETENESS | unit PASS (essential overflow) |
| HISTORY_INCLUDED | config prior_turns=32; live UNAVAILABLE |
| CONTEXT_OVERFLOW | fail-closed path preserved; live UNAVAILABLE |

---

## 9. Residuais / decisões

| ID | Estado |
|---|---|
| INT1-G1-TEO-DECOMPOSITION-ATTRACTOR | OPEN — requer owner TEO description clarity |
| INT1-LIVE-FULL-CONTEXT-RERUN | BLOCKED — security/credential gate |
| INT1-CREDENTIAL-ISOLATION | RESIDUAL (inalterado) |
| INT1-CATALOG-HARD-CAP-256 | safety residual (configurável futuro se necessário) |
| INT1-STAGE | **BLOCKED** |
| INT1_CLOSED | NO |
| INT2/INT3/T3/PRODUCTION | NOT_AUTHORIZED |

**NEXT:** `COORDINATION_INT1_FULL_CONTEXT_INDEPENDENT_REVIEW`

---

## 10. Arquivos

- `delia-api/app/application/capability_provision/governed_capability_orchestrator.py`
- `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py`
- `delia-api/app/infrastructure/config/pydantic_ai_runtime_config.py`
- `delia-api/config/pydantic_ai.runtime.delpi.json`
- `delia-api/tests/test_int1_full_context_projection_remediation.py`
- este documento + ledger / 16 / residual updates
