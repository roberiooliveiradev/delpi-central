# 312 — INT-1 Business Identifier Resolution, MCP Schema Integrity and Partial Authorization Real Qwen Remediation

**TASK_ID:** `DELIA-C3-T2-INT1-IDENTIFIER-RESOLUTION-AND-PARTIAL-AUTHZ-SCHEMA-REMEDIATION-01`
**Data:** 2026-11-12
**EXTERNAL_LLM:** AUTHORIZED — EXECUTED
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED
**FULL_BATTERY:** NOT_RUN
**NEW_AGENT / ROUTER / RESOLVER_ENGINE:** NO

---

## 1. Reancoragem

| Item | Value |
|---|---|
| REFERENCE_HEAD | `25f3b76f6b0f06ec730ba1f57eedab951cdd1256` — ancestral do HEAD no início |
| HEAD início | `feat/lnf-migration-f3` (WIP LNF concorrente — **não** executada aqui; estado reportado e preservado) |
| HEAD efetivo execução | `287a534220` = `origin/main` (commits LNF integrados pelo usuário durante a sessão) |
| PHASE_FROM_16 | C3/T2 INT-1 PENDING_COORDINATION_REVIEW (Doc 311 abriu IG2 + PARTIAL) |
| Instruction | `generalist-semantic-v2-2-object-authz-continuity` / fp `3692299dac74c26e` MATCH — **inalterada** |
| Model / profile | `qwen/qwen3-14b` / `openrouter_qwen` |
| Config fp | `e4a5b706a3b3156b` |
| Pydantic AI | `2.50.0` |
| Isolation | eval containers `delpi-delia-eval-int1-or-qwen14b` + `delpi-teo-eval-int1` (TÉO com código corrigido montado); `PROD_CONTAINER_UNTOUCHED=YES` |
| Egress | `DELIA_MCP_TRUSTED_ENDPOINT_HOSTS` **somente** no env efêmero da eval (host TÉO isolado); nenhuma mudança em `infra/.env` |
| WIP preservado | `engineering-api/…/understanding.py` (EVA, concorrente) + artefatos não relacionados — **não** commitados |

Baseline Doc 311 reutilizado: `or-qwen14b-99d36aa86540` (IG2 NOT_SATISFIED) e `or-qwen14b-195dc9cf3bb6` (PARTIAL INCONCLUSIVE). IG1/IG3/IG4 não repetidos.

---

## 2. Inventário e causas raiz (cadeia de evidência)

### Frente A — Identificadores empresariais

| Defeito | Cadeia | Owner |
|---|---|---|
| A1 `params.id=PROC-0034` → 500 owner | `decomposition_tree.get`/views/BPMN/doc faziam cast `::uuid`; `process.get` já resolvia via `ProcessoRepository.get` (uuid **ou** `codigo_processo`) | TÉO `dispatch_service.py` |
| A2 `uncovered_identifier:PROC-0034` após leitura real | cobertura só reconhecia `data.root.code` (padrão DAVI); payload TÉO não devolvia `codigo_processo` | DÉLIA `semantic_capability_support.py` + TÉO response |

**EXISTING_EQUIVALENT=YES** (`ProcessoRepository.get` canonical) → **REUSE_DECISION=REUSE**. Nenhum resolver engine na DÉLIA.

### Frente B — Schema rejection / authz parcial

| Defeito | Cadeia | Owner |
|---|---|---|
| B1 tentativa sem feedback | `validate_arguments` → `None` sem motivo → retry cego | DÉLIA `argument_validation.py` / orchestrator |
| B2 `coverage_note` enganosa | rejeição de schema herda nota "select a different capability" → modelo migra de tool repetindo o erro | DÉLIA `_attempt_projection` |
| B3 `capability_id` ausente no trace | tentativa rejeitada não tem provenance | DÉLIA projection/eval |
| **B4 — causa raiz material** | `focus_arguments_on_next_identifier` **injetava `query` top-level** em args quando o texto do usuário nomeava ≥2 identificadores — em tools cujo schema não declara `query` → DÉLIA rejeitava **a própria mutação** como `arguments_schema_rejected` ×7, `MCP_INVOCATIONS=0` | DÉLIA `pydantic_ai_investigation.py` |

B4 comprovado no trace real: **todas** as rejeições (incl. `teo.get_context`, `davi.get_context`) eram `unknown top-level field(s): query` — o modelo nunca enviou `query`; a mutação vinha do foco. Single-id (IG2/R1) não ativava o caminho → consistente com Doc 311.

