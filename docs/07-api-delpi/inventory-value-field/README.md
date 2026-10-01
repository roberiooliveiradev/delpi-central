# Inventário semântico e de consumidores — campo `value` (API DELPI)

> **Escopo:** pass de inventário/evidência + Contract Freeze proposal. **Nenhum contrato, catálogo, consumer ou dado persistido foi alterado.**
> Artefato de dados: `value_field_consumer_inventory.json` (98 linhas, schema v2 com colunas de freeze).

## 0. Estado validado (rebaseline)

| Item | Valor | Evidência |
|---|---|---|
| HEAD | `22b4aef60626cbf4f0f822a0972053f113f2ab71` | `git rev-parse HEAD` |
| `origin/main` | `22b4aef…` — **igual a HEAD** | `git ls-remote origin main` (live) |
| REMOTE_REVALIDATION | **PASS** | fetch bem-sucedido nesta sessão |
| Branch | `main` | `git branch --show-current` |
| Working tree | 4 arquivos modificados + ~18 untracked `.tmp-*` (diagnósticos de terceiros) + artefatos deste inventário — preservados | `git status --short` |
| OpenAPI operations | **720** | `openapi_baseline.json` |
| Rotas de dados TV | **520** | `tv_data_routes.json` |
| Rotas projetáveis com `value` | **98** (72 SI + 26 non-SI) | revalidado em HEAD |

## 1. Achado central — `value` não tem um significado único

| Onde | Significado de `value` | Produzido em runtime? |
|---|---|---|
| SI `*_realized` (36 ops) | valor realizado — **escalar canônico** | sim (SI API) |
| SI `*_meta` (36 ops) | meta comparável — **alias** de `comparable_goal` | sim |
| Quality parity (5 ops) | espelho do KPI primário | sim, via `attach_quality_kpi_parity` / use case |
| `get_refugos_rankings` | custo R$ por linha em `items[]` — **canônico de domínio** | sim |
| Demais 17 non-SI | **nunca emitido** — candidato de catálogo inexistente no payload | não |
| TV presentation | `kpi.value` / `kpiMetrics[].value` — chave de apresentação | sim (camada TV, não API) |
| Chat presentation | `kpiCards[].value` — chave de apresentação compilada | sim (camada chat, não API) |

## 2. Auditoria de consumidores persistidos (tv_dashboard, read-only)

Fonte: `delpi-postgres-plugins` local (dev), schema `tv_dashboard`. Produção **não** auditada — classificar resultados como evidência local.

Superfícies JSONB auditadas: `slides.native_config` (32), `playlists.master_config` (10), `playlists.data_defaults` (10), `playlist_sections.master_config` (1), `slide_templates.native_config` (4), `playlist_history.snapshot` (46), `gpt_actions_idempotency_keys.response_snapshot` (14).

Binding model confirmado: bloco → `dataBinding.operationId` | `dataSourceId` → bloco-fonte | `dataModels[].inputs[].operationId`. Campos projetados: `textProjection.field`, `kpiProjection.metrics[].field`, `chartProjection.series[].field`, `contentRuns[].dataRef.field`, `cells[][].dataRef.field`.

### Refs `field == "value"` em slides ATIVOS (88 refs totais; 25 em slides ativos)

