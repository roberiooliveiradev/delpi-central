/**
 * Escala tipografia/traços de blocos complexos (KPI / gráfico / tabela / filtro)
 * ao redimensionar o frame — estilo PowerPoint “scale object”.
 * Fator uniforme: min(wRatio, hRatio). Persistido no modelo (px de design).
 */

import { isComplexViewBlockType } from "./complexViewBlocks";
import {
  CHART_PART_FONT_SIZE_DEFAULTS,
  isChartTextPartKind,
  mergeChartPartsWithOptions,
  parseChartPartRef,
  resolveChartPartFontSize,
  serializeChartPartRef,
  upsertChartPartState,
  type ComunicadoChartPartRef,
  type ComunicadoChartPartsMap,
  type ComunicadoChartPartStyle,
} from "./comunicadoChartParts";
import {
  INPUT_ICON_DEFAULT_SIZE_PX,
  INPUT_PART_FONT_SIZE_DEFAULTS,
  isInputTextPartKind,
  mergeInputParts,
  resolveInputPartFontSize,
  serializeInputPartRef,
  upsertInputPartState,
  type ComunicadoInputPartRef,
  type ComunicadoInputPartsMap,
  type ComunicadoInputPartStyle,
} from "./comunicadoInputParts";
import {
  KPI_ICON_DEFAULT_SIZE_PX,
  KPI_PART_FONT_SIZE_DEFAULTS,
  isKpiTextPartKind,
  kpiPartStyleWithAutoFont,
  mergeKpiPartsWithOptions,
  resolveKpiPartFontSize,
  serializeKpiPartRef,
  upsertKpiPartState,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartsMap,
  type ComunicadoKpiPartStyle,
} from "./comunicadoKpiParts";
import { scaleCanvasTableBlockTypography } from "./comunicadoCanvasTable";
import type {
  ComunicadoBlock,
  ComunicadoCanvasTableBlock,
  ComunicadoChartViewBlock,
  ComunicadoFrame,
  ComunicadoInputBlock,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
} from "./comunicadoTypes";

/** Alinhado a `COMUNICADO_FONT_SIZE_MIN` — evita tipografia ilegível no resize. */
const FONT_PX_MIN = 12;
const STROKE_PX_MIN = 0.5;
const STROKE_PX_MAX = 48;
const ICON_PX_MIN = 8;
const ICON_PX_MAX = 240;
const SCALE_EPSILON = 0.001;

/** Default tipográfico da tabela quando `tableOptions.fontSize` está ausente. */
export const TABLE_VIEW_DEFAULT_FONT_SIZE_PX = 16;

export type FrameSize = Pick<ComunicadoFrame, "w" | "h">;

export function uniformFrameScale(before: FrameSize, after: FrameSize): number {
  const w1 = Number(before.w);
  const h1 = Number(before.h);
  const w2 = Number(after.w);
  const h2 = Number(after.h);
  if (!(w1 > 0 && h1 > 0 && w2 > 0 && h2 > 0)) return 1;
  const s = Math.min(w2 / w1, h2 / h1);
  if (!Number.isFinite(s) || s <= 0) return 1;
  if (Math.abs(s - 1) < SCALE_EPSILON) return 1;
  return s;
}

/**
 * Escala pela área (média geométrica dos eixos).
 * Alongar só altura/largura ainda cresce tipografia/ícone — preenche o espaço interno
 * (min(w,h) sozinho deixava o conteúdo «preso» no topo).
 */
export function contentFillFrameScale(before: FrameSize, after: FrameSize): number {
  const w1 = Number(before.w);
  const h1 = Number(before.h);
  const w2 = Number(after.w);
  const h2 = Number(after.h);
  if (!(w1 > 0 && h1 > 0 && w2 > 0 && h2 > 0)) return 1;
  const s = Math.sqrt((w2 / w1) * (h2 / h1));
  if (!Number.isFinite(s) || s <= 0) return 1;
  if (Math.abs(s - 1) < SCALE_EPSILON) return 1;
  return s;
}

