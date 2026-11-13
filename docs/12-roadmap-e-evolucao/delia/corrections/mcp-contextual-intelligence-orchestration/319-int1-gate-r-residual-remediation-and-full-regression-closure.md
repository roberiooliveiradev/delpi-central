# 319 — INT-1 Gate R | Remediação integral dos residuais e fechamento das 4 suítes

**Data:** 2026-11-13  
**Tipo:** EXECUTION / REMEDIATION — código + evidência publicadas para revisão independente (não é autoaceite).  
**TASK_ID:** `DELIA-C3-T2-INT1-GATE-R-REMEDIATION-FINAL-COMMIT-AND-PUSH-01` (execução sob `DELIA-C3-T2-INT1-GATE-R-COMPLETE-RESIDUAL-REMEDIATION-AND-FINAL-VALIDATION-01`).  
**BASE_HEAD:** `87729c5323` (reanchor inicial; WIP concorrente identificado e preservado).  
**Autoridades:** 16 → 293 → 300 → 313–318 → execution ledger → residual register.  
**Fase:** C3/T2, INT-1 não encerrada. `L/A/O=PASS` reportados e sujeitos a revisão; `R` agora proposto `PASS` — veredito final é da coordenação. Nenhum avanço de fase ou produção autorizado.

## 1. Resultado autoritativo das 4 suítes (containers isolados, mounts do candidato)

| Suíte | Resultado | Estado |
|---|---|---|
| DÉLIA (`delia-api`) | **1,601 passed / 0 failed** | exit 0 |
| TÉO (`transformometro-api`) | **2,127 passed / 62 skipped / 0 failed** | exit 0 |
| VISTA (`tv-dashboard-api`) | **2,535 passed / 0 failed** | exit 0 |
| DAVI (`api-delpi`) | **5,970 passed / 10 skipped / 0 failed** | exit 0 |

Reconciliação R-X1: contagens medidas em junit/pytest autoritativo nesta execução (não herdam os relatórios de Doc 317). Skips são baseline canônico dos próprios pacotes (fixtures externas/exports operacionais gitignored/serviços vivos), não supressão de falha — nenhum teste foi desabilitado ou xfail-ado nesta remediação.

## 2. Matriz das classes do Doc 318 → resolução

| ID | Classificação Doc 318 | Resolução | Primeira divergência / causa raiz |
|---|---|---|---|
| R-D1 profiles parity | POLICY_RECONCILIATION_REQUIRED | **CLOSED** | Doc 300 ratificou divergência de capacidade (qwen 32 turns/20k vs ollama 4/6000). Teste reescrito: `TECHNICAL_CAPACITY_PATHS` (model, generation, effective_context_window_tokens, prior_turns_limit, max_projection_chars) toleram divergência; **toda governança** (retries, timeouts, attempts, observability) exige paridade + teste negativo que detecta divergência proibida. 6/6 GREEN |
| R-D2 truncamento | OPEN/TO_VERIFY | **CLOSED — PASS** | Truncamento é parcial honesto e recuperável: envelope de paginação (`has_more`,`total`), owner aceita `page`, DÉLIA projeta `extract_pagination_envelope`. Nenhum defeito |
| R-T1 OAuth TÉO | BASELINE_REPORTED | **CLOSED** | 4 das 5 falhas "OAuth" eram async sem plugin — mesma causa de R-T2 |
| R-T2 realtime async | ENVIRONMENT_REPORTED | **CLOSED** | `pytest-asyncio` ausente de `requirements.txt` — dependência declarada; 16 testes async recuperados |
| R-T3 demais TÉO | UNCLASSIFIED_FAIL | **CLOSED** (todos classificados) | Ver §3 |
| R-V1 baseline VISTA | BASELINE_REPORTED | **CLOSED** | Consolidação 18→6 tools ratificada (commit `06103630cf`) — testes stale reconciliados ao contrato (`proposal_handle`, `DEPENDENCY_UNSATISFIABLE`, sem `confirmation=`); avatar `PUBLIC_BASE_URL` env-driven; `_presentation_payload_cache` reset no fixture autouse |
| R-V2 OpenAPI sync | ENVIRONMENT_REPORTED | **CLOSED** | Baseline stale (583 vs 597 GETs vivos). Sync canônico `sync_openapi_baseline.py` + regen `tv_data_routes.json` (597 rotas); drift host/container era falta de `openapi_param_locale.json` no container |
| R-V3 artifact | PROVEN_TEST_ISOLATION_DEFECT | **CLOSED** | `TV_DATA_ROUTES_PATH=/app/data/tv-dashboard/catalog/` (mount runtime) dessincronizado do conteúdo regerado — replicado `sync_safe()` do startup |
| R-A1 DAVI | ENVIRONMENT+UNCLASSIFIED | **CLOSED** | `git` ausente na imagem eval (binário host + `.git` via docker cp); manifests pinned ressincronizados (`dd9799a202` → sha live) via spec canônica; gaps `ROUTE_CONTRACTS`; literal `Query` → tier factories; avatar env-driven |
| R-X1 reconciliação | INCONSISTENCY_PROVEN | **CLOSED** | Contagens autoritativas §1 |
| R-V-budget (novo) | — | **CLOSED** | Envelope Actions >100KiB — §4 |
| R-V-b5 (novo) | — | **CLOSED** | Patch `ACCESS_SVC` mirava módulo errado — §5 |

