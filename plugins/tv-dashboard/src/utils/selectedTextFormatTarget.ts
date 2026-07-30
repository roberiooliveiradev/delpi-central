import {
  CHART_PART_FONT_SIZE_DEFAULTS,
  KPI_PART_FONT_SIZE_DEFAULTS,
  INPUT_PART_FONT_SIZE_DEFAULTS,
  KPI_TEXT_PART_KINDS,
  TABLE_VIEW_DEFAULT_FONT_SIZE_PX,
  chartPartAllowsEdit,
  getChartPartState,
  getInputPartState,
  getKpiPartState,
  getTablePartState,
  isChartTextPartKind,
  isInputTextPartKind,
  kpiPartUsesAutoFitFont,
  mergeComunicadoTableOptions,
  resolveCanvasTableFontSize,
  resolveChartPartFontSize,
  resolveInputPartFontSize,
  resolveKpiPartFontSize,
  type ComunicadoBlock,
  type ComunicadoCanvasTableBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartViewBlock,
  type ComunicadoInputBlock,
  type ComunicadoInputPartRef,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiViewBlock,
  type ComunicadoTablePartRef,
  type ComunicadoTableViewBlock,
} from "@delpi/tv-dashboard-presentation";

import {
  chartPartSelectionLabel,
  inputPartSelectionLabel,
  kpiPartSelectionLabel,
  tablePartSelectionLabel,
} from "./resolveSelectionChromeMode";

/** Subconjunto tipográfico compartilhado entre bloco de texto e parts KPI/chart/tabela/input. */
export type TextFormatStyleSnapshot = {
  fontFamily?: string;
  fontSize?: number;
  /** KPI: tipografia automática (FitText) — UI mostra «Auto». */
  fontSizeAuto?: boolean;
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

export type ComplexTextFormatSource =
  | "table"
  | "chart"
  | "kpi"
  | "input"
  | "canvas_table";

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
      source: "kpi" | "chart" | "input" | "table";
      blockId: string;
      partLabel: string;
      style: TextFormatStyleSnapshot;
      textAlign?: string;
      verticalAlign?: string;
    }
  | {
      /** Bloco complexo sem parte textual — tipografia global (paridade Fonte da tabela). */
      mode: "complexGlobal";
      source: ComplexTextFormatSource;
      blockId: string;
      partLabel: string;
      style: TextFormatStyleSnapshot;
      textAlign?: string;
      verticalAlign?: string;
    };

const KPI_TEXT_FORMAT_KINDS = new Set<string>(KPI_TEXT_PART_KINDS);
const CHART_TEXT_FORMAT_KINDS = new Set([
  "title",
  "legend",
  "axisTitle",
  "dataLabel",
  "dataLabels",
  "axis",
  "axes",
]);
const TABLE_TEXT_FORMAT_KINDS = new Set(["title", "header", "headerCell", "cell", "row"]);

export function isKpiTextFormatPart(part: ComunicadoKpiPartRef | null | undefined): boolean {
  return Boolean(part && KPI_TEXT_FORMAT_KINDS.has(part.kind));
}

export function isChartTextFormatPart(part: ComunicadoChartPartRef | null | undefined): boolean {
  if (!part) return false;
  if (!CHART_TEXT_FORMAT_KINDS.has(part.kind)) return false;
  if (
    part.kind === "axis" ||
    part.kind === "axes" ||
    part.kind === "dataLabel" ||
    part.kind === "dataLabels"
  ) {
    return true;
  }
  return chartPartAllowsEdit(part);
}

export function isInputTextFormatPart(part: ComunicadoInputPartRef | null | undefined): boolean {
  return Boolean(part && isInputTextPartKind(part.kind));
}

export function isTableTextFormatPart(part: ComunicadoTablePartRef | null | undefined): boolean {
  return Boolean(part && TABLE_TEXT_FORMAT_KINDS.has(part.kind));
}

/** Alvo tipográfico admite seção Parágrafo (alinhamento H/V). */
export function textFormatTargetSupportsParagraphAlign(
  target: SelectedTextFormatTarget | null | undefined,
): boolean {
  return Boolean(target);
}

function snapshotFromPartStyle(
  style: {
    fontFamily?: string;
    fontSize?: number;
    fontWeight?: string | number;
    fontStyle?: string;
    color?: string;
    textDecoration?: string;
    textAlign?: string;
    verticalAlign?: string;
    textShadow?: string;
    textStrokeColor?: string;
    textStrokeWidth?: number;
    textReflection?: boolean;
  } | null | undefined,
  fontSizeFallback: number,
  fontSizeAuto?: boolean,
): TextFormatStyleSnapshot {
  return {
    fontFamily: style?.fontFamily,
    fontSize: style?.fontSize != null && style.fontSize > 0 ? style.fontSize : fontSizeFallback,
    fontSizeAuto,
    fontWeight: style?.fontWeight != null ? String(style.fontWeight) : undefined,
    fontStyle: style?.fontStyle,
    color: style?.color,
    textDecoration: style?.textDecoration,
    textAlign: style?.textAlign,
    verticalAlign: style?.verticalAlign,
    textShadow: style?.textShadow,
    textStrokeColor: style?.textStrokeColor,
    textStrokeWidth: style?.textStrokeWidth,
    textReflection: style?.textReflection,
  };
}