export function scaleFontPx(px: number, scale: number): number {
  if (!(scale > 0) || !Number.isFinite(scale) || Math.abs(scale - 1) < SCALE_EPSILON) {
    return Math.round(px);
  }
  if (!(px > 0) || !Number.isFinite(px)) return FONT_PX_MIN;
  return Math.max(FONT_PX_MIN, Math.round(px * scale));
}

function scaleStrokePx(px: number, scale: number): number {
  if (!(scale > 0) || !Number.isFinite(scale) || Math.abs(scale - 1) < SCALE_EPSILON) {
    return px;
  }
  if (!(px > 0) || !Number.isFinite(px)) return STROKE_PX_MIN;
  const next = Math.round(px * scale * 10) / 10;
  return Math.max(STROKE_PX_MIN, Math.min(STROKE_PX_MAX, next));
}

function scaleIconPx(px: number, scale: number): number {
  if (!(scale > 0) || !Number.isFinite(scale) || Math.abs(scale - 1) < SCALE_EPSILON) {
    return Math.round(px);
  }
  if (!(px > 0) || !Number.isFinite(px)) return ICON_PX_MIN;
  return Math.max(ICON_PX_MIN, Math.min(ICON_PX_MAX, Math.round(px * scale)));
}


function scaleChartPartStyle(
  ref: ComunicadoChartPartRef,
  style: ComunicadoChartPartStyle | undefined,
  scale: number,
): ComunicadoChartPartStyle {
  const next: ComunicadoChartPartStyle = { ...(style ?? {}) };
  const textKind =
    ref.kind === "dataLabels"
      ? "dataLabels"
      : isChartTextPartKind(ref.kind)
        ? ref.kind
        : null;

  if (textKind) {
    const base = resolveChartPartFontSize(textKind, style);
    next.fontSize = scaleFontPx(base, scale);
  } else if (style?.fontSize != null && style.fontSize > 0) {
    next.fontSize = scaleFontPx(style.fontSize, scale);
  }

  if (style?.textStrokeWidth != null && style.textStrokeWidth > 0) {
    next.textStrokeWidth = scaleStrokePx(style.textStrokeWidth, scale);
  }
  if (style?.strokeWidth != null && style.strokeWidth > 0) {
    next.strokeWidth = scaleStrokePx(style.strokeWidth, scale);
  }
  if (style?.markerRadius != null && style.markerRadius > 0) {
    next.markerRadius = scaleStrokePx(style.markerRadius, scale);
  }
  return next;
}

function ensureChartTextDefaults(parts: ComunicadoChartPartsMap): ComunicadoChartPartsMap {
  let next = parts;
  const simpleKinds = ["title", "legend", "dataLabels"] as const;
  for (const kind of simpleKinds) {
    const ref: ComunicadoChartPartRef = { kind };
    if (!next[serializeChartPartRef(ref)]?.style?.fontSize) {
      next = upsertChartPartState(next, ref, {
        style: { fontSize: CHART_PART_FONT_SIZE_DEFAULTS[kind] },
      });
    }
  }
  for (const axis of ["x", "y"] as const) {
    for (const kind of ["axis", "axisTitle"] as const) {
      const ref: ComunicadoChartPartRef = { kind, axis };
      const def = CHART_PART_FONT_SIZE_DEFAULTS[kind];
      if (!next[serializeChartPartRef(ref)]?.style?.fontSize) {
        next = upsertChartPartState(next, ref, { style: { fontSize: def } });
      }
    }
  }
  return next;
}

export function scaleChartPartsTypography(
  parts: ComunicadoChartPartsMap | null | undefined,
  scale: number,
  options?: { ensureDefaults?: boolean },
): ComunicadoChartPartsMap {
  if (Math.abs(scale - 1) < SCALE_EPSILON) return parts ?? {};
  let next = options?.ensureDefaults ? ensureChartTextDefaults(parts ?? {}) : { ...(parts ?? {}) };
  for (const key of Object.keys(next)) {
    const ref = parseChartPartRef(key);
    if (!ref) continue;
    const state = next[key];
    const stylePatch = scaleChartPartStyle(ref, state?.style, scale);
    next = upsertChartPartState(next, ref, { style: stylePatch });
  }
  return next;
}