## 3. TÉO — 12 falhas de domínio classificadas

- **Defeito real 1 — vazamento de setor:** `resolve_instancia_anchor` ignorava `setor_id`/`codigo_setor` top-level quando `setores` presente mas vazio → `"" == ""` em `_share_setor` vazava recurso de outro setor. Fix no owner `shared_resource_scope_service`.
- **Defeito real 2 — ordem autorização↔existência:** `_upsert_document` resolvia existência (404) antes do check de permissão (403); `check_processo_manage_access` ignora o id → ordem invertida vazava existência. Corrigido no branch DECOMPOSITION_TREE.
- **Stale tests (mocks faltando):** `_valid` sem `ProcessoRepository`; setor-não-vinculado sem `FilialRepository` — mesmo padrão dos siblings.
- **Contrato novo:** rota virou PREPARE legado (proposal 200) — teste atualizado para PREPARE→COMMIT (commit 400 correto).
- **Date-sensitive:** `sent_at=2026-08-27` fora da janela de 10 dias → data relativa; 1 dashboard idem.
- **Fixtures:** `fixtures/cadastro/*.json` gitignored por design (export operacional) → fixture sintética `cadastro_bootstrap_filiais_synthetic.json` + exceção no `.gitignore` + path `parents[]` corrigido.
- **Dashboard SQL tiers:** investigado via `pagination_tiers`/`pagination_inbound_inventory` — regerados (123→125 entries) e rota ajustada ao tier `page_25_100`/`limit_200_500` via factories centralizadas.

## 4. VISTA — compactação do envelope Actions (≤100KiB)

Baseline já estourava o teto: `envelopeAscii` HTTP = 105,294B; standalone headroom = 2,247B (<4,096 exigido). Cortes somente de redundância/transporte, com precedente canônico (`18c0505e69`):

- `designIntelligence.designMethodology` — registro do avaliador server-side; ponteiro canônico permanece em `agent_directives.design_methodology`.
- `visual_selection.catalog_chart_types` — duplicata literal de `designTokens.chartTypeHints` (mantido).
- `designTokens.partChrome` + `designTokens.roles` — pisos de chrome/vocabulário de slots são autoridade VERIFY server-side; `typography.minTvSize` e `recipes[].roles` seguem na projeção.
- `filter_layering.decision_table` — restatement compacto de `placement` (autoridade estrutural intacta).
- `layout_perception.epistemology` — integralmente restated pelas `rules`/`forbidden` da própria seção; `screenshot_parity.epistemology` (autoridade única) **mantido**.
- `modes` **mantido** — pinado no transporte Actions (`build_capability_surface()` default=`"actions"`).

**Não cortado (autoridade live):** `capabilities` (vocabulário intent→op), `operations` (índice já compacto), `anti_patterns`, `object_resolution`, todas as seções de regras/forbidden/pipeline — permanecem por contrato.

Resultado: standalone `envelopeAscii` = **96,715B** (headroom **5,685** ≥ 4,096); dispatch `get_catalog` c/ `displayFormatCatalog` = **102,182B** ≤ 102,400.

## 5. VISTA — outros

- `test_list_shares_denied_without_manage`: `patch(ACCESS_SVC)` mirava `playlist_access_service.PlaylistAccessService`, mas `playlist_share_service` usa binding próprio — passava isolado por sorte do DB. Alvo corrigido para `playlist_share_service.PlaylistAccessService` (padrão dos siblings com `{SHARE_SVC}.PlaylistRepository`).
- Catálogo de runtime `~/.delpi/tv-dashboard/catalog/tv_data_routes.json` (mount `TV_DATA_ROUTES_PATH`) ressincronizado ao conteúdo canônico.
- Mounts faltantes no eval: `/docs` (inventários value-field) e `/scripts` (gerador).

