# Changelog — Playbook 12: apresentação declarativa (jun/2026)

## Documentação

- Playbook: [playbook-12-apresentacao-declarativa-refatoracao.md](../roadmap/playbook-12-apresentacao-declarativa-refatoracao.md)
- Segunda onda de generalização do pipeline de apresentação (pós onda 1 em [apresentacao-dados-generalizada-jun2026.md](../roadmap/apresentacao-dados-generalizada-jun2026.md))

## Fase R0 — baseline e inventário

- `ChatPresentationRefactorBaselineService` — contagem de condicionais por path, métodos `_enrich_*` dedicados e gaps de perfil (`visualBuilders`, `tableAssembly`)
- Script `scripts/audit_presentation_path_ifs.py` (`--write-baseline`, `--check-baseline`, `--json`)
- Baseline congelado: `docs/architecture/presentation-refactor-baseline-jun2026.json`
- Fixtures tier A: `presentation_vocabulary.json` → `playbook12Refactor.tierAPipelineCases`
- Vocabulário R0: `playbook12Refactor` (auditFiles, tierAProfileKeys, tableAssemblyPathFragments, scanPatterns, targets)
- Testes: `test_presentation_refactor_baseline.py`

### Métricas iniciais (jun/2026)

| Métrica | Valor |
|---------|-------|
| Condicionais por path (4 arquivos) | 46 |
| Montagem tabela no use case | 15 |
| Handlers rota (section availability) | 10 |
| Linhas section availability | 1125 |
| Métodos `_enrich_*` dedicados | 7 |
| Perfis tier A sem `visualBuilders` | 6 |

## Fase R2 — registry de bundles visuais

- `ChatPresentationProfileVisualBundleService` — mapa `builderName → callable` + loop por `viewOrder`
- `presentation_profiles.json` — `visualBuilders`, `chartPolicy` (`skip`|`auto`), `visualBundle` (`dashboardListRole`, `requiresItems`, …)
- `ChatPresentationVisualBundleService` reduzido — sem `_enrich_*_bundle` dedicados (796 → 273 linhas)
- 11 perfis ricos declarados; tier A restante sem builders: `analyser` (R3/R6)

## Fase R3 — montagem declarativa de `tablePresentations`

- `ChatPresentationTableAssemblyService` — registry de builders + layouts (`profile_primary`, `profile_only`, `analyser_slots`)
- `presentation_profiles.json` → `tableAssembly` em 11 perfis (incl. analyser com slots por vocabulário)
- `ExecuteExternalActionUseCase` — bloco ~200 linhas de `elif` substituído por `assemble()`
- `ChatPresentationStructureDedupService` — slots `profileTablePresentation` / `inspectionTablePresentation` preservados quando referenciam tabelas do bundle (R3)
- Testes: `test_chat_presentation_table_assembly_service.py`
- Baseline: `useCaseTableAssemblyPathConditionalCount` 15 → 2

## Fase R4 — section availability declarativa

- `ChatPresentationSectionRulesService` — `resolve_visibility`, `build_framing`, `resolve_narrative_order` por regras JSON
- `presentation_profiles.json` → `stackPlans.*.sectionRules` (analyser, stock, factory/production/shipping status, exclusividade, MP, simulador, precificação, árvore)
- `ChatPresentationSectionAvailabilityService` reduzido — delega ao rules service; fallback genérico via `ChatPresentationStackMarkdownService`
- Baseline: `sectionAvailabilityLineCount` 1125 → 78; handlers por rota 10 → 0

## Fase R5 — texto e decisão por perfil

- `ChatPresentationProfileTextBuilderService` — registry `textBuilder` (14 perfis)
- `ChatPresentationOperationalDecisionService` — árvore/preço/estoque/analyser via flags + `operationalDecision` no vocabulário
- `ExternalActionTextPresentationPresenter` — ~80 linhas de `elif` por path removidas
- `ChatPresentationDecisionService._decision_for_operational_intent` — delega ao serviço operacional

## Fase R6 — quartet visual unificado