| Slide | Bloco | Caminho | operationId resolvido | Classificação |
|---|---|---|---|---|
| `df385a9b` "Refugo e retrabalho" (pl `422136fc`) | 3, 8, 20, 24 | `textProjection.field` | `get_quality_rework_cost_pct` ×2, `get_quality_scrap_cost_pct` ×2 | **INVALID_CATALOG_FIELD** — `value` nunca emitido por esses producers; funciona via fallback de apresentação (`kpi.value`) |
| `8ea92ea6` "PPM interno e externo" (pl `422136fc`) | 3, 26 | `textProjection.field` | `get_si_indicator_quality_ppm_external_realized` ×2 | **KEEP_REALIZED** |
| `8ea92ea6` | 4, 12 | `textProjection.field` | `get_si_indicator_quality_ppm_external_meta`, `get_si_indicator_quality_ppm_internal_meta` | **MIGRATE_META** → `comparable_goal` |
| `8c3bed1b` "Kaizen e 5S" (pl `422136fc`) | 10, 25 | `textProjection.field` | `get_si_indicator_quality_kaizen_ideas_realized`, `get_si_indicator_quality_kaizen_financial_realized` | **KEEP_REALIZED** |
| `8c3bed1b` | 11, 26 | `textProjection.field` | `get_si_indicator_quality_kaizen_ideas_meta`, `get_si_indicator_quality_kaizen_financial_meta` | **MIGRATE_META** |
| `8c3bed1b` | 28 | `textProjection.field` | `get_audit_5s_summary` | **KEEP_REALIZED** (emitido, alias de paridade → candidato a remap `average_score` na Wave 3) |
| `befc8ecb` "Personalizado" (pl `6583bb0e`) | 3, 4 | `chartProjection.series[0].field`, `kpiProjection.metrics[0].field` | `get_production_oee_series` (fora do universo-98) | **LEGITIMATE_DOMAIN_VALUE** — `value` = chave de série/KPI de apresentação para op cujo catálogo não declara `value` |
| `2aee17bc` "Transforma+ - apps" | 1 | `chartProjection.series[0].field` | `get_production_oee_series` | **LEGITIMATE_DOMAIN_VALUE** |
| `839f2e10` "NC em LMPs" | 6 | `textProjection.field` | `get_lmp_nonconformity_streak` (fora do 98) | **LEGITIMATE_DOMAIN_VALUE** (apresentação) |
| `1ece5f8a` "WEG SC — % ANO" (pl `850d110a`) | 2, 4, 5 | `kpiProjection.metrics[0].field`, `contentRuns[1].dataRef.field`, `cells[0][0].dataRef.field` | `get_commercial_rol_summary` via `dataModels[].inputs[]` | **LEGITIMATE_DOMAIN_VALUE** — composta legada; o migration service já remapeia opId para rotas simples |

`playlist_history` (46 snapshots) e `gpt_actions_idempotency_keys` (5 commits com `value` refs) **espelham** os slides acima — histórico, não consumers ativos; provam que **GPT Actions (`gpt_commit_change`) escreve bindings com `field:"value"`** e que `data_route_gpt_support.py` expõe `valueFields`/`projectableFields` à façade GPT.

**Nenhuma ref persistida aos 8 ops de drift de catálogo** (rol targets, ebitda, fixed_cost, department-idd, stock-value, quality series) — mas amostra é DB local dev.

## 3. Verificação dos 8 ops de drift

| operationId | Catálogo declara | Campo real em runtime | Correção exata de catálogo |
|---|---|---|---|
| get_new_business_rol_target_pct | `new_business_rol_target_pct`, `value` | `rol` + **`rol_target_pct`** (via `recompute_target_pct_from="rol"`) | `valueFields=[rol_target_pct, rol]` |
| get_weg_rol_target_pct | `weg_rol_target_pct`, `value` | `rol` + **`rol_target_pct`** | `valueFields=[rol_target_pct, rol]` |
| get_financial_ebitda_pct | `financial_ebitda_pct`, `value` | `ebitda_over_rol_pct` (+ `ebitda_value`, `rol`) | `valueFields=[ebitda_over_rol_pct]` |
| get_financial_fixed_cost_pct | `financial_fixed_cost_pct`, `value` | `fixed_cost_over_rol_pct` (+ `fixed_cost_value`, `rol`) | `valueFields=[fixed_cost_over_rol_pct]` |
| get_dashboard_department_idd | `score`, `value`, `idd` | `score` (+ `classification`, `contribution`) — resposta sem `meta.fields` | `valueFields=[score]` |
| get_supplies_stock_value | `value`, `stockValue`, `total` | `summary.total_stock_value`, `total_stock_quantity`, `by_branch`, `by_location`, `top_products` | `valueFields=[total_stock_value]` |
| get_quality_rework_cost_pct_series | `quality_rework_cost_pct_series`, `value` | `points[].metrics.rework_cost_pct` | `seriesField`/`points[].metrics.rework_cost_pct` |
| get_quality_scrap_cost_pct_series | `quality_scrap_cost_pct_series`, `value` | `points[].metrics.scrap_cost_pct` | `seriesField`/`points[].metrics.scrap_cost_pct` |

Prova em código: producers + `meta.fields` (`kpi_field_labels.py`) + rotas. Nenhum producer desses ops emite `value` — **não adicionar `value` ao producer** (condição de parada 10).

## 4. Consumers: registro ≠ dependência de campo