## 6. DAVI — outros

- `get_pcp_stock_rupture_pendencies`: entrada de registry corrigida para `paged_list` (resposta traz `items`+`total`; teste canônico commitado exige o shape).
- `ROUTE_CONTRACTS` gaps adicionados: `prc_catalog_items`, `prc_supplier_search`, `get_pcp_stock_rupture_pendencies`, `get_nonconformity_operator_ranking`, `export_nonconformity_operator_ranking_excel`, `cancel_audit_5s_nc_candidate_without_plan`.
- `prc_catalogs_router`/`purchase_requests_router`: literal `Query` → factories centralizadas (`LIMIT_QUERY("limit_200_500")`, `PAGE_SIZE_QUERY("page_25_100")`).
- Manifests governed-knowledge v1/v2 re-pinados ao sha live via spec canônica (`davi_governed_knowledge_bundle_lib.py`).

## 7. DÉLIA — outros

- `test_llm_tuning_comes_from_runtime_json`: ambient `DELIA_RUNTIME_PROFILE=openrouter_qwen` tornava a asserção env-dependente → `delenv` determinístico (mesma classe do TTL deterministic-fix no teste de concorrência VISTA — `DELPI_AUTH_RBAC_CACHE_TTL_SECONDS=0` é config dev canônica, não defeito de auth).

## 8. Contratos preservados

- `TV_READ` ≠ `TV_WRITE` — sem mutação RBAC; `displayFormatCatalog` continua sob `TV_WRITE` no catálogo administrativo.
- Semântica 401/403/503 intacta (AuthN/AuthZ/dependency).
- PREPARE/COMMIT e `additive_single_shot` inalterados; paridade de nomes `vista_*` ↔ MCP neutro via `surface_parity.parity_map` (projeções derivam do mesmo modelo canônico).
- `display_format.list` permanece projetando presets exatos do backend sob `TV_READ`.
- `operations` continua índice compacto (`operationSchemas="openapi_requestBody_oneOf"`); `capabilities` ≥10.
- `productGuide` MCP-primary; Actions descobre via `gpt_get_product_guide`.

## 9. Residuais

| Residual | Estado | Nota |
|---|---|---|
| INT1-PROJECTION-BUDGET | **CLOSED** | reconciliado em R-D1 (Doc 300 ratificado) |
| INT1-ATTEMPT-STATUS-CONFLATION | OPEN_MINOR | observability debt — `attempt.status` confla classes |
| INT1-MCP-HEAVY-VIEW-TIMEOUT | OPEN_MINOR | `mcp_timeout` 15s em `teo.analyze` pesado — confiabilidade |
| INT1-DAVI-NONEXECUTABLE-CAPS | OPEN | herdado Doc 310, owner DAVI |
| INT1-EVAL-ENV-FLAKES | OPEN_OPERATIONAL | `model_unavailable`/`turn_budget_limited` ocasionais |
| INT1-EVAL-ENV-CATALOG-ARTIFACT | **CLOSED** | runtime catalog resyncado (§5) |
| TÉO 62 skipped / DAVI 10 skipped | BASELINE_SKIPS | fixtures externas/exports operacionais — sem supressão |

## 10. Gates e recomendação

- `L_GATE=PASS` (reportado); `A_GATE=PASS` (AGENT_COUNT=1, owners intactos); `O_GATE=PASS`.
- `R_GATE=PASS_PROPOSED` — as 4 suítes atingem exit 0 estrito do Doc 293 nesta execução; veredito formal exige revisão independente da coordenação (este documento não autoaprova).
- `NEW_REGRESSIONS=0` vs baseline do candidato; todos os fixes são owner-bounded: 2 defeitos reais de código (vazamento de setor TÉO, ordem authz/existência), demais stale tests/fixtures/env/baseline/artifact/drift — classificados individualmente.

**INT1_CLOSED=NO; INT2/INT3/T3/PRODUCTION_DEPLOY=NOT_AUTHORIZED.**

**NEXT=`COORDINATION_INT1_GATE_R_PUBLISHED_CODE_INDEPENDENT_REVIEW`** — SHA do commit e artefatos de teste disponíveis para revisão.
