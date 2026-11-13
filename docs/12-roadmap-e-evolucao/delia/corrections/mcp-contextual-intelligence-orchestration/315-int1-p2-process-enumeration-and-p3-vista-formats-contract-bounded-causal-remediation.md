# 315 — INT-1 P2 Process Enumeration and P3 VISTA Formats Contract — Bounded Causal Remediation

**TASK_ID:** `DELIA-C3-T2-INT1-P2-PROCESS-ENUMERATION-AND-P3-VISTA-FORMATS-CONTRACT-REMEDIATION-01`
**BASE_HEAD:** `c5b4a1c553d9d6c620099db064fd3d4fd9577f56` (reancoragem: local `630ca6f3b9` → ff `c5b4a1c553`; WIP concorrente preservado)
**PHASE:** C3/T2 — INT-1 não encerrada · `INT1_STAGE_ACCEPTANCE=PENDING_COORDINATION_REVIEW`
**MODEL:** `qwen/qwen3-14b` via `openrouter_qwen` · instrução `generalist-semantic-v2-2-object-authz-continuity` inalterada
**ESCOPO:** duas pendências do Doc 314 — P2 (enumeração de processos) e P3 (formatos de visualização VISTA). Não é auditoria geral.

---

## 1. Reancoragem

```text
HEAD pré-ff:        630ca6f3b90abd50ecaffceefa92f2d3380414a3
origin/main:        c5b4a1c553d9d6c620099db064fd3d4fd9577f56
Ação:               fast-forward (2 commits docs-only alheios); sem drift
PHASE_FROM_16:      C3/T2 · INT-1 pendente de revisão de coordenação
NEXT_FROM_LEDGER:   COORDINATION_INT1_FINITE_ACCEPTANCE_DECISION (Doc 314)
CP_RQ:              remediação causal bounded P2 + decisão contratual P3
FROZEN_DECISIONS:   AGENT_COUNT=1 · instrução v2-2 fp 3692299dac74c26e intacta ·
                    RBAC/owners intactos · sem Agent/router/planner/resolver novo
WIP concorrente:    preservado (plugins/*, tv-dashboard-api/data, stash alheios)
```

---

## 2. Frente A — P2: reconstrução causal completa

### 2.1 Traço histórico `or-qwen14b-123ff3f94c37`

```text
USER QUESTION          "Quais processos de transformação estão cadastrados?"
OBJECTIVE              enumeração empresarial (read, breadth)
CAPABILITY SELECTION   teo.read — CORRETA (único owner de processos)
MODEL-VISIBLE CONTRACT B3: "search lists records" — não afirmava que
                       params omitidos enumeram todos os registros acessíveis,
                       nem que `q` é filtro restritivo, nem ecoava critérios
MODEL ARGUMENTS        {entity:process, action:search, params:{q:"transformação"}}
DELIA MUTATIONS        nenhuma — args model-authored íntegros (sem injeção,
                       sem reescrita, sem rejeição de schema)
OWNER READ             {success:true, data:{total:0, items:[]}} — busca filtrada
                       legítima: `q` aplica ILIKE sobre nome/código/família/
                       descrição/objetivo → 0 matches para "transformação"
PROJECTION             {total:0, items:[]} — SEM echo dos filtros aplicados
NEXT MODEL DECISION    retry com O MESMO q + paginação → 0 novamente;
                       desviou para davi.get_context; finalizou insuficiente
```

### 2.2 Primeira divergência material

**MODEL ARGUMENT CONSTRUCTION** — o modelo converteu um objetivo de enumeração numa busca textual restritiva (`q:"transformação"`). Determinísticamente exonerados antes de responsabilizar o LLM:

| Hipótese | Veredito |
|---|---|
| DÉLIA mutou/injetou `q` | EXONERADA — `argument_values_sanitized` bate com o call; zero mutações |
| Schema rejeitou args corretos | EXONERADO — call SUCCESS, sem schema feedback |
| Owner não suporta enumeração | EXONERADO — `ProcessoRepository.list()` sem `q` lista todos não-deletados + `filter_rows_for_access`; probe live retornou `total:109` para `ti_delpi` |
| Transporte/endpoint | EXONERADO — owner respondeu `success:true` |

**Fatores contratuais comprovados (contribuintes, não desculpa):**
1. Descrição B1/B3 dizia "search lists records" sem declarar a semântica de enumeração sem filtro nem a natureza restritiva de `q` — ambiguidade model-visible.
2. Resposta `{total, items}` não ecoava `filters_applied` — impossível distinguir "filtro restritivo → 0" de "catálogo vazio" (critério §7 da task).