function resolveTableGlobalStyle(block: ComunicadoTableViewBlock): TextFormatStyleSnapshot {
  const options = mergeComunicadoTableOptions(block.tableOptions, block.tablePreset);
  return {
    fontFamily: options.fontFamily,
    fontSize: options.fontSize ?? TABLE_VIEW_DEFAULT_FONT_SIZE_PX,
    fontWeight: options.fontWeight != null ? String(options.fontWeight) : undefined,
    fontStyle: options.fontStyle,
    color: options.cellTextColor,
    textAlign: options.textAlign,
  };
}

function resolveCanvasGlobalStyle(block: ComunicadoCanvasTableBlock): TextFormatStyleSnapshot {
  const style = block.style;
  return {
    fontFamily: style?.fontFamily,
    fontSize: resolveCanvasTableFontSize(block),
    fontWeight: style?.fontWeight != null ? String(style.fontWeight) : undefined,
    fontStyle: style?.fontStyle,
    color: style?.color,
    textDecoration: style?.textDecoration,
    textAlign: style?.textAlign,
    verticalAlign: style?.verticalAlign,
    textShadow: style?.textShadow,
    textStrokeColor: style?.textStrokeColor,
    textStrokeWidth: style?.textStrokeWidth,
    textReflection: style?.textReflection,
  };
}

function resolveKpiGlobalStyle(block: ComunicadoKpiViewBlock): TextFormatStyleSnapshot {
  const title = getKpiPartState(block.kpiParts, { kind: "title" })?.style;
  return snapshotFromPartStyle(title, KPI_PART_FONT_SIZE_DEFAULTS.title);
}

function resolveChartGlobalStyle(block: ComunicadoChartViewBlock): TextFormatStyleSnapshot {
  const title = getChartPartState(block.chartParts, { kind: "title" })?.style;
  return snapshotFromPartStyle(title, CHART_PART_FONT_SIZE_DEFAULTS.title);
}

function resolveInputGlobalStyle(block: ComunicadoInputBlock): TextFormatStyleSnapshot {
  const label = getInputPartState(block.inputParts, { kind: "label" })?.style;
  return snapshotFromPartStyle(label, INPUT_PART_FONT_SIZE_DEFAULTS.label);
}

/**
 * Resolve onde a ribbon Formatar / tipografia deve gravar o estilo.
 * Bloco text/heading/shape, parte textual, ou tipografia global de complexo.
 */