| Consumer | Registrado? | Lê `data.value`? | Evidência |
|---|---|---|---|
| TV pipeline (gateway→enrichment→display) | 98/98 | indireto — `value` é candidato de `valueFields`; `kpi.value`/`kpiMetrics` materializados | código |
| TV MFE binding editor | 98/98 | `value` aparece como opção de campo quando declarado | código |
| Bindings persistidos (DB local) | 13 refs em ops do 98 | sim — ver §2 | dump read-only |
| Chat tier-C registry | 98/98 registrados | **não diretamente** — `measure_fields` schema-driven; `kpiCards[].value` é chave de apresentação gerada pelo `PresentationKpiCompilerService` | código |
| Chat follow-up grounded answer | — | lê `cards[].value`/`baseline.value` — **artefato de apresentação do chat**, não `data.value` da API | código |
| DAVI | 8/98 na allowlist | **não** — `approvedResponseFields` só campos semânticos | contrato |
| GPT Actions (tv façade) | catálogo inteiro | `valueFields`/`projectableFields` expostos; `gpt_commit_change` **escreve** `field:"value"` em bindings | código + DB |
| MCP `resource_metadata` | existe | metadados, não projeção de `value` | código |
| commercial-api BFF | rotas próprias | campos semânticos (`bff_get_closing_rate`, `bff_get_sales_conversion_rate_series`) | código |
| Dashboard MFEs | path-level | **não** — todos leem campos semânticos / `indicators[].score` | código |

## 5. Matriz de Contract Freeze

JSON v2 (`value_field_consumer_inventory.json`) com colunas: `operationId, route, producer_field, value_runtime_emitted, value_semantics, canonical_field, consumer_count_code, consumer_count_persisted, consumer_locations, decision, migration_required, compatibility_policy, removal_precondition, evidence`.

Distribuição: **KEEP 37** (A: 36 SI realized + D: rankings) / **DEPRECATE_ALIAS 53** (B: 36 SI meta + C: 5 parity + F: 12) / **FIX_CATALOG 8**.

## 6. Waves de migração propostas (não executar)

| Wave | Conteúdo | Ops | Pré-condição |
|---|---|---|---|
| **1** | Correções de catálogo (drift): `valueFields`/`projectableFields` ← campos reais (`rol_target_pct`, `ebitda_over_rol_pct`, `fixed_cost_over_rol_pct`, `score`, `total_stock_value`, `points[].metrics.*`). Sem mudança de producer. | 8 | nenhuma — bindings ativos nunca viram `value` emitido (fallback já cobre) |
| **2** | Normalização semântica aditiva SI meta: garantir `comparable_goal` como canônico documentado; manter `value` emitido (alias). TV picker passa a preferir `comparable_goal`. | 36 meta | Wave 1 |
| **3** | Migração de bindings persistidos `field=="value"` → campo canônico (padrão `tv_commercial_composite_binding_migration_service.py`): 13 refs ativas mapeadas + auditoria do DB de produção. | refs, não ops | Wave 1 + auditoria prod |
| **4** | Migração de consumers de código: catálogo TV deixa de listar `value` onde não emitido; display fallback permanece interno à TV. GPT Actions deixa de oferecer `value` para ops não-emissoras. | 20 non-SI | Waves 1–3 |
| **5** | Enforcement: `value` removido de `valueFields`/`projectableFields` nas ops B/C após deprecation window; residual search (`field:"value"` em JSONB prod, code refs). | 41 | Wave 4 + zero refs persistidas |
| **6** | (opcional, versão futura) remoção física de `value` de payloads SI meta / parity — **BREAKING**, requer major/contract notice. | 41 | política de versão + clientes migrados |

## 7. Plano de testes (antes de implementar)

1. **Producer contract tests**: por sibling group, afirmar campos reais do payload (incl. ausência de `value` nos grupos E/F e presença nos A/B/C).
2. **Catalog-vs-schema sync (CI invariante novo)**: para cada rota TV, `projectableFields`/`valueFields` ⊆ campos realmente declarados/emidtos (`meta.fields` + schema de resposta). Falha = drift. Detecta os 8 ops atuais.
3. **Persisted-binding migration tests**: fixture com `field:"value"` por classe (KEEP_REALIZED / MIGRATE_META / INVALID_CATALOG_FIELD) → remap correto, idempotente, sem mutação de outros campos.
4. **Old-consumer × new-producer**: slide com `value` → resposta sem `value` para ops de catálogo corrigido → fallback de apresentação resolve `kpi.value`.
5. **New-consumer × compatible producer**: binding `comparable_goal`/`rol_target_pct` resolve em producer atual (campos já emitidos).
6. **Positive/sibling/negative**: positive = campo semântico resolve; sibling = op irmã da mesma família; negative = `INVALID_PROJECTION_FIELD` para campo inexistente pós-catálogo.
7. **Residual search**: CI grep `field:\"value\"` em fixtures/JSONB exportados + teste de regeneração do catálogo (`generate_tv_data_routes_from_openapi.py`) sem reintroduzir `value` fantasma.

## 8. Stop conditions — status

