import type {
  ComunicadoBlock,
  ComunicadoChartViewBlock,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { ChartSelectionFloatToolbar } from "./ChartSelectionFloatToolbar";
import { KpiSelectionFloatToolbar } from "./KpiSelectionFloatToolbar";
import { TableSelectionFloatToolbar } from "./TableSelectionFloatToolbar";

/**
 * Dispatcher da float toolbar para visuais de dados (chart / kpi / table).
 * Retorna null para tipos sem float.
 */
export function ComplexViewFloatToolbar({ block }: { block: ComunicadoBlock }) {
  if (block.type === "chart_view") {
    return <ChartSelectionFloatToolbar block={block as ComunicadoChartViewBlock} />;
  }
  if (block.type === "kpi_view") {
    return <KpiSelectionFloatToolbar block={block as ComunicadoKpiViewBlock} />;
  }
  if (block.type === "table_view") {
    return <TableSelectionFloatToolbar block={block as ComunicadoTableViewBlock} />;
  }
  return null;
}

export function shouldShowComplexViewFloatToolbar(params: {
  block: ComunicadoBlock;
  isPrimary: boolean;
  selectedIdsLength: number;
  selectedChartPart: unknown;
  selectedKpiPart: unknown;
  selectedTablePart: unknown;
}): boolean {
  const { block, isPrimary, selectedIdsLength } = params;
  if (!isPrimary || selectedIdsLength !== 1) return false;
  if (block.type === "chart_view") return !params.selectedChartPart;
  if (block.type === "kpi_view") return !params.selectedKpiPart;
  if (block.type === "table_view") return !params.selectedTablePart;
  return false;
}
