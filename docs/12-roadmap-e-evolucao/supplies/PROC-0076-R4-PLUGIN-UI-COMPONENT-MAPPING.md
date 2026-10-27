# PROC-0076.R4 — Mapeamento `@delpi/plugin-ui`: Inteligência de Mercado

> **Status:** INVENTÁRIO VERIFICADO contra HEAD `8b9003f438` (2026-10-26). Nomes de exports são os reais do HEAD — os títulos conceituais do briefing (PerspectiveSwitcher etc.) mapeiam para exports existentes ou composições locais conforme classificação.
> **Classificações:** `REUSE_EXISTING` (export pronto), `COMPOSE_EXISTING` (combinação de exports existentes), `LOCAL_FEATURE_COMPONENT` (componente da feature, sem pretensão de kit), `SHARED_KIT_CANDIDATE` (candidato a kit só com justificativa e consulta), `TO_INVENTORY` (lacuna a investigar).
> **Instanciação:** os portais consomem o kit via fábricas `createDashboard*` com prefixo BEM (`sp`) — wrappers existem em `plugins/supplies/src/app/suppliesUi.ts`. Regra: nunca instanciar `create*` fora do wrapper.

## 1. Inventário por responsabilidade

| Conceito (briefing) | Export real / composição | Origem | Classificação |
|---|---|---|---|
| PagePath / breadcrumb | `SuppliesPagePath` = `createDashboardPagePath({prefix:"sp", portalScopeClassName:"dashboard-supplies-portal"})` | `plugin-ui/src/components/layout/PagePath.tsx` → `suppliesUi.ts` | REUSE_EXISTING |
| PageHero | `SuppliesPageHero` = `createDashboardPageHero` + `density:"compact"`; props: `eyebrow,title,description,badge,actions,highlights,children` | `layout/PageHero.tsx` → `suppliesUi.ts` | REUSE_EXISTING |
| PerspectiveSwitcher (Metais/Câmbio/Indicadores) | `SuppliesSegmentToggle` = `createDashboardSegmentToggle("sp")`; props: `options:{value,label,ariaLabel,disabled}[], value, onChange, ariaLabel, size, widthMode:"fill"\|"content", direction` | `forms/SegmentToggle.tsx` → `suppliesUi.ts` | REUSE_EXISTING |
| MetalSelectionCard (cards selecionáveis) | **Sem export equivalente** — `InteractiveDataCard` (`data/InteractiveDataCard.tsx`) é card de navegação (`onActivate`/`openHint`, sem `aria-pressed`/checkbox semantics); `MetricStrip`/KPI tiles aceitam `active`+`aria-pressed` mas são tiles de KPI, não seleção de instrumento | gap → Doc D | LOCAL_FEATURE_COMPONENT (primeira opção) / SHARED_KIT_CANDIDATE (se ≥2 features precisarem) |
| FrequencySwitcher (Dia/Semana/Mês/Ano) | `SuppliesSegmentToggle` com `ChartGranularity="day"\|"week"\|"month"\|"year"` | `forms/SegmentToggle.tsx`, `types/chartGranularity.ts` | REUSE_EXISTING |
| KPI Strip | Opção A: `SuppliesDataCardsGrid` + `SuppliesKpiCard` (`createDashboardKpiCard`); Opção B: `createDashboardMetricStrip` (`layout/MetricStrip.tsx`, items `PageHeroHighlight{id,label,value,description,tone,loading,onSelect,active,ariaLabel}`) — export disponível, ainda sem wrapper supplies | `layout/DelpiKpiCard.tsx`, `layout/MetricStrip.tsx`, `data/DataCardsGrid.tsx` | REUSE_EXISTING |
| ViewSwitcher (Gráfico/Tabela/Comparação) | `SuppliesSegmentToggle` (opções com ícone + `ariaLabel`; opção Comparação usa `disabled`) | `forms/SegmentToggle.tsx` | REUSE_EXISTING |
| ChartPanel | `MultiTypeSeriesChart` (`data,categoryKey,series:MultiTypeSeriesSpec[],chartType,height,formatY,formatTooltipValue,showLegend,incompleteBucketMode,bucketFractionKey,...`) dentro de `ChartViewShell` (slots: `granularity,overlays,seriesColors,typeToggle,exportActions,extra`) + `StableResponsiveContainer` | `charts/MultiTypeSeriesChart.tsx`, `charts/ChartViewShell.tsx`, `charts/StableResponsiveContainer.tsx` | COMPOSE_EXISTING (já composto no R3 `MarketIntelligencePanel`) |
| TablePanel | `SuppliesDataTable` = `DataTable` + classNames/labels `sp`; props `columns:DataTableColumn[],rows`, sort/paginação via `SuppliesCompactPagination`, visibilidade via `TableColumnVisibilityMenu` | `data/DataTable.tsx` → `suppliesUi.ts` | REUSE_EXISTING |
| ComparisonPanel | Sem composição dedicada: = `MultiTypeSeriesChart` com N `MultiTypeSeriesSpec` (mesma unidade/granularidade) ou `CompareSparkline` para micro-comparativos | `charts/MultiTypeSeriesChart.tsx`, `data/CompareSparkline.tsx` | COMPOSE_EXISTING |
| EmptyState | `SuppliesEmptyState` (card com título) / `SuppliesInlineEmptyState` (message-only); `SoftEmptyState` e `InfoStatePanel` (`createInfoStatePanel`) para variantes contextuais | `feedback/EmptyState.tsx`, `feedback/SoftEmptyState.tsx`, `feedback/InfoStatePanel.tsx` | REUSE_EXISTING |
| SourceStatus (disponibilidade/cobertura) | `SuppliesStatusBadge` (`variant:neutral\|info\|success\|warning\|danger`) + `SuppliesStateBanner` (`variant:default\|error\|success`, `role="status"`) | `feedback/StatusBadge.tsx`, `feedback/StateBanner.tsx` | REUSE_EXISTING |
| FilterControls | `SuppliesFilterBarShell` (`createFilterBarShell`, `withGrid`), `FiltersRow`, `SuppliesSelectField`, `SuppliesMultiSelectField`, `SuppliesDateField`, `SuppliesQuickPeriodSelector`, `SuppliesFilterCheckbox(Field)` | `layout/FilterBarShell.tsx`, `layout/FiltersRow.tsx`, `forms/*`, `layout/QuickPeriodSelector.tsx` | REUSE_EXISTING |
| Help/Tooltip | `HelpTooltip` (`placement,trigger`) + `SuppliesTitleWithHelp` + `SectionHintLabel`; conteúdo em `plugins/supplies/src/content/helpTooltips.ts` | `help/HelpTooltip.tsx`, `help/TitleWithHelp.tsx`, `help/SectionHintLabel.tsx` | REUSE_EXISTING |
| ExportControls | `SuppliesTabularExportButtons` = `createDashboardTabularExportButtons` (CSV/XLSX/PDF — `TabularExportFormat`); `ExcelExportButton` e `runTabularExport` para custom | `export/ExportButtons.tsx`, `export/runTabularExport.ts`, `export/types.ts` | REUSE_EXISTING |
| Loading skeleton | `SuppliesLoadingCard` (`createDashboardLoadingActivityCard`) + `LoadingState`/`createDashboardLoadingState` | `feedback/LoadingActivityCard.tsx`, `feedback/EmptyState.tsx` | REUSE_EXISTING |
| Hero refresh/favorite | `SuppliesActionButton` (`ActionButton`), `LoadingActivityBadge` | `actions/ActionButton.tsx` | REUSE_EXISTING |
| Error boundary | `PluginErrorBoundary` | `feedback/PluginErrorBoundary.tsx` | REUSE_EXISTING |

