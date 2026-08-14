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

| Gráfico | Família | Excel (antes do shell) | Preferências alvo |
|---------|---------|------------------------|-------------------|
| `AnalyticsRolSeriesChart` | `time_multi_series` | Sim (CSV/XLS/PDF) | type, yoy, trend |
| `AnalyticsClosingRateSeriesChart` | `time_multi_series` | Sim | type, yoy |
| `CustomerBillingSeriesChart` | `time_multi_series` | **Falta** | type, yoy/+2/+3, trend |
| `CustomerAccountBillingChart` | `time_multi_series` | **Falta** | type, trend |
| `CustomerPurchaseEvolutionChart` | `period_compare` | **Falta** | type, trend |
| `AnalyticsOtdInsightBarChart` | `ranking` | **Falta** | type |
| OP coverage / prazo (`OpenOrdersProductionDetailContent`) | `composition` / `categorical` | **Falta** | type se couber |
| `AnalyticsFunnelChart` | `funnel` | Sim | — |
| Gauges OTD / sparkline ranking | `scalar` / `mini` | N/A | — |

## Gaps Excel (obrigatório nesta onda)

Todos os itens marcados **Falta** devem passar a exportar via `runTabularExport` + `ExcelExportButton` ou `TabularExportButtons`.

## APIs do kit (alvo)

| Peça | Módulo |
|------|--------|
| Preferências | `usePersistedChartPreferences` |
| Type switcher | `ChartTypeSegmentToggle` + `chartDataFamilies` |
| Plot | `MultiTypeSeriesChart` |
| Shell | `ChartViewShell` |
| Checkbox compacto | `NativeCheckboxControl` `hintPlacement: "tooltip"` |

## Critério de pronto (Excel)

Gate estrutural: cada gráfico do inventário (exceto `scalar`/`mini`) menciona `runTabularExport` ou `ExcelExportButton`.