export function scaleChartPartTypographyOnResize(
  parts: ComunicadoChartPartsMap | null | undefined,
  ref: ComunicadoChartPartRef,
  beforeFrame: FrameSize,
  afterFrame: FrameSize,
): ComunicadoChartPartsMap {
  const scale = uniformFrameScale(beforeFrame, afterFrame);
  if (Math.abs(scale - 1) < SCALE_EPSILON) return parts ?? {};
  const state = parts?.[serializeChartPartRef(ref)];
  const stylePatch = scaleChartPartStyle(ref, state?.style, scale);
  return upsertChartPartState(parts, ref, { style: stylePatch });
}

function scaleKpiPartStyle(
  ref: ComunicadoKpiPartRef,
  style: ComunicadoKpiPartStyle | undefined,
  scale: number,
): ComunicadoKpiPartStyle {
  // Título/valor/hint: escalam em px com o frame do bloco (paridade PowerPoint).
  // FitText no valor só no layout livre (frame da parte) — ver scaleKpiPartTypographyOnResize.
  const next: ComunicadoKpiPartStyle = { ...(style ?? {}) };
  if (isKpiTextPartKind(ref.kind)) {
    const base = resolveKpiPartFontSize(ref.kind, style);
    next.fontSize = scaleFontPx(base, scale);
  } else if (style?.fontSize != null && style.fontSize > 0) {
    next.fontSize = scaleFontPx(style.fontSize, scale);
  }
  if (ref.kind === "icon" || style?.iconSize != null) {
    const base =
      style?.iconSize != null && style.iconSize > 0 ? style.iconSize : KPI_ICON_DEFAULT_SIZE_PX;
    next.iconSize = scaleIconPx(base, scale);
  }
  if (style?.borderRadius != null && style.borderRadius > 0) {
    next.borderRadius = scaleStrokePx(style.borderRadius, scale);
  }
  if (style?.textStrokeWidth != null && style.textStrokeWidth > 0) {
    next.textStrokeWidth = scaleStrokePx(style.textStrokeWidth, scale);
  }
  if (style?.strokeWidth != null && style.strokeWidth > 0) {
    next.strokeWidth = scaleStrokePx(style.strokeWidth, scale);
  }
  return next;
}

function ensureKpiTextDefaults(parts: ComunicadoKpiPartsMap): ComunicadoKpiPartsMap {
  let next = parts;
  for (const kind of Object.keys(KPI_PART_FONT_SIZE_DEFAULTS) as Array<
    keyof typeof KPI_PART_FONT_SIZE_DEFAULTS
  >) {
    const ref: ComunicadoKpiPartRef = { kind };
    const key = serializeKpiPartRef(ref);
    if (!next[key]?.style?.fontSize) {
      next = upsertKpiPartState(next, ref, {
        style: { fontSize: KPI_PART_FONT_SIZE_DEFAULTS[kind] },
      });
    }
  }
  const iconKey = serializeKpiPartRef({ kind: "icon" });
  if (next[iconKey] && next[iconKey]?.style?.iconSize == null) {
    next = upsertKpiPartState(next, { kind: "icon" }, {
      style: { iconSize: KPI_ICON_DEFAULT_SIZE_PX },
    });
  }
  return next;
}

export function scaleKpiPartsTypography(
  parts: ComunicadoKpiPartsMap | null | undefined,
  scale: number,
  options?: { ensureDefaults?: boolean },
): ComunicadoKpiPartsMap {
  if (Math.abs(scale - 1) < SCALE_EPSILON) return parts ?? {};
  let next = options?.ensureDefaults
    ? ensureKpiTextDefaults(mergeKpiPartsWithOptions(parts, null))
    : { ...(parts ?? {}) };
  for (const kind of ["title", "value", "hint", "icon", "card"] as const) {
    const ref: ComunicadoKpiPartRef = { kind };
    const key = serializeKpiPartRef(ref);
    if (!next[key] && kind === "card") continue;
    if (!next[key] && !options?.ensureDefaults) continue;
    const stylePatch = scaleKpiPartStyle(ref, next[key]?.style, scale);
    next = upsertKpiPartState(next, ref, { style: stylePatch });
  }
  return next;
}