### 2.3 Inventário do contrato TÉO `process.search` (CONFIRMADO_NO_CODIGO)

| Atributo | Contrato real |
|---|---|
| `q` | opcional; ILIKE sobre nome/código/família/descrição/objetivo |
| `familia_processo` | match exato |
| outros filtros | `filial_id`, `setor_id`, `status`, `has_improvement`, `page`, `page_size` |
| sem filtros | `ProcessoRepository.list()` → todos não-deletados → `filter_rows_for_access` (escopo do sujeito) — enumeração legítima, PROVADO live (`total:109`) |
| paginação | `page`/`page_size`, cap 40; `{page,page_size,has_more}` |
| retorno | `{total, items[, pagination]}` → agora `+ filters_applied` |
| vazio filtrado ≠ vazio catálogo | agora distinguível via `filters_applied` |

### 2.4 Correção bounded implementada (owner TÉO)

`EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND` — reuso do wrapper `_wrap_search_rows` + projeção `project_search_records`; nenhum componente novo.

1. **`tm_app/interface/mcp/server.py`** — descrição `read` agora declara: "search lists records: **with no params it enumerates ALL records the caller can see** (results echo total + filters_applied + pagination); **q is an optional free-text filter** over name/code/family/description/objective; omit all filters to list everything accessible".
2. **`tm_app/application/gpt_actions/dispatch_service.py`** — `_wrap_search_rows` ecoa `filters_applied` (critérios não-vazios) em ambos os shapes (paginado e não-paginado), para todas as entidades search.
3. **`tm_app/application/gpt_actions/response_compact.py`** — `project_search_records` preserva `filters_applied`.

### 2.5 Testes determinísticos (7 GREEN)

`transformometro-api/tests/test_gpt_process_search_filters_echo.py`:

- `unfiltered_enumerates_all_and_echoes_no_filters` — `filters_applied == {}`, `total` = catálogo
- `filtered_empty_result_echoes_applied_filters` — `filters_applied == {"q": ...}`, `total == 0`
- `filtered_empty_is_not_equivalent_to_empty_catalog` — distinção provada
- `pagination_and_total_echo_filters` — `page/page_size/has_more` + echo
- `family_filter_is_exact_and_echoed` — match exato `familia_processo`
- `disallowed_field_still_fails_closed` — `INVALID_FIELD` preservado (negativo)
- `project_search_records_preserves_filters_applied` — projeção

Adjacentes TÉO (contrato/metadata/platform/v3/parity): **18 verdes**. Suite ampla TÉO: 153 passed / **5 falhas pré-existentes** OAuth-contract (baseline, registrado; não tocadas).

### 2.6 Reavaliação real `or-qwen14b-7c2d2bd54410` (pós-correção)

Primeira tentativa (`or-qwen14b-4be3b315381e`) **invalidada por ambiente**: container TÉO isolado criado sem `--root-path /apps/transformometro-api` → POST `/mcp/` 404 → `catalog_failure:mcp_protocol_error`, toolset sem `teo.*` (11 tools). Corrigido o container isolado (Cmd canônico com root-path) — probe: `tools/list` 6 tools, `process.search{}` → `total:109`, `filters_applied:{}`. **Sem alteração de produção.**

Run válido P2:

```text
B3 toolset          15 tools incl. teo.* — descrição nova PRESENTE:
                    "with no params it enumerates ALL records the caller
                    can see (results echo total + filters_applied + pagination)"
FIRST_TOOL          teo.read
ARGUMENTS           {entity:process, action:search, params:{q:"transformação"}}
OWNER_RESULT        {total:0, items:[], filters_applied:{q:"transformação"}}
                    — echo entregue ao modelo
MODEL DECISION      declarou "insufficient": "Nenhum processo de transformação
                    foi encontrado no sistema." → overridden → clarificação
ELAPSED             88.4s · 1 model call
```

**Resultado:** a correção contratual foi integralmente entregue (descrição explícita em B3 + `filters_applied` visível na resposta) e o Qwen **repetiu** o `q` restritivo e ainda concluiu "nenhum processo cadastrado" a partir de `filters_applied:{q:"transformação"}, total:0` — sem retry sem filtro.