---

## 3. Contratos publicados (B1/B2/B3)

| Boundary | Evidência |
|---|---|
| B1 owner | `teo.read` `entity=process action=search|get`, filtros `q/filial_id/setor_id/status/familia_processo/has_improvement/page/page_size`; `decomposition_tree.get params.id` — publicado `string`, runtime exigia UUID (A1) |
| B2 composed | `provider_request_b3` tool_count=15, tool_order estável, `description_length`/`schema_sha256` capturados |
| B3 provider | `pydantic_ai_provider_boundary=PROVEN`; `http_wire_bytes=NOT_OBSERVED` |

`process.search q`: ILIKE em `nome/codigo_processo/descricao` — retorna `processo_id` UUID + `codigo_processo` (Alternativa A search→get viável e confirmada por R2).

---

## 4. Correções implementadas

| Mudança | Arquivo | Motivo |
|---|---|---|
| `explain_arguments()` (bounded, field names/types — nunca valores) | `delia-api/.../argument_validation.py` | B1 |
| `INVALID_ARGUMENTS` content + `LIMITATION_ARGUMENT_SCHEMA_REJECTED` na tentativa | `governed_capability_orchestrator.py` / `contracts.py` | B1 |
| `_attempt_identifier_roots()` — cobertura por valores escalares exatos do payload owner (fullmatch; int→decimal; prosa nunca cobre) | `semantic_capability_support.py` | A2 |
| `declared_properties` no focus — nunca injetar `query` não declarado pelo schema | `pydantic_ai_investigation.py` | **B4** |
| `coverage_note` específica para rejeição de schema (mesma capability + hint `{group}.get_context`) | `pydantic_ai_investigation.py` | B2 |
| `capability_id` na projeção da tentativa rejeitada | `pydantic_ai_investigation.py` + eval | B3 |
| `_resolve_processo_row/_resolve_processo_ref` (reuso `ProcessoRepository.get`) em analyze/decomposition/diagram/BPMN/upsert | `transformometro-api/.../dispatch_service.py` | A1 |
| `codigo_processo`/`nome_processo` no response de `decomposition_tree`/diagram/BPMN | idem | A2 (owner atesta vínculo código↔documento) |
| `DELIA_EVAL_TEO_BASE_URL` + egress host efêmero | `run_int1_openrouter_qwen14b_instrumented_eval.sh` | isolamento eval |
| Observabilidade trace: `limitations`, `content_head`, `authorization_denied` | eval scripts | trace req. |

`NEW_RESOLVER_ENGINE=NO` · `NEW_ROUTER=NO` · `PERMISSIONS_CHANGED=NO` · instrução v2-2 inalterada.

---

## 5. Testes determinísticos

| Suíte | Resultado |
|---|---|
| `test_int1_identifier_resolution_and_schema_feedback.py` (novo, 19) — explain/focus/projection/coverage positive·sibling·negative | **PASS** |
| `test_gpt_process_business_code_resolution.py` (novo, TÉO) — código→UUID, uuid direto, unknown→404, authz após resolução, enrichment | **PASS** |
| Adjacentes delia (arg-validation, continuity, authz-denial, coverage, progress, finalize, parity) | **PASS** |
| Adjacentes TÉO (`record_read`, `process_document_entity`, MCP contract/surface/conformance, response_compact, schema_contract) | **PASS** |
| Suíte delia-api completa | **PASS** — exceto 2 falhas **pré-existentes** em baseline limpo (`test_runtime_profiles_share_execution_policy` config divergence; `test_module_exposes_native_first_tools` assertion stale) |

RED→GREEN: `focus_never_injects_query_undeclared_by_schema` reproduz B4 antes da correção.

---

## 6. Avaliações reais Qwen 14B

| Run | Eval id | Sujeito | Resultado |
|---|---|---|---|
| Rodada válida (R1/R2/R3) | `or-qwen14b-a06d048c2597` | `ti_delpi` | ver tabela |
| IG2 pós-enrichment | `or-qwen14b-64d9e5b4d58b` | `ti_delpi` | ver tabela |
| R4 diagnóstico ×3 | `or-qwen14b-63f52d5f8dfc` / `0369b7bfbd39` / `d95ed7d02ba9` | `e2e-delia` | reprodução incremental B1→B4 |
| **R4 final** | `or-qwen14b-84c04f1194d2` | `e2e-delia` | ver tabela |

