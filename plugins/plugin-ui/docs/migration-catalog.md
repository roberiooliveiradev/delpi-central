# Catálogo de migração — cópias locais → `@delpi/plugin-ui`

Objetivo: **uma implementação** de balões explicativos e primitivos de label/aba nos **plugins MFE**. O **portal** (shell) permanece fora de escopo — não consome `@delpi/plugin-ui`.

## Status — Fase 1 (help)

| Plugin | Arquivo local | Status | Notas |
|--------|---------------|--------|-------|
| `tv-dashboard` | — | ✅ Migrado | Referência de integração |
| `dashboard-production` | — | ✅ Migrado | Piloto Fase 1 |
| `dashboard-commercial` | — | ✅ Migrado | |
| `dashboard-engineering` | — | ✅ Migrado | |
| `dashboard-financial` | — | ✅ Migrado | |
| `dashboard-hr` | — | ✅ Migrado | |
| `dashboard-lmps` | — | ✅ Migrado | |
| `dashboard-quality` | — | ✅ Migrado | |
| `dashboard-supplies` | — | ✅ Migrado | |
| `cadastro-kaizen` | — | ✅ Migrado | F2/F3 completo — ver [UI-PLUGIN-UI.md](../../cadastro-kaizen/docs/UI-PLUGIN-UI.md) |
| `eficiencia-fabril` | — | ✅ Migrado | |
| `transformometro` | — | ✅ Migrado | — |
| `quality-action-plans` | — | ✅ Migrado | — |
| `maintenance` | — | ✅ Migrado | re-export em `components/data/index.ts` |
| `portal` | `src/components/HelpTooltip.tsx` | ❌ Fora de escopo | Shell do host; API controlada (`open`, placement) diferente |

## Mapeamento de classes CSS legadas

| Prefixo antigo | Ação na migração |
|----------------|------------------|
| `*-help-tooltip*` | Remover do plugin; estilos em `plugin-ui/src/styles.css` (`delpi-ui-*`) |
| `*-field__label` | Manter no plugin como `className` em `FieldLabel` |

## Ordem sugerida de migração (concluída Fase 1)

1. Dashboards departamentais — ✅
2. `cadastro-kaizen`, `transformometro`, `quality-action-plans`, `eficiencia-fabril`, `maintenance` — ✅

## Após cada migração

- [x] Remover arquivo `HelpTooltip.tsx` local
- [x] Remover bloco CSS `*-help-tooltip` do `index.css` do plugin
- [x] Atualizar esta tabela para ✅
- [x] `npm run build` do plugin
- [x] Compose: `context: ../plugins`, `dockerfile: {plugin}/Dockerfile`

## Roadmap completo

Fases 0–5, matriz por plugin, riscos e métricas: **[refactoring-roadmap.md](./refactoring-roadmap.md)**.

## Componentes futuros no pacote