**P2_FIRST_MATERIAL_DIVERGENCE (final): MODEL ARGUMENT CONSTRUCTION — model-caused, agora comprovado pós-correção.** Schema, descrição, projeção e owner exonerados com evidência. `P2_ACCEPTANCE=PARTIALLY_SATISFIED`: contrato owner corrigido e entregue (enumeração live provada: 109 processos acessíveis a `ti_delpi`), mas o outcome empresarial não foi atingido nesta amostra — residual de comportamento do modelo documentado. Menor trabalho restante: iteração bounded de instrução generalista (regra "enumeração ⇒ busca sem filtro; zero filtrado ⇒ alargar antes de declarar ausência") + re-run só P2 — fora do orçamento desta task (4/4 investigações consumidas).

---

## 3. Frente B — P3: inventário contratual VISTA

### 3.1 Superfície MCP real (live, `tools/list`)

| Tool | Ações relevantes | Gate |
|---|---|---|
| `get_context` | `action=context` (TV_READ) · `action=catalog` → **`get_catalog()` exige TV_WRITE** |
| `read` | `playlist.list/get/context`, `playlist_history.history`, `data_route.search` (exige `filters.query` não-vazio), `data_model.inspect` (exige refs playlist/slide/model), `product_guide.guide`, avatar — `data_visualization` **NÃO é entidade** (UNKNOWN_ENTITY real) |
| `analyze` | `data_block_preview`, `data_model_preview`, `intent_materialization` (exigem refs) |
| `knowledge` | guias/verbetes — orientação, não verdade de domínio |

### 3.2 Fonte autoritativa de "formatos de visualização" (CONFIRMADO_NO_CODIGO)

`tv-dashboard-api` — `tv_app/application/services/`:

- `DisplayFormatService.format_catalog_entries()` → publicado como `displayFormatCatalog` em `GptActionsDispatchService.get_catalog()` — **catálogo autoritativo existente**.
- `block_type_vocabulary()` — tipos canônicos de bloco (`DATA_BLOCK_TYPES` = `data_kpi|data_chart|data_table|data_metric|data_source`; `DATA_VIEW_BLOCK_TYPES` = `chart_view|table_view|kpi_view`; canvas/heading/text/shape em contratos de apresentação).
- `tv_data_route_catalog_service` — `allowedDisplayModes` por rota; união canônica `{auto, kpi, line_chart, bar_chart, table}` (probe live: 8 rotas para `ti_delpi`).

### 3.3 Decisão P3-B: capability existe, incompleta para sujeito read

```text
EXISTING_EQUIVALENT=YES   (catálogo existe no owner)
REUSE_DECISION=EXTEND     (extensão de exposição no owner, não na DÉLIA)
```

**Gap comprovado (live, sujeito `ti_delpi` = TV_READ):**

```text
vista.get_context(action="catalog")  → 403 FORBIDDEN (TV_WRITE-gated)
   — único caminho que publica displayFormatCatalog + block_type_vocabulary
read playlist.list                   → success, 0 playlists visíveis
read data_route.search               → per-route allowedDisplayModes apenas;
                                       QUERY_REQUIRED sem query;
                                       searchMissDoesNotProveAbsence=true
read data_visualization              → UNKNOWN_ENTITY
read data_model.inspect              → exige refs playlist/slide/model
analyze.*                            → exige refs de modelo/bloco
```

Conclusão: informação read-oriented ("quais formatos existem") está atrás de permissão **write** — `P3_ACCEPTANCE=BLOCKED_BY_OWNER_CONTRACT`. Alternativas read-scoped existem mas são parciais por contrato (miss não prova ausência; enumeração por rota ≠ vocabulário global). **Não é falha do LLM** — o modelo tentou o caminho semanticamente correto (`get_context catalog`) e respondeu honestamente sobre a negação.

**Dependência formal do owner VISTA (proposta mínima, não implementada unilateralmente):**

```text
OWNER=VISTA (tv-dashboard-api)
CONTRACT_GAP=displayFormatCatalog + block_type_vocabulary só expostos em
             get_catalog() (TV_WRITE) — nenhuma superfície TV_READ publica
             o vocabulário global de formatos
REQUIRED_BUSINESS_EVIDENCE=enumeração autoritativa de formatos/blocos/
             display modes para sujeito read
CONSUMERS=DÉLIA (P3), qualquer consumidor read-only de catálogo
RECOMMENDED_REUSE_OR_EXTENSION=expor o catálogo existente sob TV_READ —
             p.ex. read action catalog/formats no entity adequado ou
             rebaixar get_context action=catalog para TV_READ (decisão do owner)
```