- **Lote 1:** playbook status (`production_status`, `shipping_status`, `structure_exclusivity`)
- **Lote 2:** `factory_status`, MP (`last_purchase`, `purchase_*`), `sale_pricing`, `raw_material_price_intelligence`, `cost_impact_simulation`
- Builder estendido: KPI `sectionCards`/`computedCards`, chart `composition`/`aggregate_mp_stock`, tree `primary/fallback`/`combineSections`
- 11 perfis com `compositeVisualSpec`; presenters finos delegam ao serviço canônico
- Limpeza: bloco duplicado `build_cost_impact_*` removido de `product_raw_material_price_presenter.py`
- Testes: `test_chat_presentation_composite_visual_builder.py` + regressões playbook/MP/pricing

## Fase R7 — MFE confia no metadata da API

- `presentationMetadataPolicy.ts` — toolbar/stack via `presentationDecision.selected`, `visualOrder`, `dataShape.hasHierarchy`
- Removidos `isTableFirstRouteToolCalls` / `isStructureHeavyToolCalls` (heurística por path)
- `presentationMultiRoute.ts` — ordem visual por tool call; `ROUTE_VISUAL_ORDER` só fallback
- `presentationStackPlan.ts` — sem fallback inline `/stock`
- Testes MFE: `presentationMetadataPolicy.test.ts` + 333 regressões no plugin

## Fase R8 — narrativa, dedup e gaps residuais

- `presentation_profiles.json` — `humanizedNarrative: skip|enrich` (stock, sale_pricing skip; default enrich)
- `ChatPresentationHumanizedNarrativeService` — skips via perfil; headers via `presenter_content.humanizedNarrative` (sem regex PT)
- `ChatPresentationStackOrderService` — detecção de atenção/destaques via JSON
- `ChatPresentationStructureDedupService` — flag `structureDedupApplied` no metadata
- MFE: `presentation_vocabulary.json` + `presentationVocabulary.ts`; dedup confia na flag da API
- `ChatSchemaDrivenPresentationService._RICH_PROFILE_KEYS` — históricos de compra/orçamento

## Fase R9 — CI, homologação e encerramento

- `audit_presentation_coverage.py` — `--check-table-roles` (fail tier A sem `role`), `--check-visual-builders` (warn)
- `tests/fixtures/presentation_table_role_gate.py` — validação sobre `tierAPipelineCases`
- `ChatPresentationCoverageService.find_visual_builder_warnings` — `viewOrder` vs `visualBuilders`
- Workflow presentation — novos gates + regressões pipeline/role
- §8 homologação H1–H12 em `perguntas-teste-chat-jun2026.md`

## Fase R10 — fechamento tier A (visualBuilders + cobertura)

- `analyser` — `visualBuilders` tree/chart/kpi/dashboard; registry `build_analyser_*`
- `stock` — `build_stock_chart` no perfil e registry
- `tierAProfileKeys` — 13 perfis com `tableAssembly`
- `tierAPipelineCases` — 13 fixtures (shipping, exclusividade, cost-impact, MP/compras)
- Baseline R0: `tierAMissingVisualBuildersCount` → 0; gate `--check-visual-builders` sem avisos tier A

## Fase R11 — chips pós-resposta API↔MFE

- `text_when_available` no perfil `sale_pricing`; removidos `stock_like`/`price_like` do use case
- `should_auto_force_chart` — substitui check por path em auto-gráfico
- `interactivity.json` — `viewChipLabels.chart` → «Ver em gráfico»
- Gate `--check-interactivity-chips` + `expected_interactivity_labels` em tier A
- MFE `presentationInteractivityPolicy.ts` — menu confia em `presentationDecision`

## Fase R12 — regressão entity contract + CI consolidado

- `text_presentation_presenter.py` — parents/structure/stock via entity/profileKey (0 path literals)
- `--check-playbook12` — gate único (perfis, roles, chips, path baseline, new ops)
- `presentation_playbook12_regression_gate.py` + `test_playbook12_regression_suite.py`
- Baseline R0: `totalPathConditionals` → 0

**Playbook 12 encerrado (R0–R12).**

## Fase R1 — `role` nas tabelas

- Vocabulário: `presentation_vocabulary.json` → `tableRoles` (grupos por perfil, tokens globais, slots metadata)
- Serviço: `ChatPresentationTableRoleService` — `resolve_role`, `assign_roles`, `enrich_metadata`
- Wiring: `ChatPresentationFieldNormalizationService` (após normalização de colunas/KPI)
- MFE: `resolveTableRole` prefere `presentation.role`; `inferTableRoleFromTitle` marcado deprecated
- Testes: `test_chat_presentation_table_role_service.py`, `presentationStackPlan.test.ts`
