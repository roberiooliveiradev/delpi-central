# Chart View Shell — inventário e famílias

Shell canônico do kit para controles densos (tipo de gráfico, overlays YoY/tendência), preferências em `localStorage` (mesmo padrão de `usePersistedViewLayout`) e plot Recharts multi-tipo.

Consumidor desta onda: **Portal Commercial** (`plugins/commercial`). Dashboard Comercial fica fora.

## Famílias → tipos permitidos

| Família (`ChartDataFamily`) | Tipos | Default típico | Pizza |
|-----------------------------|-------|----------------|-------|
| `time_multi_series` | `column`, `line`, `area` | `column` ou `line` | Não |
| `period_compare` | `column`, `line`, `area` | `column` | Não |
| `ranking` | `horizontal_bar`, `bar`, `pie` (≤12 categorias) | `horizontal_bar` | Sim se ≤12 |
| `composition` | `stacked_bar` | `stacked_bar` | Não |
| `categorical` | `bar` | `bar` | Não |
| `funnel` / `scalar` / `mini` | — (sem type switcher) | — | — |

## Inventário Portal Commercial

| Gráfico | Família | Excel | Preferências |
|---------|---------|-------|--------------|
| `AnalyticsRolSeriesChart` | `time_multi_series` | Sim (CSV/XLS/PDF) | type, yoy, trend, seriesFills |
| `AnalyticsClosingRateSeriesChart` | `time_multi_series` | Sim | type, yoy, seriesFills |
| `CustomerBillingSeriesChart` | `time_multi_series` | Sim | type, yoy/+2/+3, trend, seriesFills |
| `CustomerAccountBillingChart` | `time_multi_series` | Sim | type, trend, seriesFills |
| `CustomerPurchaseEvolutionChart` | `period_compare` | Sim | type, trend, seriesFills |
| `AnalyticsOtdInsightBarChart` | `ranking` | Sim | type (cores por severidade — sem seriesFills) |
| OP coverage / prazo (`OpenOrdersProductionDetailContent`) | `composition` / `categorical` | Sim | — (export; type switcher N/A nesta onda) |
| `AnalyticsFunnelChart` | `funnel` | Sim | — |
| Gauges OTD / sparkline ranking | `scalar` / `mini` | N/A | — |

## Gate Excel

Teste estrutural: `plugins/commercial/src/features/analytics/chartExcelCoverage.structural.test.mjs` — cada gráfico do inventário (exceto `scalar`/`mini`) menciona `runTabularExport`, `ExcelExportButton` ou `CommercialTabularExportButtons`.

## APIs do kit

| Peça | Módulo |
|------|--------|
| Preferências | `usePersistedChartPreferences` (`seriesFills` por `dataKey`) |
| Type switcher | `ChartTypeSegmentToggle` (ícone + popover `ChartTypeCatalogPanel` filtrado por família) |
| Overlay options | `ChartOverlayOptionsPopover` + `buildCompareYearsOverlayOptions` (YoY / tendência) |
| Series colors | `ChartSeriesColorsPopover` (host fino sobre `ColorPickerPopover`) + `applySeriesFillPreferences` |
| Plot | `MultiTypeSeriesChart` |
| Shell | `ChartViewShell` — **mesma linha:** Agrupamento · Opções · Cores · Tipo · export |
| Checkbox compacto | `NativeCheckboxControl` `hintPlacement: "tooltip"` (help no **label**, sem ícone `?`) |