| Condição | Status |
|---|---|
| value semantics divergem do inventário | não observado — inventário revalidado em HEAD `22b4aef` |
| producer autoritativo difere | não observado |
| consumer externo exige o alias permanentemente | **não encontrado** — GPT Actions escreve `value` mas via chave de apresentação; DAVI/MFEs/chat usam semânticos |
| binding persistido sem operationId associável | **resolvido** — `dataModels[].inputs[].operationId` cobre o único caso sem `dataBinding` direto ("WEG SC") |
| campo canônico muda significado de negócio | não — canônicos já emitidos hoje |
| precisaria adicionar campo fake a producer para satisfazer catálogo | **gatilho confirmado para 8 ops** → decisão FIX_CATALOG, nunca adicionar `value` ao producer |

## 9. TO_INVENTORY residual

- Conteúdo de bindings JSONB em **produção** (DB real) — a auditoria acima é do DB local dev.
- Catálogos persistidos em versões antigas / overlays em DB divergentes do JSON do repo.
- Consumidores externos não registrados (BI/exportações) — ausência no repo não é prova; verificar via access logs do gateway/api-delpi.

## 10. Recomendação de wave de implementação

**Wave 1 (FIX_CATALOG)** é a única de baixo risco sem dependências: corrige 8 declarações de catálogo para campos reais. Todo o resto depende da auditoria de produção (Wave 3) antes de qualquer remoção de `value` de catálogo/payload.

## 11. Arquivos inspecionados nesta pass

Regras: `platform-api-contracts-integration`, `contract-evolution-backward-compatibility`, `platform-quality-testing`, `api-delpi-response-contract`, `centralized-rules-first`, `evidence-driven-execution`.
Código: `dashboard_router.py`, `dashboard_si_indicator_metric_service.py`, `get_dashboard_indicator_metric_use_case.py`, `get_dashboard_department_score_use_case.py`, `quality_kpi_parity_service.py`, `ppm_routes.py`, `quality_router.py`, `losses_routes.py`, `commercial_router.py`, `financial_routes.py`, `supplies_router.py`, `get_segment_rol_target_use_case.py`, `kpi_field_labels.py`, `dashboard_goals_service.py`, `delpi_operational_gateway.py`, `projection_fields_contract.py`, `comunicado_data_enrichment_service.py`, `display_format_service.py`, `tv_commercial_composite_binding_migration_service.py`, `data_route_gpt_support.py`, `presentation_kpi_compiler_service.py`, `chat_follow_up_grounded_answer_service.py`, `resolveDataBoundBlockRoute.ts`.
Dados: `tv_dashboard.*` JSONB (read-only, DB local), `davi_external_read_allowlist.json`, `operational_route_registry_autotierc.ci.json`, `openapi_operation_contracts.json`, `tv_data_routes.json`, `openapi_baseline.json`.

## Limitações

- DB auditado = dev local; produção permanece TO_INVENTORY.
- Nenhuma mutação de produção, contrato, consumer ou DB foi feita.

## 12. Wave 1 — execução (catalog drift correction)

Base: `8b6042b1a3bcbe1d51b428edf7c66af9429fb5b8` (HEAD = origin/main, live-verified).
Revalidação do universo nesta base: 726 ops OpenAPI (era 720 no inventário inicial),
520→525 rotas TV geradas (5 novas ops GET do baseline + 2 operationIds renomeados
upstream), 98 rotas com `value`, 72 SI, 26 non-SI — as 8 operações de drift
permanecem idênticas.

### Correções aplicadas (fonte canônica = `tv_data_route_overlays.json`)

| operationId | valueFields antes | valueFields depois | campo real |
|---|---|---|---|
| get_new_business_rol_target_pct | `new_business_rol_target_pct`, `value` | `rol_target_pct`, `rol` | `rol` + `rol_target_pct` (enrichment) |
| get_weg_rol_target_pct | `weg_rol_target_pct`, `value` | `rol_target_pct`, `rol` | idem |
| get_financial_ebitda_pct | `financial_ebitda_pct`, `value` | `ebitda_over_rol_pct` | `ebitda_over_rol_pct` |
| get_financial_fixed_cost_pct | `financial_fixed_cost_pct`, `value` | `fixed_cost_over_rol_pct` | `fixed_cost_over_rol_pct` |
| get_dashboard_department_idd | `score`, `value`, `idd` | `score` | `item.score` (unwrap) |
| get_supplies_stock_value | `value`, `stockValue`, `total` | `total_stock_value`, `total_stock_quantity`, `total_locations` | `summary.*` |
| get_quality_scrap_cost_pct_series | `quality_scrap_cost_pct_series`, `value` | `metrics.scrap_cost_pct` + `seriesField: "points"` | `points[].metrics.scrap_cost_pct` |
| get_quality_rework_cost_pct_series | `quality_rework_cost_pct_series`, `value` | `metrics.rework_cost_pct` + `seriesField: "points"` | `points[].metrics.rework_cost_pct` |