## 2. Lacunas funcionais (TO_INVENTORY)

| Lacuna | Evidência | Decisão recomendada |
|---|---|---|
| Card multi-seleção com `aria-pressed`/`role="checkbox"` + check visual + estado de disponibilidade | Nenhum export cobre "selectable option card"; `InteractiveDataCard` é nav-card | `LOCAL_FEATURE_COMPONENT` em `features/market-intelligence/` (ex.: `MarketInstrumentCard`) sobre tokens `--sp-*`; promover a `SHARED_KIT_CANDIDATE` apenas se segunda feature pedir |
| Granularidade `week` no contrato BFF | Kit tipa `"week"` (`types/chartGranularity.ts`); `MarketGranularity` no MFE = `"day"\|"month"\|"year"` (`api.ts`) | `TO_INVENTORY` — owner `supplies-api`/`external-data-api`; decisão de produto antes de implementar |
| Tipo de boletim PTAX além de fechamento | Contrato atual: `ptax_closing_sell`/`ptax_closing_buy` | `TO_INVENTORY` — depende do producer BCB |
| Comparação cross-perspectiva | Sem contrato de comparação homologado entre fontes | `TO_INVENTORY` — permanece desabilitado até metodologia |
| Catálogo de metais selecionáveis | Produção: nenhum metal com `display_allowed` (LME quarentenado) | `TO_INVENTORY` — gate de direitos, não UI |

## 3. Tokens e tokens-adjacentes usados pelos componentes mapeados

Os componentes consomem `var(--delpi-ui-*)` que `plugins/supplies/src/index.css` encadeia a `--sp-*` e ao escopo global (`--primary`, `--surface`, `--border`, `--text`). Nenhum valor hex arbitrário deve aparecer na feature — ver Doc A §11 e Doc C §tokens.

## 4. Uso existente (evidência de precedente)

- `MarketIntelligencePage.tsx`/`MarketIntelligencePanel.tsx` (R3, em produção): `SuppliesPagePath`, `SuppliesPageHero`, `SuppliesSegmentToggle` (perspectiva + modo), `SuppliesSelectField`, `SuppliesDateField`, `SuppliesStateBanner`, `SuppliesStatusBadge`, `SuppliesLoadingCard`, `SuppliesDataCardsGrid`+`SuppliesKpiCard`, `SuppliesDataTable`, `SuppliesEmptyState`, `SuppliesTabularExportButtons`, `MultiTypeSeriesChart`.
- `FiltersRow` (variant `extended`) já usado dentro do hero.
- Chart toolbar kit (`createDashboardChartToolbarKit`) instanciado em supplies (`SuppliesChartGranularityToggle`) — precedente para o FrequencySwitcher.

## 5. Regra de reuso (gate)

Antes de qualquer componente novo: (1) existe export pronto? (2) composição de exports existentes resolve? (3) é de fato específico da feature? Só depois (4) candidato a kit com consulta prévia — nunca criar componente compartilhado sem esse funil (regra `plugins-reusable-components`).
