import {
  chartPartAllowsEdit,
  getChartPartState,
  getKpiPartState,
  isChartTextPartKind,
  resolveChartPartFontSize,
  resolveKpiPartFontSize,
  defaultStyle,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoKpiPartRef,
} from "@delpi/tv-dashboard-presentation";

import {
  chartPartSelectionLabel,
  kpiPartSelectionLabel,
} from "./resolveSelectionChromeMode";

/** Subconjunto tipográfico compartilhado entre bloco de texto e parts KPI/chart. */
export type TextFormatStyleSnapshot = {
  fontFamily?: string;
  fontSize?: number;
  fontWeight?: string;
  fontStyle?: string;
  color?: string;
  textDecoration?: string;
  textHighlight?: string;
  textAlign?: string;
  verticalAlign?: string;
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  textReflection?: boolean;
};

export type SelectedTextFormatTarget =
  | {
      mode: "block";
      blockId: string;
      blockType: "heading" | "text" | "shape";
      style: TextFormatStyleSnapshot;
      textAlign?: string;
      verticalAlign?: string;
    }
  | {
      mode: "part";
      source: "kpi" | "chart";
      blockId: string;
      partLabel: string;
      style: TextFormatStyleSnapshot;
      textAlign?: string;
      verticalAlign?: string;
    };

const KPI_TEXT_FORMAT_KINDS = new Set(["title", "hint", "value"]);
const CHART_TEXT_FORMAT_KINDS = new Set(["title", "legend", "axisTitle", "dataLabel", "axis"]);

export function isKpiTextFormatPart(part: ComunicadoKpiPartRef | null | undefined): boolean {
  return Boolean(part && KPI_TEXT_FORMAT_KINDS.has(part.kind));
}

export function isChartTextFormatPart(part: ComunicadoChartPartRef | null | undefined): boolean {
  if (!part) return false;
  if (!CHART_TEXT_FORMAT_KINDS.has(part.kind)) return false;
  // axis/dataLabel: tipografia mesmo quando editable=false em alguns kinds
  if (part.kind === "axis" || part.kind === "dataLabel") return true;
  return chartPartAllowsEdit(part);
}

/** Alvo tipográfico admite seção Parágrafo (alinhamento H/V). */
export function textFormatTargetSupportsParagraphAlign(
  target: SelectedTextFormatTarget | null | undefined,
): boolean {
  return Boolean(target);
}

/**
 * Resolve onde a ribbon Formatar / tipografia deve gravar o estilo.
 * Bloco text/heading/shape OU parte textual de kpi_view / chart_view.
 */
export function resolveSelectedTextFormatTarget(params: {
  selected: ComunicadoBlock | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
}): SelectedTextFormatTarget | null {
  const { selected, selectedKpiPart = null, selectedChartPart = null } = params;
  if (!selected) return null;

  if (selected.type === "heading" || selected.type === "text") {
    const defaults = defaultStyle(selected.type);
    return {
      mode: "block",
      blockId: selected.id,
      blockType: selected.type,
      style: {
        fontFamily: selected.style?.fontFamily,
        fontSize: selected.style?.fontSize ?? defaults.fontSize,
        fontWeight: selected.style?.fontWeight,
        fontStyle: selected.style?.fontStyle,
        color: selected.style?.color,
        textDecoration: selected.style?.textDecoration,
        textHighlight: selected.style?.textHighlight,
        textAlign: selected.style?.textAlign,
        verticalAlign: selected.style?.verticalAlign,
        textShadow: selected.style?.textShadow,
        textStrokeColor: selected.style?.textStrokeColor,
        textStrokeWidth: selected.style?.textStrokeWidth,
        textReflection: selected.style?.textReflection,
      },
      textAlign: selected.style?.textAlign,
      verticalAlign: selected.style?.verticalAlign,
    };
  }

  if (selected.type === "shape") {
    const defaults = defaultStyle("shape", selected.shape);
    return {
      mode: "block",
      blockId: selected.id,
      blockType: "shape",
      style: {
        fontFamily: selected.style?.fontFamily,
        fontSize: selected.style?.fontSize ?? defaults.fontSize,
        fontWeight: selected.style?.fontWeight,
        fontStyle: selected.style?.fontStyle,
        color: selected.style?.color,
        textDecoration: selected.style?.textDecoration,
        textAlign: selected.style?.textAlign,
        verticalAlign: selected.style?.verticalAlign,
        textShadow: selected.style?.textShadow,
        textStrokeColor: selected.style?.textStrokeColor,
        textStrokeWidth: selected.style?.textStrokeWidth,
        textReflection: selected.style?.textReflection,
      },
      textAlign: selected.style?.textAlign,
      verticalAlign: selected.style?.verticalAlign,
    };
  }

  if (selected.type === "kpi_view" && isKpiTextFormatPart(selectedKpiPart) && selectedKpiPart) {
    const partStyle = getKpiPartState(selected.kpiParts, selectedKpiPart)?.style;
    const kind = selectedKpiPart.kind as "title" | "value" | "hint";
    return {
      mode: "part",
      source: "kpi",
      blockId: selected.id,
      partLabel: kpiPartSelectionLabel(selectedKpiPart),
      style: {
        fontFamily: partStyle?.fontFamily,
        fontSize: resolveKpiPartFontSize(kind, partStyle),
        fontWeight:
          partStyle?.fontWeight != null ? String(partStyle.fontWeight) : undefined,
        fontStyle: partStyle?.fontStyle,
        color: partStyle?.color,
        textDecoration: partStyle?.textDecoration,
        textAlign: partStyle?.textAlign,
        verticalAlign: partStyle?.verticalAlign,
        textShadow: partStyle?.textShadow,
        textStrokeColor: partStyle?.textStrokeColor,
        textStrokeWidth: partStyle?.textStrokeWidth,
        textReflection: partStyle?.textReflection,
      },
      textAlign: partStyle?.textAlign,
      verticalAlign: partStyle?.verticalAlign,
    };
  }

  if (selected.type === "chart_view" && isChartTextFormatPart(selectedChartPart) && selectedChartPart) {
    const partStyle = getChartPartState(selected.chartParts, selectedChartPart)?.style;
    const kind = isChartTextPartKind(selectedChartPart.kind) ? selectedChartPart.kind : null;
    return {
      mode: "part",
      source: "chart",
      blockId: selected.id,
      partLabel: chartPartSelectionLabel(selectedChartPart),
      style: {
        fontFamily: partStyle?.fontFamily,
        fontSize: kind ? resolveChartPartFontSize(kind, partStyle) : partStyle?.fontSize,
        fontWeight: partStyle?.fontWeight,
        fontStyle: partStyle?.fontStyle,
        color: partStyle?.color,
        textAlign: partStyle?.textAlign,
        verticalAlign: partStyle?.verticalAlign,
        textShadow: partStyle?.textShadow,
        textStrokeColor: partStyle?.textStrokeColor,
        textStrokeWidth: partStyle?.textStrokeWidth,
        textReflection: partStyle?.textReflection,
      },
      textAlign: partStyle?.textAlign,
      verticalAlign: partStyle?.verticalAlign,
    };
  }

  return null;
}