`projectableFields: null` nos overlays purga os projectableFields obsoletos
herdados do catálogo anterior (`merge_with_existing`);
`normalize_projectable_fields_on_route` rematerializa a partir de `valueFields`
+ `valueFieldTypes`/`valueFieldLabels`.

### Segurança de consumidor (revalidada no DB dev local)

- 117 documentos JSONB auditados; **0** refs `field:"value"` ligadas às 8 ops;
  1 slide_template (`get_supplies_stock_value`) vincula só `operationId` — consome
  a lista do catálogo, sem campo fixo.
- Runtime TV sempre acrescenta fallbacks `value|total|pct|percentage` à sonda
  escalar — remover a declaração do catálogo não remove comportamento de runtime.
- Producers, rotas SI, `items[].value` de rankings e dados persistidos: intocados.

### Invariante executável adicionado

`tv-dashboard-api/tests/test_catalog_value_field_contract.py`:
catalog `projectableFields`/`valueFields` → devem resolver no schema autoritativo
da resposta (resolver estrutural com paths aninhados, probe `summary`, unwrap
`item` e caminho relativo à linha de `seriesField`); oráculo = inventário JSON
(`decision=FIX_CATALOG`) + schemas de resposta derivados do producer. Cobre
positivo, irmão (parity `value` legítimo e série sibling) e negativo.

### Resultado

`generate_tv_data_routes_from_openapi.py --check` OK (525 rotas — o gate estava
vermelho no HEAD base por drift do baseline); `check_tv_data_routes.py` OK;
suites tv-dashboard-api: 1405 passed, 2 falhas pré-existentes em
`test_focused_data_source_context.py` (fronteira de `end_date` — falham
igualmente no HEAD sem a mudança). Contract impact: API HTTP = NONE;
TV catalog = CORRECTIVE/BEHAVIORAL.


---

## Auditoria de consumidores persistidos — PRODUCAO (srv-api)

Data: 2026-09-30. Ambiente autoritativo: `srv-api` (192.168.1.237),
`plugins_hub.tv_dashboard` via `delpi-postgres-plugins`, acesso SSH
`operador@srv-api` -> `docker exec psql` com
`default_transaction_read_only=on`. Repositorio em producao:
`5033d41` (== HEAD local pos-Wave 1); imagem `delpi-tv-dashboard-api`
servindo catalogo corrigido (verificado in-container).

READ-ONLY: nenhuma mutacao (SQL de leitura apenas).

### Documentos inspecionados: 3.883

| superficie | docs |
|---|---|
| slides.native_config | 110 |
| playlists.master_config / data_defaults | 15 + 15 |
| playlist_sections | 11 |
| slide_templates | 4 |
| playlist_history (snapshots) | 3.355 |
| gpt_actions_idempotency_keys | 373 |

### Referencias field=="value" — ATIVAS: 97 (todas em slides)

| classe | n | ops |
|---|---|---|
| KEEP_REALIZED | 15 | SI `*_realized` (ppm x12, kaizen x3) |
| MIGRATE_META | 7 | SI `*_meta` (ppm x5, kaizen x2) |
| DEPRECATE_PARITY_ALIAS | 9 | nonconformity_streak x4, scrap/rework_cost_pct x4, audit_5s x1 |
| LEGITIMATE_DOMAIN_VALUE | 11 | get_refugos_rankings (chart sobre items[].value) |
| PRESENTATION_VALUE | 55 | projecao normalizada {label,value} — ops fora das 98 |
| INVALID_CATALOG_FIELD | 0 | — |
| TO_INVENTORY | 0 | — |

Historico: 33.232 refs em playlist_history sao ecos de snapshots
(~50 pares op+path unicos). GPT idem: 307 refs sao snapshots de
write (REPLAY retorna resposta, nao re-aplica config) — evidencia
historica, nao dependencia ativa.

### Gate Wave 2 (SI meta)

7 bindings ativos leem `value` de `*_meta` (canonical:
`comparable_goal`) em 4 slides / 2 playlists. Nenhum binding meta
usa `goal_value`/`reference_goal`. SI realized: 15 bindings `value`
corretos (KEEP) — Wave 2 nao deve toca-los.

Artefato sanitizado: `prod_value_binding_audit.json` (97 linhas:
playlist/slide/block ids, operationId, field_path, classe — sem
valores de negocio).