### 3.4 Defeito DÉLIA comprovado no run e corrigido

`or-qwen14b-7c2d2bd54410` P3: envelope owner `{status:"forbidden", httpStatus:403, error_kind:"forbidden", code:"FORBIDDEN"}` foi classificado como `mcp_protocol_error`/`SOURCE_UNAVAILABLE` — negação de autorização governada reportada como indisponibilidade de fonte (mesmo mecanismo do BLK-1/Doc 314).

**Correção bounded:** `delia-api/app/application/specialist_interop/specialist_interop.py` — `_OWNER_ERROR_CODE_MAP["FORBIDDEN"] = MCP_AUTHORIZATION_DENIED` (vocabulário emitido por `tv_app/interface/mcp/tool_bridge.py`). `EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND`.

**Teste:** `test_vista_forbidden_envelope_maps_authz_not_protocol_noise` em `test_specialist_interop_usecase.py` — GREEN; suíte 33 testes verde.

Run P3 pós-correção **não repetida** (orçamento 4/4 consumido); a comunicação honesta já ocorrera mesmo com a classificação errada — a correção melhora a fidelidade diagnóstica da negação.

---

## 4. Avaliações reais — consolidação

| Eval | Cenário | Resultado |
|---|---|---|
| `or-qwen14b-4be3b315381e` | P2+P3 | INVALIDADO por ambiente — container TÉO isolado sem `--root-path` → 404 MCP (corrigido; artefato operacional documentado) |
| `or-qwen14b-7c2d2bd54410` | P2 | teo.read SUCCESS `{q:"transformação"}→0` → declared insufficient "nenhum processo cadastrado" → clarificação. Contrato corrigido entregue; **model-caused** |
| `or-qwen14b-7c2d2bd54410` | P3 | vista.get_context catalog → FORBIDDEN real → resposta honesta sobre permissão. `BLOCKED_BY_OWNER_CONTRACT` |

Budget: 4/4 investigações (`MAX_TOTAL_INVESTIGATIONS=4`). Tokens/custo: indisponíveis no runner (usage redacted) — latências: P2 88.4s, P3 30.4s.

Falhas pré-existentes registradas (não-regressão): 5 OAuth-contract TÉO; 3 delia-api (`runtime_profiles_share_execution_policy` = residual INT1-PROJECTION-BUDGET; `module_exposes_native_first_tools`; `llm_tuning` = env do container prod).

---

## 5. Classificação final da task

```text
P2_ACCEPTANCE=PARTIALLY_SATISFIED
  contrato owner corrigido+entregue (enumeração provada: total 109);
  residual model-caused (argument construction) com evidência;
  próximo passo: iteração bounded de instrução + re-run P2
P3_ACCEPTANCE=BLOCKED_BY_OWNER_CONTRACT
  catálogo autoritativo existe mas TV_WRITE-gated;
  dependência formal VISTA registrada com proposta mínima;
  misclassificação DÉLIA de envelope FORBIDDEN corrigida
MODEL_CAUSED_DEFECTS_PROVEN=YES (P2 pós-correção; P2 histórico)
CODE_CAUSED_DEFECTS_PROVEN=YES (FORBIDDEN→protocol_error — corrigido)
SCHEMA_CAUSED_DEFECTS_PROVEN=NO
OWNER_CONTRACT_GAPS_PROVEN=YES (P3: read-scoped format catalog ausente)
ENVIRONMENT_CAUSED_DEFECTS=YES (eval TÉO root-path — resolvido, operacional)
```

## 6. Residuais e dependências

- `INT1-P2-MODEL-ENUMERATION-STRATEGY` (material): modelo aplica filtro textual a objetivo de enumeração mesmo com contrato explícito; requer iteração bounded de instrução + re-run.
- `EXT-VISTA-READ-FORMAT-CATALOG` (externa): exposição TV_READ do `displayFormatCatalog`/`block_type_vocabulary` — decisão do owner VISTA.
- Operacional: containers isolados de eval devem usar o Cmd canônico (`--root-path /apps/<svc>`) — registrado para futuras evals.
- Gate R (bateria completa) segue pendente de autorização.

## 7. NEXT

`COORDINATION_INT1_P2_P3_INDEPENDENT_ACCEPTANCE_REVIEW` — decidir: (a) autorizar iteração bounded de instrução + re-run P2; (b) encaminhar dependência `EXT-VISTA-READ-FORMAT-CATALOG` ao owner VISTA; (c) gate R.