export function resolveSelectedTextFormatTarget(params: {
  selected: ComunicadoBlock | null;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedTablePart?: ComunicadoTablePartRef | null;
  selectedInputPart?: ComunicadoInputPartRef | null;
}): SelectedTextFormatTarget | null {
  const {
    selected,
    selectedKpiPart = null,
    selectedChartPart = null,
    selectedTablePart = null,
    selectedInputPart = null,
  } = params;
  if (!selected) return null;

  if (selected.type === "heading" || selected.type === "text") {
    const defaultsFont = selected.type === "heading" ? 56 : 28;
    return {
      mode: "block",
      blockId: selected.id,
      blockType: selected.type,
      style: snapshotFromPartStyle(selected.style, selected.style?.fontSize ?? defaultsFont),
      textAlign: selected.style?.textAlign,
      verticalAlign: selected.style?.verticalAlign,
    };
  }

  if (selected.type === "shape") {
    return {
      mode: "block",
      blockId: selected.id,
      blockType: "shape",
      style: snapshotFromPartStyle(selected.style, selected.style?.fontSize ?? 18),
      textAlign: selected.style?.textAlign,
      verticalAlign: selected.style?.verticalAlign,
    };
  }

  if (selected.type === "kpi_view") {
    if (isKpiTextFormatPart(selectedKpiPart) && selectedKpiPart) {
      const partStyle = getKpiPartState(selected.kpiParts, selectedKpiPart)?.style;
      const kind = selectedKpiPart.kind as "title" | "value" | "hint" | "comparison";
      const fontSizeAuto = kpiPartUsesAutoFitFont(kind, partStyle);
      const style = snapshotFromPartStyle(
        partStyle,
        resolveKpiPartFontSize(kind, partStyle),
        fontSizeAuto,
      );
      return {
        mode: "part",
        source: "kpi",
        blockId: selected.id,
        partLabel: kpiPartSelectionLabel(selectedKpiPart),
        style,
        textAlign: style.textAlign,
        verticalAlign: style.verticalAlign,
      };
    }
    const style = resolveKpiGlobalStyle(selected);
    return {
      mode: "complexGlobal",
      source: "kpi",
      blockId: selected.id,
      partLabel: "Texto do KPI",
      style,
      textAlign: style.textAlign,
      verticalAlign: style.verticalAlign,
    };
  }

  if (selected.type === "chart_view") {
    if (isChartTextFormatPart(selectedChartPart) && selectedChartPart) {
      /* Grupo «Eixos»: tipografia da ribbon aplica só a axis:x/y — snapshot a partir do X. */
      const styleSourceRef =
        selectedChartPart.kind === "axes"
          ? ({ kind: "axis", axis: "x" } as const)
          : selectedChartPart;
      const partStyle = getChartPartState(selected.chartParts, styleSourceRef)?.style;
      const kind =
        selectedChartPart.kind === "axes"
          ? ("axis" as const)
          : isChartTextPartKind(selectedChartPart.kind)
            ? selectedChartPart.kind
            : null;
      const style = snapshotFromPartStyle(
        partStyle,
        kind ? resolveChartPartFontSize(kind, partStyle) : (partStyle?.fontSize ?? 16),
      );
      return {
        mode: "part",
        source: "chart",
        blockId: selected.id,
        partLabel: chartPartSelectionLabel(selectedChartPart),
        style,
        textAlign: style.textAlign,
        verticalAlign: style.verticalAlign,
      };
    }
    const style = resolveChartGlobalStyle(selected);
    return {
      mode: "complexGlobal",
      source: "chart",
      blockId: selected.id,
      partLabel: "Texto do gráfico",
      style,
      textAlign: style.textAlign,
      verticalAlign: style.verticalAlign,
    };
  }

  if (selected.type === "table_view") {
    if (isTableTextFormatPart(selectedTablePart) && selectedTablePart) {
      const partStyle = getTablePartState(selected.tableParts, selectedTablePart)?.style;
      const global = resolveTableGlobalStyle(selected);
      const style = snapshotFromPartStyle(
        {
          fontFamily: partStyle?.fontFamily ?? global.fontFamily,
          fontSize: partStyle?.fontSize ?? global.fontSize,
          fontWeight: partStyle?.fontWeight ?? global.fontWeight,
          fontStyle: partStyle?.fontStyle ?? global.fontStyle,
          color: partStyle?.color ?? global.color,
          textAlign: partStyle?.textAlign ?? global.textAlign,
          verticalAlign: partStyle?.verticalAlign,
          textDecoration: partStyle?.textDecoration,
          textShadow: partStyle?.textShadow,
          textStrokeColor: partStyle?.textStrokeColor,
          textStrokeWidth: partStyle?.textStrokeWidth,
          textReflection: partStyle?.textReflection,
        },
        global.fontSize ?? TABLE_VIEW_DEFAULT_FONT_SIZE_PX,
      );
      return {
        mode: "part",
        source: "table",
        blockId: selected.id,
        partLabel: tablePartSelectionLabel(selectedTablePart),
        style,
        textAlign: style.textAlign,
        verticalAlign: style.verticalAlign,
      };
    }
    const style = resolveTableGlobalStyle(selected);
    return {
      mode: "complexGlobal",
      source: "table",
      blockId: selected.id,
      partLabel: "Texto da tabela",
      style,
      textAlign: style.textAlign,
      verticalAlign: style.verticalAlign,
    };
  }

  if (selected.type === "input") {
    if (isInputTextFormatPart(selectedInputPart) && selectedInputPart) {
      const partStyle = getInputPartState(selected.inputParts, selectedInputPart)?.style;
      const kind = selectedInputPart.kind as "label" | "badge" | "control";
      const style = snapshotFromPartStyle(partStyle, resolveInputPartFontSize(kind, partStyle));
      return {
        mode: "part",
        source: "input",
        blockId: selected.id,
        partLabel: inputPartSelectionLabel(selectedInputPart),
        style,
        textAlign: style.textAlign,
        verticalAlign: style.verticalAlign,
      };
    }
    const style = resolveInputGlobalStyle(selected);
    return {
      mode: "complexGlobal",
      source: "input",
      blockId: selected.id,
      partLabel: "Texto do filtro",
      style,
      textAlign: style.textAlign,
      verticalAlign: style.verticalAlign,
    };
  }

  if (selected.type === "canvas_table") {
    const style = resolveCanvasGlobalStyle(selected);
    return {
      mode: "complexGlobal",
      source: "canvas_table",
      blockId: selected.id,
      partLabel: "Texto da grade",
      style,
      textAlign: style.textAlign,
      verticalAlign: style.verticalAlign,
    };
  }

  return null;
}
