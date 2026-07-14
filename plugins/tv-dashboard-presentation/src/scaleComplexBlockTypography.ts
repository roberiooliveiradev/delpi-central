/**
 * Escala tipografia/traços de blocos complexos (KPI / gráfico / tabela)
 * ao redimensionar o frame — estilo PowerPoint “scale object”.
 * Fator uniforme: min(wRatio, hRatio). Persistido no modelo (px de design).
 */

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
  KPI_ICON_DEFAULT_SIZE_PX,
  KPI_PART_FONT_SIZE_DEFAULTS,
  isKpiTextPartKind,
  mergeKpiPartsWithOptions,
  resolveKpiPartFontSize,
  serializeKpiPartRef,
  upsertKpiPartState,
  type ComunicadoKpiPartRef,
  type ComunicadoKpiPartsMap,
  type ComunicadoKpiPartStyle,
} from "./comunicadoKpiParts";
import type {
  ComunicadoBlock,
  ComunicadoChartViewBlock,
  ComunicadoFrame,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
} from "./comunicadoTypes";

const FONT_PX_MIN = 6;
const STROKE_PX_MIN = 0.5;
const STROKE_PX_MAX = 48;
const ICON_PX_MIN = 8;
const ICON_PX_MAX = 240;
const SCALE_EPSILON = 0.001;

/** Default tipográfico da tabela quando `tableOptions.fontSize` está ausente. */
export const TABLE_VIEW_DEFAULT_FONT_SIZE_PX = 12;

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

function isComplexBlockType(
  type: ComunicadoBlock["type"],
): type is "kpi_view" | "chart_view" | "table_view" {
  return type === "kpi_view" || type === "chart_view" || type === "table_view";
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
  const scale = uniformFrameScale(beforeFrame, afterFrame);
  if (Math.abs(scale - 1) < SCALE_EPSILON) return parts ?? {};
  if (!isKpiTextPartKind(ref.kind) && ref.kind !== "icon") return parts ?? {};
  const key = serializeKpiPartRef(ref);
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
  if (!isComplexBlockType(block.type)) return block;
  const scale = uniformFrameScale(beforeFrame, afterFrame);
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
