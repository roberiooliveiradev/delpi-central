import {
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
  resolveChartPartFontSize,
  resolveInputPartFontSize,
  resolveKpiPartFontSize,
  upsertChartPartState,
  upsertInputPartState,
  upsertKpiPartState,
  upsertTablePartState,
  CHART_PART_FONT_SIZE_DEFAULTS,
  INPUT_TEXT_PART_KINDS,
  KPI_TEXT_PART_KINDS,
  type ChartTextPartKind,
  type ComunicadoBlock,
  type ComunicadoChartPartRef,
  type ComunicadoChartPartStyle,
  type ComunicadoInputPartRef,
  type ComunicadoInputPartStyle,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartStyle,
  type ComunicadoTablePartRef,
  type KpiTextPartKind,
} from "@delpi/tv-dashboard-presentation";

import type { TextFormatStyleSnapshot } from "./selectedTextFormatTarget";
import {
  isChartTextFormatPart,
  isInputTextFormatPart,
  isKpiTextFormatPart,
  isTableTextFormatPart,
  resolveSelectedTextFormatTarget,
} from "./selectedTextFormatTarget";
import {
  mergeSparseStyleProperties,
  resolveAppliedNumericProperty,
  sparsePropertyPatch,
  type SelectionPropertyApplyOptions,
} from "./selectionPropertyApply";
import { patchCanvasTableCellsStyle } from "./canvasTableSelectionCommands";

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

/**
 * Merge tipográfico esparso: só propriedades definidas no patch.
 * Evita `{ fontWeight: undefined }` apagar estilo prévio no upsert do gráfico.
 */
function mergeTypographyStyle(
  prev: AnyPartStyle | null | undefined,
  patch: TextFormatStyleSnapshot,
  opts?: { fontSizeAuto?: boolean; nextFontSize?: number | undefined; typographyMode?: string },
): AnyPartStyle {
  const sparse = sparsePropertyPatch({
    fontFamily: patch.fontFamily,
    fontWeight: patch.fontWeight,
    fontStyle: patch.fontStyle,
    color: patch.color,
    textDecoration: patch.textDecoration,
    textShadow: patch.textShadow,
    textStrokeColor: patch.textStrokeColor,
    textStrokeWidth: patch.textStrokeWidth,
    textReflection: patch.textReflection,
    textAlign: pickTextAlign(patch.textAlign),
    verticalAlign: pickVerticalAlign(patch.verticalAlign),
  } as Record<string, unknown>) as AnyPartStyle;

  let next = mergeSparseStyleProperties((prev ?? {}) as Record<string, unknown>, sparse) as AnyPartStyle;

  if (opts?.fontSizeAuto) {
    const { fontSize: _drop, ...rest } = next;
    next = { ...rest, typographyMode: "auto" };
  } else if (opts?.nextFontSize != null) {
    next = {
      ...next,
      fontSize: opts.nextFontSize,
      typographyMode: opts.typographyMode ?? "fixed",
    };
  } else if (patch.fontSize != null) {
    next = { ...next, fontSize: patch.fontSize };
  }

  return next;
}

function resolveFontSizeForTarget(params: {
  current: number;
  patch: TextFormatStyleSnapshot;
  options?: SelectionPropertyApplyOptions;
}): number | undefined {
  return resolveAppliedNumericProperty({
    current: params.current,
    value: params.patch.fontSize,
    mode: params.options?.fontSizeMode,
    delta: params.options?.fontSizeDelta,
    clamp: clampFontSize,
  });
}

function typographyPatchForChart(patch: TextFormatStyleSnapshot): TextFormatStyleSnapshot {
  return {
    ...patch,
    fontWeight: pickFontWeight(patch.fontWeight) ?? patch.fontWeight,
    fontStyle: pickFontStyle(patch.fontStyle) ?? patch.fontStyle,
  };
}

function wantsFontSizeChange(
  patch: TextFormatStyleSnapshot,
  options?: SelectionPropertyApplyOptions,
): boolean {
  if (options?.fontSizeMode === "delta") return true;
  return patch.fontSize != null;
}

