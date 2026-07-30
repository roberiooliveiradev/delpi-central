import {
  applyChartTextStyleToSiblingParts,
  applyInputTextStyleToSiblingParts,
  applyKpiPartStyleToSiblingParts,
  clampFontSize,
  getChartPartState,
  getInputPartState,
  getKpiPartState,
  getTablePartState,
  mergeComunicadoChartOptions,
  mergeComunicadoKpiOptions,
  mergeComunicadoTableOptions,
  mergeKpiPartsWithOptions,
  mergeTablePartsWithOptions,
  partsToChartOptions,
  partsToKpiOptions,
  upsertChartPartState,
  upsertInputPartState,
  upsertKpiPartState,
  upsertTablePartState,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartPartStyle,
  type ComunicadoInputPartRef,
  type ComunicadoInputPartStyle,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartStyle,
  type ComunicadoTablePartRef,
} from "@delpi/tv-dashboard-presentation";

import type { TextFormatStyleSnapshot } from "./selectedTextFormatTarget";
import {
  isChartTextFormatPart,
  isInputTextFormatPart,
  isKpiTextFormatPart,
  isTableTextFormatPart,
  resolveSelectedTextFormatTarget,
} from "./selectedTextFormatTarget";

type AnyPartStyle = {
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
  typographyMode?: string;
};

function pickTextAlign(
  value: string | undefined,
): "left" | "center" | "right" | "justify" | undefined {
  if (value === "left" || value === "center" || value === "right" || value === "justify") {
    return value;
  }
  return undefined;
}

function pickVerticalAlign(value: string | undefined): "top" | "middle" | "bottom" | undefined {
  if (value === "top" || value === "middle" || value === "bottom") return value;
  return undefined;
}

function pickFontWeight(value: string | undefined): "bold" | "normal" | undefined {
  if (value === "bold" || value === "normal") return value;
  return undefined;
}

function pickFontStyle(value: string | undefined): "italic" | "normal" | undefined {
  if (value === "italic" || value === "normal") return value;
  return undefined;
}

function mergeTypographyStyle(
  prev: AnyPartStyle | null | undefined,
  patch: TextFormatStyleSnapshot,
  opts?: { fontSizeAuto?: boolean; nextFontSize?: number | undefined; typographyMode?: string },
): AnyPartStyle {
  const nextAlign = pickTextAlign(patch.textAlign);
  const nextVAlign = pickVerticalAlign(patch.verticalAlign);
  return {
    ...(prev ?? {}),
    fontFamily: patch.fontFamily ?? prev?.fontFamily,
    ...(opts?.fontSizeAuto
      ? { fontSize: undefined, typographyMode: "auto" }
      : opts?.nextFontSize != null
        ? { fontSize: opts.nextFontSize, typographyMode: opts.typographyMode ?? "fixed" }
        : patch.fontSize != null
          ? { fontSize: patch.fontSize }
          : {}),
    fontWeight: patch.fontWeight ?? prev?.fontWeight,
    fontStyle: patch.fontStyle ?? prev?.fontStyle,
    color: patch.color ?? prev?.color,
    textDecoration: patch.textDecoration ?? prev?.textDecoration,
    textShadow: patch.textShadow ?? prev?.textShadow,
    textStrokeColor: patch.textStrokeColor ?? prev?.textStrokeColor,
    textStrokeWidth: patch.textStrokeWidth ?? prev?.textStrokeWidth,
    textReflection: patch.textReflection ?? prev?.textReflection,
    ...(nextAlign ? { textAlign: nextAlign } : {}),
    ...(nextVAlign ? { verticalAlign: nextVAlign } : {}),
  };
}

/**
 * Calcula o patch de bloco para tipografia da ribbon Fonte.
 * Retorna `null` quando o caller deve cair em `updateSelectedStyle` (text/shape).
 */