export function scaleKpiPartTypographyOnResize(
  parts: ComunicadoKpiPartsMap | null | undefined,
  ref: ComunicadoKpiPartRef,
  beforeFrame: FrameSize,
  afterFrame: FrameSize,
): ComunicadoKpiPartsMap {
  if (!isKpiTextPartKind(ref.kind) && ref.kind !== "icon") return parts ?? {};
  const key = serializeKpiPartRef(ref);
  /*
   * Valor em layout livre: resize do frame da parte reativa FitText (limpa px fixo).
   * Resize do bloco pai escala fontSize via scaleKpiPartsTypography — caminho separado.
   */
  if (ref.kind === "value") {
    return upsertKpiPartState(parts, ref, {
      style: kpiPartStyleWithAutoFont(parts?.[key]?.style),
    });
  }
  const scale = uniformFrameScale(beforeFrame, afterFrame);
  if (Math.abs(scale - 1) < SCALE_EPSILON) return parts ?? {};
  const stylePatch = scaleKpiPartStyle(ref, parts?.[key]?.style, scale);
  return upsertKpiPartState(parts, ref, { style: stylePatch });
}

export function scaleTableOptionsFontSize(
  fontSize: number | undefined,
  scale: number,
): number {
  const base =
    fontSize != null && fontSize > 0 ? fontSize : TABLE_VIEW_DEFAULT_FONT_SIZE_PX;
  return scaleFontPx(base, scale);
}

function scaleInputPartStyle(
  ref: ComunicadoInputPartRef,
  style: ComunicadoInputPartStyle | undefined,
  scale: number,
): ComunicadoInputPartStyle {
  const next: ComunicadoInputPartStyle = { ...(style ?? {}) };
  if (isInputTextPartKind(ref.kind)) {
    const base = resolveInputPartFontSize(ref.kind, style);
    next.fontSize = scaleFontPx(base, scale);
  } else if (style?.fontSize != null && style.fontSize > 0) {
    next.fontSize = scaleFontPx(style.fontSize, scale);
  }
  if (ref.kind === "icon" || style?.iconSize != null) {
    const base =
      style?.iconSize != null && style.iconSize > 0
        ? style.iconSize
        : INPUT_ICON_DEFAULT_SIZE_PX;
    next.iconSize = scaleIconPx(base, scale);
  }
  if (style?.borderRadius != null && style.borderRadius > 0) {
    next.borderRadius = scaleStrokePx(style.borderRadius, scale);
  }
  if (style?.textStrokeWidth != null && style.textStrokeWidth > 0) {
    next.textStrokeWidth = scaleStrokePx(style.textStrokeWidth, scale);
  }
  if (style?.strokeWidth != null && style.strokeWidth > 0) {
    next.strokeWidth = scaleStrokePx(style.strokeWidth, scale);
  }
  return next;
}

function ensureInputTextDefaults(parts: ComunicadoInputPartsMap): ComunicadoInputPartsMap {
  let next = parts;
  for (const kind of Object.keys(INPUT_PART_FONT_SIZE_DEFAULTS) as Array<
    keyof typeof INPUT_PART_FONT_SIZE_DEFAULTS
  >) {
    const ref: ComunicadoInputPartRef = { kind };
    const key = serializeInputPartRef(ref);
    if (!next[key]?.style?.fontSize) {
      next = upsertInputPartState(next, ref, {
        style: { fontSize: INPUT_PART_FONT_SIZE_DEFAULTS[kind] },
      });
    }
  }
  const iconKey = serializeInputPartRef({ kind: "icon" });
  if (next[iconKey] && next[iconKey]?.style?.iconSize == null) {
    next = upsertInputPartState(next, { kind: "icon" }, {
      style: { iconSize: INPUT_ICON_DEFAULT_SIZE_PX },
    });
  }
  return next;
}

export function scaleInputPartsTypography(
  parts: ComunicadoInputPartsMap | null | undefined,
  scale: number,
  options?: { ensureDefaults?: boolean },
): ComunicadoInputPartsMap {
  if (Math.abs(scale - 1) < SCALE_EPSILON) return parts ?? {};
  let next = options?.ensureDefaults
    ? ensureInputTextDefaults(mergeInputParts(parts))
    : { ...(parts ?? {}) };
  for (const kind of ["label", "badge", "control", "icon", "frame"] as const) {
    const ref: ComunicadoInputPartRef = { kind };
    const key = serializeInputPartRef(ref);
    if (!next[key] && kind === "frame") continue;
    if (!next[key] && !options?.ensureDefaults) continue;
    const stylePatch = scaleInputPartStyle(ref, next[key]?.style, scale);
    next = upsertInputPartState(next, ref, { style: stylePatch });
  }
  return next;
}

