import type {
  ComunicadoBlock,
  ComunicadoCanvasTableBlock,
  ComunicadoChartViewBlock,
  ComunicadoInputBlock,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { CanvasTableSelectionFloatToolbar } from "./CanvasTableSelectionFloatToolbar";
import { ChartSelectionFloatToolbar } from "./ChartSelectionFloatToolbar";
import { InputSelectionFloatToolbar } from "./InputSelectionFloatToolbar";
import { KpiSelectionFloatToolbar } from "./KpiSelectionFloatToolbar";
import { TableSelectionFloatToolbar } from "./TableSelectionFloatToolbar";

/**
 * Dispatcher da float toolbar para visuais complexos (chart / kpi / table / Grade / filtro).
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
  if (block.type === "canvas_table") {
    return <CanvasTableSelectionFloatToolbar block={block as ComunicadoCanvasTableBlock} />;
  }
  if (block.type === "input") {
    return <InputSelectionFloatToolbar block={block as ComunicadoInputBlock} />;
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
  selectedInputPart?: unknown;
}): boolean {
  const { block, isPrimary, selectedIdsLength } = params;
  if (!isPrimary || selectedIdsLength !== 1) return false;
  if (block.type === "chart_view") return !params.selectedChartPart;
  if (block.type === "kpi_view") return !params.selectedKpiPart;
  if (block.type === "table_view") return !params.selectedTablePart;
  if (block.type === "canvas_table") return true;
  if (block.type === "input") return !params.selectedInputPart;
  return false;
}