/** Tipografia global do gráfico: merge por parte + absolute/delta no tamanho. */
function applyChartComplexGlobalTypography(
  selected: Extract<ComunicadoBlock, { type: "chart_view" }>,
  patch: TextFormatStyleSnapshot,
  options?: SelectionPropertyApplyOptions,
): Partial<ComunicadoBlock> {
  const typographyPatch = typographyPatchForChart(patch);
  const applySize = wantsFontSizeChange(typographyPatch, options);
  const sizeOptions: SelectionPropertyApplyOptions | undefined = applySize
    ? options?.fontSizeMode
      ? options
      : { fontSizeMode: "absolute" }
    : undefined;

  let nextParts = selected.chartParts ?? {};
  const kinds = Object.keys(CHART_PART_FONT_SIZE_DEFAULTS) as ChartTextPartKind[];

  for (const kind of kinds) {
    if (kind === "dataLabel") continue;
    const refs: ComunicadoChartPartRef[] =
      kind === "axis"
        ? [
            { kind: "axis", axis: "x" },
            { kind: "axis", axis: "y" },
          ]
        : kind === "axisTitle"
          ? [
              { kind: "axisTitle", axis: "x" },
              { kind: "axisTitle", axis: "y" },
            ]
          : [{ kind }];

    for (const ref of refs) {
      const prev = getChartPartState(nextParts, ref)?.style;
      const currentSize = resolveChartPartFontSize(kind, prev);
      const nextFontSize = applySize
        ? resolveFontSizeForTarget({
            current: currentSize,
            patch: typographyPatch,
            options: sizeOptions,
          })
        : undefined;
      const partPatch: TextFormatStyleSnapshot = { ...typographyPatch };
      if (nextFontSize == null) {
        delete partPatch.fontSize;
      } else {
        partPatch.fontSize = nextFontSize;
      }
      nextParts = upsertChartPartState(nextParts, ref, {
        style: mergeTypographyStyle(prev, partPatch) as ComunicadoChartPartStyle,
      });
    }
  }

  const optionsNext = mergeComunicadoChartOptions({
    ...selected.chartOptions,
    ...partsToChartOptions(nextParts),
  });
  return {
    chartParts: nextParts,
    chartOptions: optionsNext,
  } as Partial<ComunicadoBlock>;
}

function applyKpiComplexGlobalTypography(
  selected: Extract<ComunicadoBlock, { type: "kpi_view" }>,
  patch: TextFormatStyleSnapshot,
  options?: SelectionPropertyApplyOptions,
): Partial<ComunicadoBlock> {
  const applySize = wantsFontSizeChange(patch, options);
  const sizeOptions: SelectionPropertyApplyOptions | undefined = applySize
    ? options?.fontSizeMode
      ? options
      : { fontSizeMode: "absolute" }
    : undefined;

  let nextParts = selected.kpiParts ?? {};
  for (const kind of KPI_TEXT_PART_KINDS) {
    const ref = { kind } as const;
    const prev = getKpiPartState(nextParts, ref)?.style;
    const currentSize = resolveKpiPartFontSize(kind as KpiTextPartKind, prev);
    const nextFontSize = applySize
      ? resolveFontSizeForTarget({
          current: currentSize,
          patch,
          options: sizeOptions,
        })
      : undefined;

    const partPatch: TextFormatStyleSnapshot = { ...patch };
    if (nextFontSize == null) delete partPatch.fontSize;
    else partPatch.fontSize = nextFontSize;

    nextParts = upsertKpiPartState(nextParts, ref, {
      style: mergeTypographyStyle(prev, partPatch, {
        fontSizeAuto: patch.fontSizeAuto === true,
        nextFontSize: patch.fontSizeAuto === true ? undefined : nextFontSize,
        typographyMode:
          patch.fontSizeAuto === true
            ? "auto"
            : nextFontSize != null
              ? "fixed"
              : prev?.typographyMode,
      }) as ComunicadoKpiPartStyle,
    });
  }

  const kpiOptions = mergeComunicadoKpiOptions({
    ...selected.kpiOptions,
    ...partsToKpiOptions(nextParts),
  });
  if (patch.color) kpiOptions.valueColor = patch.color;
  return {
    kpiParts: mergeKpiPartsWithOptions(nextParts, kpiOptions),
    kpiOptions,
  } as Partial<ComunicadoBlock>;
}

function applyInputComplexGlobalTypography(
  selected: Extract<ComunicadoBlock, { type: "input" }>,
  patch: TextFormatStyleSnapshot,
  options?: SelectionPropertyApplyOptions,
): Partial<ComunicadoBlock> {
  const applySize = wantsFontSizeChange(patch, options);
  const sizeOptions: SelectionPropertyApplyOptions | undefined = applySize
    ? options?.fontSizeMode
      ? options
      : { fontSizeMode: "absolute" }
    : undefined;

  let nextParts = selected.inputParts ?? {};
  for (const kind of INPUT_TEXT_PART_KINDS) {
    const ref = { kind } as const;
    const prev = getInputPartState(nextParts, ref)?.style;
    const currentSize = resolveInputPartFontSize(kind, prev);
    const nextFontSize = applySize
      ? resolveFontSizeForTarget({
          current: currentSize,
          patch,
          options: sizeOptions,
        })
      : undefined;
    const partPatch: TextFormatStyleSnapshot = { ...patch };
    if (nextFontSize == null) delete partPatch.fontSize;
    else partPatch.fontSize = nextFontSize;
    nextParts = upsertInputPartState(nextParts, ref, {
      style: mergeTypographyStyle(prev, partPatch) as ComunicadoInputPartStyle,
    });
  }
  return { inputParts: nextParts } as Partial<ComunicadoBlock>;
}