Ver inventário detalhado em [refactoring-roadmap.md § 1.3](./refactoring-roadmap.md#13-componentes-duplicados--candidatos-a-extrair-2-consumidores).

Resumo (2+ consumidores):

| Componente | Ocorrências | Fase sugerida |
|------------|-------------|---------------|
| `KpiCard` | 15 | F2 ✅ |
| `ChartCard` | 14 | F2 ✅ |
| `LoadingActivityCard` | 12 | F2 ✅ |
| `Pagination` (+ jump, page size) | 7 dashboards | F2 ✅ (7 dept.) |
| `MultiSelectField` | 13 | F2 ✅ (8 dept. + lmps + ef + tm) |
| `FilterBar` | 12 | F2 ✅ (FiltersRow + FilterInputField) |
| `FilterBarShell` | 2 | F2 ✅ (maintenance form/card; ef grid) |
| `FiltersRow` trailing/compact | 1 | F2 ✅ (quality-action-plans) |

## Gate CI

```bash
python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
python3 scripts/ci/audit_plugin_ui_duplication.py --check          # bloqueia HelpTooltip local + integração
python3 scripts/ci/audit_plugin_ui_duplication.py --check --strict # falha em toda duplicata catalogada
```

| `DataTable` / `DataTableSection` | ~25 | F2 ✅ (7 dept. + lmps DataTable) |
| `DetailFieldGrid` | 5 | F3 ✅ (5 consumidores) |
| `EditableSectionCard` | 3 | F3 ✅ |
| `ReadOnlyField` | 2 | F3 ✅ |
| `SelectField` | 2 | F3 ✅ |
| `TextField` / `TextAreaField` | 1 (PAC) | F3 ✅ |
| `TitleWithHelp` | 1 (PAC) | F3 ✅ |
| `FilterCheckboxField` | 1 (PAC) | F3 ✅ |
| `FormGrid` / `FormActions` | PAC + kaizen | F3 ✅ |
| `FormFieldShell` / campos nativos | kaizen | F3 ✅ |
| `StateBanner` | kaizen | F3 ✅ |
| `PageHeader` (brand) | kaizen + transformometro + maintenance | F3 ✅ |
| `CreatableMultiSelectField` | PAC + kaizen categorias | F3 ✅ |
| `TableHeaderCell` | PAC + transformometro | F3 ✅ |
| `PageHeader` | 7 | F3 ✅ |
| `DetailCard` | 3 | F3 ✅ |
| `SectionCard` | PAC + kaizen | F3 ✅ |
| `EmptyState` / `LoadingState` | 2 | F3 ✅ |

## Status — Fase 4 (utilitários)

| Utilitário | Consumidores | Notas |
|------------|--------------|-------|
| `paginationPages` | plugin-ui Pagination | ✅ desde F2.4 |
| `chartColors` | 8 dashboards + transformometro + PAC | Paletas `DEPARTMENTAL`, `LMPS`, `CSS_VARS` |
| `operationalUnitLabels` | 8 dashboards | Filiais 01/02 TOTVS |
| `goalDisplay` | 8 dashboards | Badges IDD / meta KPI |

Reexport local: `export * from "../../../plugin-ui/src/utils/goalDisplay"` (imports existentes preservados).

## Status — Fase 5 (evidências / confirm / SI)

| Plugin | FileDropzone | Confirm | Notas |
|--------|--------------|---------|-------|
| `cadastro-kaizen` | ✅ | — | `fileDropzoneKaizenClasses` |
| `quality-action-plans` | ✅ | ✅ | `useConfirmDialogController` + `ConfirmModalPanel` |
| `transformometro` | ✅ | ✅ | Provider + `ConfirmModalPanel` |
| `strategic-indicators` | — | — | `operationalUnitLabels` reexport |

| Componente | Pacote | Notas |
|------------|--------|-------|
| `ConfirmModalPanel` | ✅ F5 | Headless; `ModalShell` local (PAC, transformometro) |
| `ModalShell` | ✅ F5.5 | Portal + escape; overlay scope no wrapper |

**Não** mover sem consolidar — ver [contributing.md](./contributing.md).

## Status — Fase 2 (shell de dashboard)

| Plugin | Pagination | MultiSelect | FiltersRow | ChartCard | KpiCard | LoadingActivity | Notas |
|--------|------------|-------------|------------|-----------|---------|-----------------|-------|
| `dashboard-production` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Piloto F2 |
| `dashboard-commercial` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-engineering` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-financial` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-hr` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-quality` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-supplies` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-lmps` | — | ✅ | ✅ | ✅ | ✅ | ✅ | Pagination via CompactPagination |
| `transformometro` | ✅ | ✅ | — | ✅ | ✅ | | CompactPagination + ChartCard + MultiSelect + KpiCard + DataTable + TableHeader F2/F3 |
| `eficiencia-fabril` | — | ✅ | — | ✅ | ✅ | ✅ | ChartCard + MetricKpiCard + FilterBarShell + MultiSelect F2 |
| `maintenance` | ✅ | ✅ | — | — | — | — | TablePaginationNav + FilterBarShell + MultiSelect + DataTable F2 |
| `controle-retrabalhos` | — | — | — | ✅ | ✅ | ✅ | Empty/Loading F3 + KpiCard/ChartCard/LoadingActivity F2 |
| `financeiro-centro-custo` | — | — | — | ✅ | ✅ | — | `@delpi/plugin-ui` + ChartCard/KpiCard F2 |
| `auditoria-5s` | — | — | — | ✅ | — | — | `@delpi/plugin-ui` + ChartCard F2 |
| `pedidos-venda-abertos` | — | ✅ | — | — | ✅ | — | PageHeader F3 + Pagination/KpiCard F2 |
| `inspecoes-entrada` | ✅ | — | — | — | ✅ | — | PageHeader F3 + Pagination/KpiCard F2 |
| `quality-action-plans` | — | ✅ | ✅ | ✅ | ✅ | — | FiltersRow + forms F3 (TextField, TableHeaderCell, FilterCheckbox) |
| `cadastro-kaizen` | — | ✅ | FiltersRow + FilterSelectField + createKaizenKpiCard + SectionCard + forms F2/F3 |

Após migração Pagination: remover `PaginationPageJump.tsx` e `utils/paginationPages.ts` locais; reexportar `TABLE_PAGE_SIZE_OPTIONS` em `./Pagination`.

Após migração MultiSelect: wrapper fino com `createDashboardMultiSelectField` (~20 linhas); CSS permanece no plugin.

## Status — Fase 3 (formulários e detalhe)

| Plugin | DetailFieldGrid | Notas |
|--------|-----------------|-------|
| `dashboard-production` | ✅ | `valueFallback: "—"`; sem empty state |
| `dashboard-commercial` | ✅ | hints + `wrapLabels` |
| `dashboard-quality` | ✅ | empty state "Sem dados." |
| `dashboard-lmps` | ✅ | hints + `wrapLabels` |
| `eficiencia-fabril` | ✅ | empty state "Sem dados." |

Após migração DetailFieldGrid: wrapper fino com `createDashboardDetailFieldGrid` (~12 linhas); CSS `{prefix}-detail-grid*` permanece no plugin.

| Plugin | EditableSectionCard | Notas |
|--------|---------------------|-------|
| `cadastro-kaizen` | ✅ | `editableSectionCardBemClasses("kz")` |
| `transformometro` | ✅ | `editableSectionCardTransformometroClasses("ds")` |
| `quality-action-plans` | ✅ | `SectionCard` + `createDashboardEditableSectionCardPac` |

| Plugin | DetailCard | PageHeader | Empty/Loading |
|--------|------------|------------|---------------|
| `dashboard-production` | ✅ | — | — |
| `dashboard-commercial` | ✅ | — | — |
| `dashboard-lmps` | ✅ | — | — |
| `quality-action-plans` | — | ✅ | — |
| `transformometro` | — | ✅ | — |
| `maintenance` | — | ✅ | — |
| `pedidos-venda-abertos` | — | ✅ | — |
| `inspecoes-entrada` | — | ✅ | — |
| `propostas-comerciais` | — | ✅ | — |
| `strategic-indicators` | — | ✅ | — |
| `controle-retrabalhos` | — | — | ✅ |
| `financeiro-centro-custo` | — | — | ✅ |

## Integração `@delpi/plugin-ui` (Vite + Docker)

Plugins com alias Vite, `styles.css` no bootstrap e Dockerfile `context: ../plugins`:

| Plugin | F1 help | F2/F3 componentes |
|--------|---------|-------------------|
| `pedidos-venda-abertos` | — | PageHeader, Pagination, KpiCard |
| `inspecoes-entrada` | — | PageHeader, Pagination, KpiCard |
| `propostas-comerciais` | — | PageHeader, StateBox, PanelCard, InfoGrid |
| `strategic-indicators` | — | PageHeader, InfoState, LoadingActivityInline, ContentCard | `operationalUnitLabels` |
| `controle-retrabalhos` | — | KpiCard, ChartCard, LoadingActivity |
| `financeiro-centro-custo` | — | ChartCard, KpiCard, EmptyState, LoadingState |
| `auditoria-5s` | — | ChartCard |

## Referência — `cadastro-kaizen` (migração UI concluída)

Documento canônico do plugin: [cadastro-kaizen/docs/UI-PLUGIN-UI.md](../../cadastro-kaizen/docs/UI-PLUGIN-UI.md).

| Camada | Exports plugin-ui | Wrapper local |
|--------|-------------------|---------------|
| Help | `HelpTooltip`, `FieldLabel` (via factories) | — |
| Formulário | `createDashboardNativeFormFields`, `DateField`, `FormGrid`, `FormActions` | `components/ui/kzFormFields`, `DateField`, `FormGrid` |
| Filtros | `createDashboardFiltersKit` (+ `FilterSelectField`) | `FiltersKit.ts` |
| KPI dashboard | `createKaizenKpiCard` | `KpiCard.tsx` |
| Seções | `SectionCard`, `EditableSectionCard` | `SectionCard`, `EditableSectionCard` |
| Lista/tabela | `createDashboardDataTableKit`, Pagination | `components/data/dataTableUi.ts` |
| Multiselect | `createDashboardMultiSelectField`, creatable | `MultiSelectField`, `CategoryMultiSelectField` |
| Feedback | `createDashboardStateBanner`, `PageHeader` | `StateAlert`, `KaizenPageHeader` |
| Evidências | `createDashboardFileDropzone` | `KaizenEvidenceDropzone` |
| Modal | `createModalShell` | `Modal.tsx` |

Commits de referência (jul/2026): série `refactor(cadastro-kaizen): … via plugin-ui` até `refactor(cadastro-kaizen): concluir migração UI para @delpi/plugin-ui`.