TOTAL_INVESTIGATIONS≤8. TOKEN_USAGE/COST=UNAVAILABLE. Setup failure `catalog_failure:mcp_endpoint_egress_denied` descartada (egress allowlist corrigida — env efêmero, não prod).

| Cenário | MCP invokes | Grounding | Objetivo |
|---|---|---|---|
| R1/IG2 `PROC-0034` | `teo.read` ×1 (`decomposition_tree.get {id:"PROC-0034"}` resolveu direto) | **GROUNDED** | partial — `result_truncated` (árvore > budget projeção 20k), **sem** `uncovered_identifier` |
| R2 título "Avaliações de Desempenho" | search→get UUID ×2 | **GROUNDED** | **complete** — `PROC-0035` descoberto via `q`, UUID reutilizado |
| R3 ambíguo "E2E probe proc." | search→0 | NON_GROUNDED | clarificação honesta, **sem** seleção arbitrária |
| **R4 parcial composta** | ×5: `teo.read` SOURCE_UNAVAILABLE(transitório)→`davi.get_context`×2→`teo.read` SUCCESS (eco `codigo_processo`)→`davi.read` **AUTHZ_DENIED** | NON_GROUNDED | **partial** — evidência TÉO preservada + denial DAVI comunicado; `authorization_denied_partial`; sem bypass/leak |

### Critérios §21/§22

```text
IDENTIFIER_RESOLUTION: BUSINESS_IDENTIFIER_RECOGNIZED=YES OWNER_SEARCH_USED_WHEN_REQUIRED=YES(R2)
  AUTHORITATIVE_ID_OBTAINED=YES ID_TYPE_VALID=YES ID_REUSED_CORRECTLY=YES
  TARGET_READ_EXECUTED=YES EVIDENCE_GROUNDED=YES OBJECTIVE_SATISFIED=YES(R2)/PARTIAL(R1 trunc.)
PARTIAL_AUTHZ: VALID_TOOL_ARGUMENTS=YES TEO_READ_EXECUTED=YES AUTHORIZED_EVIDENCE_PRESERVED=YES
  DAVI_DENIAL_OBSERVED=YES DENIED_DATA_DISCLOSED=NO AUTHORIZATION_BYPASS=NO
  USER_FACING_PARTIAL_EXPLANATION=PASS
```

---

## 7. Generalização

```text
GENERALIZATION_PROVEN_IN_SAMPLE — código (R1), título (R2), multi-identificador (R4):
  mesma regra canônica, sem branch por cenário; B4 corrigiu a classe "campo injetado
  não declarado", não o literal "query"
GENERALIZATION_LIMITATIONS: n=4 cenários válidos; R1 truncado por budget (limitação
  honesta); R3 sem match real (clarificação); sem claim estatística
```

---

## 8. Residuais

| ID | Status |
|---|---|
| INT1-PROCESS-CODE-VS-UUID | **CLOSED_IN_SAMPLE** — owner resolve código/título/UUID; R1/R2 provam |
| INT1-PARTIAL-AUTHZ-E2E-COMPOSED | **PROVEN_IN_SAMPLE** — R4 e2e com denial real |
| INT1-ARGS-SCHEMA-FEEDBACK | **MITIGATED** — feedback acionável + get_context hint; modelo pode ainda esgotar budget em schemas opacos (residual de capacidade do modelo, não de contrato) |
| INT1-PROJECTION-BUDGET | **OPEN** — árvores TÉO > `max_projection_chars` (20k) truncam; continuação honesta, paginação owner é residual |
| INT1-DAVI-NONEXECUTABLE-CAPS | OPEN (herdado 310) |
| DELIA-PREEXISTING-TEST-DEBT | **OPEN** — 2 testes falhando em baseline limpo (não causados por esta task) |
| INT1-STAGE | PENDING_COORDINATION_REVIEW |
| INT1-CLOSED | NO |

---

## 9. Próximo passo

`COORDINATION_INT1_IDENTIFIER_RESOLUTION_AND_PARTIAL_AUTHZ_INDEPENDENT_REVIEW`

Residuais bounded opcionais: paginação/continuação de resultados TÉO grandes; contrato de `params` aninhado mais descritivo nas tools de leitura (reduzir dependência de `get_context`).

`PRODUCTION_DEPLOY=NOT_AUTHORIZED` · `FULL_BATTERY=NOT_RUN`