/**
 * Calcula o patch de bloco para tipografia da ribbon Fonte.
 * Retorna `null` quando o caller deve cair em `updateSelectedStyle` (text/shape).
 *
 * `applyOptions.fontSizeMode`:
 * - `absolute` — mesmo px em todos os subitens (input / preset)
 * - `delta` — ±passo em cada subitem (hierarquia preservada)
 */
export function buildSelectedTextFormatBlockPatch(params: {
  selected: ComunicadoBlock;
  patch: TextFormatStyleSnapshot;
  selectedKpiPart?: ComunicadoKpiPartRef | null;
  selectedChartPart?: ComunicadoChartPartRef | null;
  selectedTablePart?: ComunicadoTablePartRef | null;
  /** Multi-seleção de colunas/células/linhas — tipografia aplica a todas. */
  selectedTableParts?: ComunicadoTablePartRef[] | null;
  selectedInputPart?: ComunicadoInputPartRef | null;
  selectedCanvasTableCell?: {
    blockId: string;
    cells: Array<{ row: number; col: number }>;
    focus: { row: number; col: number };
  } | null;
  applyOptions?: SelectionPropertyApplyOptions;
}): Partial<ComunicadoBlock> | null {
  const {
    selected,
    patch,
    selectedKpiPart = null,
    selectedChartPart = null,
    selectedTablePart = null,
    selectedTableParts = null,
    selectedInputPart = null,
    selectedCanvasTableCell = null,
    applyOptions,
  } = params;

  const target = resolveSelectedTextFormatTarget({
    selected,
    selectedKpiPart,
    selectedChartPart,
    selectedTablePart,
    selectedInputPart,
    selectedCanvasTableCell,
  });
  if (!target) return null;

  if (target.mode === "block") {
    return null;
  }

  if (target.mode === "canvasCell" && selected.type === "canvas_table") {
    const currentSize = target.style.fontSize ?? 14;
    const nextFont = resolveFontSizeForTarget({
      current: currentSize,
      patch,
      options: applyOptions?.fontSizeMode
        ? applyOptions
        : patch.fontSize != null
          ? { fontSizeMode: "absolute" }
          : undefined,
    });
    const stylePatch = sparsePropertyPatch({
      fontFamily: patch.fontFamily,
      fontWeight: patch.fontWeight,
      fontStyle: patch.fontStyle,
      color: patch.color,
      textDecoration: patch.textDecoration,
      textAlign: pickTextAlign(patch.textAlign),
      verticalAlign: pickVerticalAlign(patch.verticalAlign),
      ...(nextFont != null ? { fontSize: nextFont } : {}),
    } as Record<string, unknown>);
    return {
      cells: patchCanvasTableCellsStyle({
        cells: selected.cells,
        selection: target.cells,
        stylePatch,
      }),
    } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "part" && target.source === "kpi" && selected.type === "kpi_view") {
    if (!isKpiTextFormatPart(selectedKpiPart) || !selectedKpiPart) return null;
    const prev = getKpiPartState(selected.kpiParts, selectedKpiPart)?.style;
    const kind = selectedKpiPart.kind as KpiTextPartKind;
    const currentSize = resolveKpiPartFontSize(kind, prev);
    const stepped = resolveFontSizeForTarget({
      current: currentSize,
      patch,
      options: applyOptions,
    });
    const nextFontSize =
      patch.fontSizeAuto === true
        ? undefined
        : stepped != null
          ? stepped
          : patch.fontSize != null
            ? patch.fontSize
            : prev?.fontSize;
    const nextTypographyMode =
      patch.fontSizeAuto === true
        ? ("auto" as const)
        : nextFontSize != null
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
    const typographyPatch = typographyPatchForChart(patch);
    if (selectedChartPart.kind === "axes") {
      let nextParts = selected.chartParts;
      for (const axis of ["x", "y"] as const) {
        const axisRef = { kind: "axis" as const, axis };
        const prev = getChartPartState(nextParts, axisRef)?.style;
        const currentSize = resolveChartPartFontSize("axis", prev);
        const nextFontSize = resolveFontSizeForTarget({
          current: currentSize,
          patch: typographyPatch,
          options: applyOptions,
        });
        const partPatch = { ...typographyPatch };
        if (nextFontSize == null) delete partPatch.fontSize;
        else partPatch.fontSize = nextFontSize;
        nextParts = upsertChartPartState(nextParts, axisRef, {
          style: mergeTypographyStyle(prev, partPatch) as ComunicadoChartPartStyle,
        });
      }
      return { chartParts: nextParts } as Partial<ComunicadoBlock>;
    }
    const prev = getChartPartState(selected.chartParts, selectedChartPart)?.style;
    const textKindRaw = selectedChartPart.kind;
    const textKind: ChartTextPartKind =
      textKindRaw in CHART_PART_FONT_SIZE_DEFAULTS
        ? (textKindRaw as ChartTextPartKind)
        : "title";
    const currentSize = resolveChartPartFontSize(textKind, prev);
    const nextFontSize = resolveFontSizeForTarget({
      current: currentSize,
      patch: typographyPatch,
      options: applyOptions,
    });
    const partPatch = { ...typographyPatch };
    if (nextFontSize == null) delete partPatch.fontSize;
    else partPatch.fontSize = nextFontSize;
    const nextParts = upsertChartPartState(selected.chartParts, selectedChartPart, {
      style: mergeTypographyStyle(prev, partPatch) as ComunicadoChartPartStyle,
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
    const targets = (selectedTableParts?.length ? selectedTableParts : [selectedTablePart]).filter(
      (part) => isTableTextFormatPart(part),
    );
    const applyTo = targets.length > 0 ? targets : [selectedTablePart];
    let nextParts = selected.tableParts;
    for (const part of applyTo) {
      const prev = getTablePartState(nextParts, part)?.style;
      nextParts = upsertTablePartState(nextParts, part, {
        style: mergeTypographyStyle(prev, patch) as AnyPartStyle,
      });
    }
    return { tableParts: nextParts } as Partial<ComunicadoBlock>;
  }

  if (target.mode === "complexGlobal" && target.source === "kpi" && selected.type === "kpi_view") {
    return applyKpiComplexGlobalTypography(selected, patch, applyOptions);
  }

  if (target.mode === "complexGlobal" && target.source === "chart" && selected.type === "chart_view") {
    return applyChartComplexGlobalTypography(selected, patch, applyOptions);
  }

  if (target.mode === "complexGlobal" && target.source === "input" && selected.type === "input") {
    return applyInputComplexGlobalTypography(selected, patch, applyOptions);
  }

  if (target.mode === "complexGlobal" && target.source === "table" && selected.type === "table_view") {
    const current = mergeComunicadoTableOptions(selected.tableOptions, selected.tablePreset);
    const currentSize = current.fontSize ?? 14;
    const nextFont = resolveFontSizeForTarget({
      current: currentSize,
      patch,
      options: applyOptions?.fontSizeMode
        ? applyOptions
        : patch.fontSize != null
          ? { fontSizeMode: "absolute" }
          : undefined,
    });
    const nextOptions = {
      ...current,
      ...(patch.fontFamily != null ? { fontFamily: patch.fontFamily } : {}),
      ...(nextFont != null ? { fontSize: nextFont } : {}),
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
    const currentSize = selected.canvasTableOptions?.fontSize ?? selected.style?.fontSize ?? 14;
    const nextFont = resolveFontSizeForTarget({
      current: currentSize,
      patch,
      options: applyOptions?.fontSizeMode
        ? applyOptions
        : patch.fontSize != null
          ? { fontSizeMode: "absolute" }
          : undefined,
    });
    const styleSparse = sparsePropertyPatch({
      fontFamily: patch.fontFamily,
      fontWeight: patch.fontWeight,
      fontStyle: patch.fontStyle,
      color: patch.color,
      textDecoration: patch.textDecoration,
      textShadow: patch.textShadow,
      textStrokeColor: patch.textStrokeColor,
      textStrokeWidth: patch.textStrokeWidth,
      textReflection: patch.textReflection,
      textAlign: pickTextAlign(patch.textAlign),
      verticalAlign: pickVerticalAlign(patch.verticalAlign),
      ...(nextFont != null ? { fontSize: nextFont } : {}),
    } as Record<string, unknown>);
    return {
      canvasTableOptions: {
        ...(selected.canvasTableOptions ?? {}),
        ...(nextFont != null ? { fontSize: nextFont } : {}),
      },
      style: {
        ...(selected.style ?? {}),
        ...styleSparse,
      },
    } as Partial<ComunicadoBlock>;
  }

  return null;
}
