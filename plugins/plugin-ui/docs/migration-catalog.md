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
| `cadastro-kaizen` | — | ✅ Migrado | `FieldLabel` + tokens `--delpi-ui-*` |
| `eficiencia-fabril` | — | ✅ Migrado | |
| `transformometro` | — | ✅ Migrado | `TableHeader` local (tabelas HTML) |
| `quality-action-plans` | — | ✅ Migrado | `TitleWithHelp` / `TableHeaderCell` locais (UX com ícone `?`) |
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
| `MultiSelectField` | 13 | F2 ✅ (8 dept. + lmps) |
| `FilterBar` | 12 | F2 ✅ (FiltersRow + FilterInputField) |
| `DataTable` / `DataTableSection` | ~25 | F2 ✅ (7 dept. + lmps DataTable) |
| `DetailFieldGrid` | 5 | F3 ✅ (5 consumidores) |
| `EditableSectionCard` | 3 | F3 ✅ |
| `ReadOnlyField` | 2 | F3 ✅ |
| `SelectField` | 2 | F3 ✅ |
| `PageHeader` | 7 | F3 ✅ |
| `DetailCard` | 3 | F3 ✅ |
| `SectionCard` | 1 (PAC) | F3 ✅ |
| `EmptyState` / `LoadingState` | 2 | F3 ✅ |

## Status — Fase 4 (utilitários)

| Utilitário | Consumidores | Notas |
|------------|--------------|-------|
| `paginationPages` | plugin-ui Pagination | ✅ desde F2.4 |
| `chartColors` | 8 dashboards + transformometro + PAC | Paletas `DEPARTMENTAL`, `LMPS`, `CSS_VARS` |
| `operationalUnitLabels` | 8 dashboards | Filiais 01/02 TOTVS |
| `goalDisplay` | 8 dashboards | Badges IDD / meta KPI |

Reexport local: `export * from "../../../plugin-ui/src/utils/goalDisplay"` (imports existentes preservados).

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
| `dashboard-lmps` | — | ✅ | ✅ | ✅ | ✅ | ✅ | Pagination simplificado (local) |
| `transformometro` | — | — | — | — | ✅ | |
| `eficiencia-fabril` | — | — | — | — | ✅ | |
| `inspecoes-entrada` | — | — | — | — | — | — | `@delpi/plugin-ui` + PageHeader F3 |
| `controle-retrabalhos` | — | — | — | — | — | — | `@delpi/plugin-ui` + Empty/Loading F3 |

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
| `pedidos-venda-abertos` | — | PageHeader |
| `inspecoes-entrada` | — | PageHeader |
| `propostas-comerciais` | — | PageHeader |
| `strategic-indicators` | — | PageHeader |
| `controle-retrabalhos` | — | EmptyState, LoadingState |
| `financeiro-centro-custo` | — | EmptyState, LoadingState |