export function scaleInputPartTypographyOnResize(
  parts: ComunicadoInputPartsMap | null | undefined,
  ref: ComunicadoInputPartRef,
  beforeFrame: FrameSize,
  afterFrame: FrameSize,
): ComunicadoInputPartsMap {
  const scale = uniformFrameScale(beforeFrame, afterFrame);
  if (Math.abs(scale - 1) < SCALE_EPSILON) return parts ?? {};
  if (!isInputTextPartKind(ref.kind) && ref.kind !== "icon") return parts ?? {};
  const key = serializeInputPartRef(ref);
  const stylePatch = scaleInputPartStyle(ref, parts?.[key]?.style, scale);
  return upsertInputPartState(parts, ref, { style: stylePatch });
}

/**
 * Aplica escala tipográfica ao bloco complexo após mudança de w/h do frame.
 * `block` deve ser o **baseline** (tipografia pré-resize) — nunca o estado já escalado
 * do frame intermediário (senão o fator acumula a cada pointermove).
 * O caller define `block.frame` (ou usa `applyComplexBlockFrameWithTypography`).
 * No-op se o tipo não for complexo ou se o fator for ~1.
 */
export function scaleComplexBlockOnResize(
  block: ComunicadoBlock,
  beforeFrame: FrameSize,
  afterFrame: FrameSize,
): ComunicadoBlock {
  if (!isComplexViewBlockType(block.type)) return block;
  // KPI/filtro: média geométrica — aproveita espaço ao alongar um eixo.
  // Gráfico/tabela: min (evita tipografia estourar o plot).
  const scale =
    block.type === "kpi_view" || block.type === "input"
      ? contentFillFrameScale(beforeFrame, afterFrame)
      : uniformFrameScale(beforeFrame, afterFrame);
  if (Math.abs(scale - 1) < SCALE_EPSILON) return block;

  if (block.type === "kpi_view") {
    const kpi = block as ComunicadoKpiViewBlock;
    const baseParts = mergeKpiPartsWithOptions(kpi.kpiParts, kpi.kpiOptions ?? null);
    return {
      ...kpi,
      kpiParts: scaleKpiPartsTypography(baseParts, scale, { ensureDefaults: true }),
    };
  }

  if (block.type === "chart_view") {
    const chart = block as ComunicadoChartViewBlock;
    const baseParts = mergeChartPartsWithOptions(chart.chartParts, chart.chartOptions ?? null);
    return {
      ...chart,
      chartParts: scaleChartPartsTypography(baseParts, scale, { ensureDefaults: true }),
    };
  }

  if (block.type === "input") {
    const inputBlock = block as ComunicadoInputBlock;
    return {
      ...inputBlock,
      inputParts: scaleInputPartsTypography(inputBlock.inputParts, scale, {
        ensureDefaults: true,
      }),
    };
  }

  if (block.type === "canvas_table") {
    return scaleCanvasTableBlockTypography(
      block as ComunicadoCanvasTableBlock,
      scale,
      scaleFontPx,
    );
  }

  const table = block as ComunicadoTableViewBlock;
  const nextFont = scaleTableOptionsFontSize(table.tableOptions?.fontSize, scale);
  return {
    ...table,
    tableOptions: {
      ...(table.tableOptions ?? {}),
      fontSize: nextFont,
    },
  };
}

/**
 * Resize live / finalize: aplica `afterFrame` + tipografia a partir do baseline do arrasto.
 */
export function applyComplexBlockFrameWithTypography(
  baseline: ComunicadoBlock,
  afterFrame: ComunicadoFrame,
): ComunicadoBlock {
  const withFrame = { ...baseline, frame: afterFrame } as ComunicadoBlock;
  return scaleComplexBlockOnResize(withFrame, baseline.frame, afterFrame);
}
