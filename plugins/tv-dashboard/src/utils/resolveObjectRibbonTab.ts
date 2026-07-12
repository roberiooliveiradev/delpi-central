import { BarChart3, LayoutTemplate, Paintbrush, Shapes } from "lucide-react";
import {
  chartPartVisualPrimitive,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoKpiPartRef,
} from "@delpi/tv-dashboard-presentation";

import { resolveSelectedTextFormatTarget } from "../utils/selectedTextFormatTarget";
import type { ComunicadoRibbonTabRequest } from "../components/comunicadoEditorContextCore";

/**
 * Resolve a aba contextual correta após remoção de «Formatar».
 * Tipografia e chrome ficam na aba do objeto (Forma / Gráfico / Tabela).
 */
export function resolveObjectRibbonTab(params: {
  selected: ComunicadoBlock | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  preferred?: ComunicadoRibbonTabRequest | null;
}): ComunicadoRibbonTabRequest {
  const { selected, selectedChartPart = null, selectedKpiPart = null, preferred } = params;
  if (
    preferred &&
    preferred !== "format" &&
    preferred !== "insert" &&
    preferred !== "view"
  ) {
    return preferred;
  }

  if (!selected) return "shape";

  if (selected.type === "chart_view") {
    const primitive = selectedChartPart
      ? chartPartVisualPrimitive(selectedChartPart)
      : null;
    const textTarget = resolveSelectedTextFormatTarget({
      selected,
      selectedChartPart,
      selectedKpiPart,
    });
    if (primitive && (!textTarget || textTarget.mode !== "part" || selectedChartPart?.kind === "axis")) {
      return "shape";
    }
    return "chart";
  }

  if (selected.type === "table_view") return "table";
  if (selected.type === "kpi_view") return "shape";
  if (
    selected.type === "shape" ||
    selected.type === "heading" ||
    selected.type === "text" ||
    selected.type === "image" ||
    selected.type === "video"
  ) {
    return "shape";
  }
  if (
    selected.type === "data_source" ||
    selected.type.startsWith("data_")
  ) {
    return "data";
  }
  return "shape";
}

/** Ícones legados — mantidos para imports que ainda referenciam Formatar. */
export const LEGACY_FORMAT_TAB_ICON = Paintbrush;
export const OBJECT_RIBBON_ICONS = {
  shape: Shapes,
  chart: BarChart3,
  table: LayoutTemplate,
} as const;
