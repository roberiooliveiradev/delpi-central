# Changelog — apresentação delivered puro (jun/2026)

## Resumo

Corte definitivo do pipeline rico legado. Toda metadata de `execute_external_action` passa por **schema-first as-delivered**.

## Fase 1 — pipeline (commit `aaabe746`)

- `ChatPresentationMetadataPipelineService` — delegação única a `ChatPresentationApiDeliveredMetadataService` (~35 linhas).
- `ChatDataInsightEnrichmentService` re-ligado no caminho as-delivered (`dataAnswer` / `dataCommentary`).
- `ChatToolContextFormatService` e `ChatPresentationPrimaryViewService` — `ChatSchemaDrivenPresentationService.build_bundle` (sem visual bundle).
- **Removidos** 12 módulos: visual bundle, table assembly, humanized narrative, composite visual, entity route dispatch, hierarchy tree, story, prose quality, dashboard assembly, profile text/visual builders.

## Fase 2 — decisão e contrato (commit `f058a363`)

- Decisão automática só escolhe visuais presentes no payload.
- Estoque e listas `as_delivered` priorizam tabela; texto-first não força perfis `table_when_available`.
- Modo texto explícito → `layoutMode: single` (sem stack forçado por `stackLayoutPolicy: always`).
- Entity resolvida pelo path quando falta `apiDelpiResponseMeta`.
- SQL com `rows`/`items` + `sessionResponseFormat=table` promove tabela via `apply_session_preference`.

## Fase 3 — declarativo e presenter (jun/2026)

- `presentation_profiles.json`: removidas 67 chaves mortas (`visualBuilders`, `tableAssembly`, `textBuilder`, `visualBundle`, `compositeVisualSpec`, …) de perfis `as_delivered`.
- `entitySets.presentationTableAssemblyEntities` esvaziado; `defaults.presentationStrategy` = `as_delivered`.
- Gates `audit_presentation_coverage` / `refactor_baseline`: exigem `visualBuilders`/`tableAssembly` **somente** em perfis `presentationStrategy: legacy`.
- Stubs `build_*_table_presentations` removidos de `ExternalActionResultPresenter`.

## Presenters

Pasta `external_actions/presenters/` reduzida a hosts utilitários (SQL, KPI, operational table, content). Sem presenters por entidade.

## Documentação

- `docs/architecture/presentation-delivered-pure-jun2026.md`
- Playbook 22, chat-assistant-content-presentation, regra Cursor `schema-first-presentation-delivered.mdc`

## Testes

- 462 testes `test_chat_presentation_*` passando após Fase 2.
- `test_chat_presentation_data_only_pipeline.py` — reativado (Fase 4).

## Fase 3b — rich stack as-delivered (jun/2026)

- `is_rich_stack_profile` — só perfis `presentationStrategy: legacy`.
- `should_default_to_text_stack` — bloqueia stack automático em schema-first; mantém stack só com «visão integrada» explícita.
- `apply_visual_order` — não força `layoutMode: stack` por `stackLayoutPolicy: always` em perfis `as_delivered`.
- `structure_exclusivity`: `stackLayoutPolicy` → `on_demand`.
- `entitySets.richStackProfiles` esvaziado.

## Fase 4 — data-only no pipeline (jun/2026)

- `ChatPresentationDataOnlyProseService.apply_pipeline` ligado em `ChatPresentationApiDeliveredMetadataService` (pós-`finalize`).
- `test_chat_presentation_data_only_pipeline.py` reativado.

## Fase 5 — render mínimo em layout single (jun/2026)

- `ChatPresentationPayloadPruningService` — allowlist de tail só em `layoutMode: stack`; plano single sem `narrativeOrder`/`tailVisualOrder`.
- Testes `test_presentation_render_contract.py` alinhados ao modo texto explícito → `single`.

## Fase 6 — slim ChatPresentationDecisionService (jun/2026)

| Módulo | Responsabilidade |
|--------|------------------|
| `ChatPresentationAutomaticScoreService` | scoring + seleção automática |
| `ChatPresentationDecisionMetadataService` | entity, rows, slots |
| `ChatPresentationDecisionBuilderService` | `build`, merge views, stack layout |
| `ChatPresentationOperationalIntentDecisionService` | rich stack, árvore, narrativas por perfil |

Fachada `ChatPresentationDecisionService`: ~790 linhas (era ~2170).

## Fase 7 — preferência, gráfico e decide genérico (jun/2026)

| Módulo | Responsabilidade |
|--------|------------------|
| `ChatPresentationUserFormatPreferenceService` | toolbar, aliases, `build_decision` por preferência |
| `ChatPresentationChartDecisionService` | tipo de gráfico, policy/cap, agregação |
| `ChatPresentationGenericDecisionService` | checklist/canvas, KPI/árvore/dashboard, shape tabular |

`decide()` na fachada: preferência → intent operacional → genérico.

## Fase 8 — enrich_metadata (jun/2026)

| Módulo | Responsabilidade |
|--------|------------------|
| `ChatPresentationDecisionEnrichmentService` | pós-`decide`: scores, insight, chart/dashboard explain, recomendações, text-first/stack |
| `ChatPresentationRouteVisualPolicyService` | ordem visual por rota (estoque, árvore, tabela nativa) |

Fachada `ChatPresentationDecisionService`: **~500 linhas** (era ~2170).

## Fase 9 — fachada mínima (jun/2026)

| Módulo | Responsabilidade |
|--------|------------------|
| `ChatPresentationDecideService` | orquestração `decide()` — preferência → intent → genérico |

Fachada pública: só `decide`, `enrich_metadata`, `compute_scores` (~85 linhas). Wrappers `_*` removidos; consumidores usam delegates canônicos.

## Pendente (Fase 10+)

- OpenAPI import (Playbook 22 Fase D).
