/**
 * Re-export canônico — tamanho da float toolbar (KPI / gráfico / tabela).
 * Mantém aliases `chart*` para consumidores legados.
 */
export {
  chartFrameShortSidePx,
  complexFrameShortSidePx,
  resolveChartFloatToolbarMetrics,
  resolveComplexFloatToolbarMetrics,
  type ChartFloatToolbarMetrics,
  type ComplexFloatToolbarMetrics,
} from "./complexFloatToolbarSize";