export function buildSelectedTextFormatBlockPatch(params: {
  selected: ComunicadoBlock;
  patch: TextFormatStyleSnapshot;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedTablePart?: ComunicadoTablePartRef | null;
  selectedInputPart?: ComunicadoInputPartRef | null;
}): Partial<ComunicadoBlock> | null {
  const {
    selected,
    patch,
    selectedKpiPart = null,
    selectedChartPart = null,
    selectedTablePart = null,
    selectedInputPart = null,
  } = params;

  const target = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
    selectedTablePart,
    selectedInputPart,
  });
  if (!target) return null;

  if (target.mode === "block") {
    return null;
  }

  if (target.mode === "part" && target.source === "kpi" && selected.type === "kpi_view") {
    if (!isKpiTextFormatPart(selectedKpiPart) || !selectedKpiPart) return null;
    const prev = getKpiPartState(selected.kpiParts, selectedKpiPart)?.style;
    const nextFontSize =
      patch.fontSizeAuto === true
        ? undefined
        : patch.fontSize != null
          ? patch.fontSize
          : prev?.fontSize;
    const nextTypographyMode =
      patch.fontSizeAuto === true
        ? ("auto" as const)
        : patch.fontSize != null
          ? ("fixed" as const)
          : prev?.typographyMode;
    const nextParts = upsertKpiPartState(selected.kpiParts, selectedKpiPart, {
      style: mergeTypographyStyle(prev, patch, {
        fontSizeAuto: patch.fontSizeAuto === true,
        nextFontSize,
        typographyMode: nextTypographyMode,
      }) as ComunicadoKpiPartStyle,
    });
    const options = mergeComunicadoKpiOptions({
      ...selected.kpiOptions,
      ...partsToKpiOptions(nextParts),
    });
    if (selectedKpiPart.kind === "value" && patch.color) {
      options.valueColor = patch.color;
    }
    return {
      kpiParts: mergeKpiPartsWithOptions(nextParts, options),
      kpiOptions: options,
    } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "part" && target.source === "chart" && selected.type === "chart_view") {
    if (!isChartTextFormatPart(selectedChartPart) || !selectedChartPart) return null;
    const typographyPatch = {
      ...patch,
      fontWeight: pickFontWeight(patch.fontWeight) ?? patch.fontWeight,
      fontStyle: pickFontStyle(patch.fontStyle) ?? patch.fontStyle,
    };
    /* Parte grupo «Eixos»: só axis:x e axis:y — não vaza para dataLabels/título/legenda. */
    if (selectedChartPart.kind === "axes") {
      let nextParts = selected.chartParts;
      for (const axis of ["x", "y"] as const) {
        const axisRef = { kind: "axis" as const, axis };
        const prev = getChartPartState(nextParts, axisRef)?.style;
        nextParts = upsertChartPartState(nextParts, axisRef, {
          style: mergeTypographyStyle(prev, typographyPatch) as ComunicadoChartPartStyle,
        });
      }
      return { chartParts: nextParts } as Partial<ComunicadoBlock>;
    }
    const prev = getChartPartState(selected.chartParts, selectedChartPart)?.style;
    const nextParts = upsertChartPartState(selected.chartParts, selectedChartPart, {
      style: mergeTypographyStyle(prev, typographyPatch) as ComunicadoChartPartStyle,
    });
    return { chartParts: nextParts } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "part" && target.source === "input" && selected.type === "input") {
    if (!isInputTextFormatPart(selectedInputPart) || !selectedInputPart) return null;
    const prev = getInputPartState(selected.inputParts, selectedInputPart)?.style;
    const nextParts = upsertInputPartState(selected.inputParts, selectedInputPart, {
      style: mergeTypographyStyle(prev, patch) as AnyPartStyle,
    });
    return { inputParts: nextParts } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "part" && target.source === "table" && selected.type === "table_view") {
    if (!isTableTextFormatPart(selectedTablePart) || !selectedTablePart) return null;
    const prev = getTablePartState(selected.tableParts, selectedTablePart)?.style;
    const nextParts = upsertTablePartState(selected.tableParts, selectedTablePart, {
      style: mergeTypographyStyle(prev, patch) as AnyPartStyle,
    });
    return { tableParts: nextParts } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "complexGlobal" && target.source === "kpi" && selected.type === "kpi_view") {
    const style = mergeTypographyStyle({}, patch, {
      fontSizeAuto: patch.fontSizeAuto === true,
      nextFontSize: patch.fontSizeAuto === true ? undefined : patch.fontSize,
      typographyMode: patch.fontSizeAuto === true ? "auto" : patch.fontSize != null ? "fixed" : undefined,
    }) as ComunicadoKpiPartStyle;
    const nextParts = applyKpiPartStyleToSiblingParts(selected.kpiParts, { kind: "title" }, style);
    const options = mergeComunicadoKpiOptions({
      ...selected.kpiOptions,
      ...partsToKpiOptions(nextParts),
    });
    if (patch.color) options.valueColor = patch.color;
    return {
      kpiParts: mergeKpiPartsWithOptions(nextParts, options),
      kpiOptions: options,
    } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "complexGlobal" && target.source === "chart" && selected.type === "chart_view") {
    const style = mergeTypographyStyle(
      {},
      {
        ...patch,
        fontWeight: pickFontWeight(patch.fontWeight) ?? patch.fontWeight,
        fontStyle: pickFontStyle(patch.fontStyle) ?? patch.fontStyle,
      },
    ) as ComunicadoChartPartStyle;
    const nextParts = applyChartTextStyleToSiblingParts(selected.chartParts, style);
    const options = mergeComunicadoChartOptions({
      ...selected.chartOptions,
      ...partsToChartOptions(nextParts),
    });
    return {
      chartParts: nextParts,
      chartOptions: options,
    } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "complexGlobal" && target.source === "input" && selected.type === "input") {
    const style = mergeTypographyStyle({}, patch) as AnyPartStyle;
    return {
      inputParts: applyInputTextStyleToSiblingParts(selected.inputParts, style as ComunicadoInputPartStyle),
    } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "complexGlobal" && target.source === "table" && selected.type === "table_view") {
    const current = mergeComunicadoTableOptions(selected.tableOptions, selected.tablePreset);
    const nextOptions = {
      ...current,
      ...(patch.fontFamily != null ? { fontFamily: patch.fontFamily } : {}),
      ...(patch.fontSize != null ? { fontSize: clampFontSize(patch.fontSize) } : {}),
      ...(patch.fontWeight != null ? { fontWeight: patch.fontWeight } : {}),
      ...(patch.fontStyle != null ? { fontStyle: patch.fontStyle } : {}),
      ...(patch.color != null
        ? { cellTextColor: patch.color, headerTextColor: patch.color }
        : {}),
      ...(pickTextAlign(patch.textAlign)
        ? { textAlign: pickTextAlign(patch.textAlign)! }
        : {}),
    };
    return {
      tableOptions: nextOptions,
      tableParts: mergeTablePartsWithOptions(selected.tableParts, nextOptions),
    } as Partial<ComunicadoBlock>;
  }

  if (
    target.mode === "complexGlobal" &&
    target.source === "canvas_table" &&
    selected.type === "canvas_table"
  ) {
    const nextFont =
      patch.fontSize != null ? clampFontSize(patch.fontSize) : selected.canvasTableOptions?.fontSize;
    return {
      canvasTableOptions: {
        ...(selected.canvasTableOptions ?? {}),
        ...(nextFont != null ? { fontSize: nextFont } : {}),
      },
      style: {
        ...(selected.style ?? {}),
        ...(patch.fontFamily != null ? { fontFamily: patch.fontFamily } : {}),
        ...(nextFont != null ? { fontSize: nextFont } : {}),
        ...(patch.fontWeight != null ? { fontWeight: patch.fontWeight } : {}),
        ...(patch.fontStyle != null ? { fontStyle: patch.fontStyle } : {}),
        ...(patch.color != null ? { color: patch.color } : {}),
        ...(pickTextAlign(patch.textAlign) ? { textAlign: pickTextAlign(patch.textAlign) } : {}),
        ...(pickVerticalAlign(patch.verticalAlign)
          ? { verticalAlign: pickVerticalAlign(patch.verticalAlign) }
          : {}),
        ...(patch.textDecoration != null ? { textDecoration: patch.textDecoration } : {}),
        ...(patch.textShadow != null ? { textShadow: patch.textShadow } : {}),
        ...(patch.textStrokeColor != null ? { textStrokeColor: patch.textStrokeColor } : {}),
        ...(patch.textStrokeWidth != null ? { textStrokeWidth: patch.textStrokeWidth } : {}),
        ...(patch.textReflection != null ? { textReflection: patch.textReflection } : {}),
      },
    } as Partial<ComunicadoBlock>;
  }

  return null;
}
