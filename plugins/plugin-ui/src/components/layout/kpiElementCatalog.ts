/**
 * Catálogo de elementos do KPI (ligar/desligar famílias de partes) — espelho de seriesChartElementCatalog.
 */

import type { KpiCardFlatOptions, KpiPartRef, KpiPartsMap } from "./kpiCardParts";
import {
  KPI_PART_DEFAULT_FRAMES,
  kpiOptionsToParts,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  seedKpiPartsFreeLayoutFrames,
  upsertKpiPartState,
} from "./kpiCardParts";

export type KpiElementId =
  | "kpiTitle"
  | "kpiValue"
  | "kpiHint"
  | "kpiIcon"
  | "kpiCard"
  | "kpiComparison"
  | "kpiProgress"
  | "kpiSparkline";

export type KpiElementDefinition = {
  id: KpiElementId;
  label: string;
  description?: string;
};

export const KPI_ELEMENT_CATALOG: KpiElementDefinition[] = [
  { id: "kpiCard", label: "Card", description: "Fundo e contorno do indicador" },
  { id: "kpiTitle", label: "Título", description: "Rótulo do indicador" },
  { id: "kpiValue", label: "Valor", description: "Número principal" },
  { id: "kpiHint", label: "Subtítulo", description: "Texto auxiliar abaixo do valor" },
  { id: "kpiIcon", label: "Ícone", description: "Ícone à direita do card" },
  { id: "kpiComparison", label: "Comparação", description: "Delta vs meta ou período" },
  { id: "kpiProgress", label: "Progresso", description: "Barra até a meta" },
  { id: "kpiSparkline", label: "Sparkline", description: "Mini-série temporal" },
];

export type KpiAddElementChoiceId =
  | "title:on"
  | "title:off"
  | "hint:on"
  | "hint:off"
  | "icon:on"
  | "icon:off"
  | "comparison:target"
  | "comparison:previous"
  | "comparison:off"
  | "progress:on"
  | "progress:off"
  | "sparkline:on"
  | "sparkline:off"
  | "layout:compact"
  | "layout:ban"
  | "layout:scorecard"
  | "layout:free";

export function kpiElementPrimaryPartRef(elementId: KpiElementId): KpiPartRef {
  switch (elementId) {
    case "kpiCard":
      return { kind: "card" };
    case "kpiTitle":
      return { kind: "title" };
    case "kpiValue":
      return { kind: "value" };
    case "kpiHint":
      return { kind: "hint" };
    case "kpiIcon":
      return { kind: "icon" };
    case "kpiComparison":
      return { kind: "comparison" };
    case "kpiProgress":
      return { kind: "progress" };
    case "kpiSparkline":
      return { kind: "sparkline" };
    default: {
      const _exhaustive: never = elementId;
      return _exhaustive;
    }
  }
}

export function kpiElementIdForPartRef(ref: KpiPartRef): KpiElementId {
  switch (ref.kind) {
    case "card":
      return "kpiCard";
    case "title":
      return "kpiTitle";
    case "value":
      return "kpiValue";
    case "hint":
      return "kpiHint";
    case "icon":
      return "kpiIcon";
    case "comparison":
      return "kpiComparison";
    case "progress":
      return "kpiProgress";
    case "sparkline":
      return "kpiSparkline";
    case "metricCard":
      return "kpiCard";
    default: {
      const _exhaustive: never = ref;
      return _exhaustive;
    }
  }
}

export function isKpiElementEnabled(
  elementId: KpiElementId,
  options?: KpiCardFlatOptions | null,
  parts?: KpiPartsMap | null,
): boolean {
  const merged = mergeKpiPartsWithOptions(parts, options);
  const ref = kpiElementPrimaryPartRef(elementId);
  const state = merged[ref.kind];
  if (elementId === "kpiIcon") {
    if (options?.showIcon === false) return false;
    return state?.visible !== false;
  }
  if (elementId === "kpiTitle") {
    if (options?.showTitle === false) return false;
    return state?.visible !== false;
  }
  if (elementId === "kpiHint") {
    if (state?.visible === false) return false;
    return Boolean(options?.subtitle?.trim() || state?.content?.trim() || state?.visible === true);
  }
  if (elementId === "kpiComparison") {
    if (options?.showComparison === false) return false;
    return state?.visible === true || options?.showComparison === true;
  }
  if (elementId === "kpiProgress") {
    if (options?.showProgress === false) return false;
    return state?.visible === true || options?.showProgress === true;
  }
  if (elementId === "kpiSparkline") {
    if (options?.showSparkline === false) return false;
    return state?.visible === true || options?.showSparkline === true;
  }
  if (elementId === "kpiCard" || elementId === "kpiValue") return true;
  return state?.visible !== false;
}

export function applyKpiElementVisibility(
  elementId: KpiElementId,
  enabled: boolean,
  options?: KpiCardFlatOptions | null,
  parts?: KpiPartsMap | null,
): { options: KpiCardFlatOptions; parts: KpiPartsMap } {
  const ref = kpiElementPrimaryPartRef(elementId);
  let nextParts = upsertKpiPartState(parts, ref, { visible: enabled });
  const nextOptions: KpiCardFlatOptions = {
    ...(options ?? {}),
    ...partsToKpiOptions(nextParts),
  };
  if (elementId === "kpiIcon") nextOptions.showIcon = enabled;
  if (elementId === "kpiTitle") nextOptions.showTitle = enabled;
  if (elementId === "kpiHint" && !enabled) nextOptions.subtitle = undefined;
  if (elementId === "kpiHint" && enabled && !nextOptions.subtitle) {
    nextOptions.subtitle = " ";
    nextParts = upsertKpiPartState(nextParts, ref, { visible: true, content: " " });
  }
  if (elementId === "kpiComparison") {
    nextOptions.showComparison = enabled;
    if (enabled && (nextOptions.comparisonMode == null || nextOptions.comparisonMode === "none")) {
      nextOptions.comparisonMode = "target";
    }
    if (!enabled) nextOptions.comparisonMode = "none";
  }
  if (elementId === "kpiProgress") {
    nextOptions.showProgress = enabled;
    /* Looker: progresso e sparkline mutuamente exclusivos. */
    if (enabled) {
      nextOptions.showSparkline = false;
      nextParts = upsertKpiPartState(nextParts, { kind: "sparkline" }, { visible: false });
    }
  }
  if (elementId === "kpiSparkline") {
    nextOptions.showSparkline = enabled;
    if (enabled) {
      nextOptions.showProgress = false;
      nextParts = upsertKpiPartState(nextParts, { kind: "progress" }, { visible: false });
    }
  }
  nextParts = mergeKpiPartsWithOptions(nextParts, nextOptions);
  return { options: nextOptions, parts: nextParts };
}

export function isKpiElementOpenForPart(
  elementId: KpiElementId,
  part?: KpiPartRef | null,
): boolean {
  if (!part) return false;
  return kpiElementIdForPartRef(part) === elementId;
}

export function setKpiElementEnabled(
  elementId: KpiElementId,
  enabled: boolean,
  options?: KpiCardFlatOptions | null,
  parts?: KpiPartsMap | null,
): { options: KpiCardFlatOptions; parts: KpiPartsMap } {
  return applyKpiElementVisibility(elementId, enabled, options, parts);
}

/** Presets de frames % (Onda D) — aplicados via seed de layout livre. */
export const KPI_LAYOUT_PRESET_FRAMES: Record<
  "compact" | "ban" | "scorecard",
  Partial<Record<keyof typeof KPI_PART_DEFAULT_FRAMES, { x: number; y: number; w?: number; h?: number }>>
> = {
  compact: {
    title: { x: 4, y: 6, w: 70, h: 18 },
    value: { x: 4, y: 28, w: 92, h: 48 },
    hint: { x: 4, y: 78, w: 70, h: 14 },
    icon: { x: 78, y: 6, w: 18, h: 20 },
    comparison: { x: 4, y: 72, w: 60, h: 12 },
    sparkline: { x: 62, y: 70, w: 34, h: 22 },
    progress: { x: 4, y: 90, w: 92, h: 6 },
  },
  ban: {
    title: { x: 4, y: 4, w: 72, h: 16 },
    value: { x: 4, y: 22, w: 72, h: 42 },
    comparison: { x: 4, y: 66, w: 55, h: 14 },
    sparkline: { x: 60, y: 58, w: 36, h: 28 },
    hint: { x: 4, y: 82, w: 55, h: 12 },
    icon: { x: 80, y: 4, w: 16, h: 18 },
    progress: { x: 4, y: 92, w: 92, h: 5 },
  },
  scorecard: {
    title: { x: 4, y: 4, w: 70, h: 14 },
    value: { x: 4, y: 20, w: 60, h: 40 },
    comparison: { x: 4, y: 62, w: 50, h: 12 },
    progress: { x: 4, y: 78, w: 92, h: 8 },
    hint: { x: 4, y: 88, w: 70, h: 10 },
    icon: { x: 78, y: 4, w: 18, h: 18 },
    sparkline: { x: 62, y: 52, w: 34, h: 22 },
  },
};

export function applyKpiLayoutPreset(
  preset: "compact" | "ban" | "scorecard" | "free",
  options?: KpiCardFlatOptions | null,
  parts?: KpiPartsMap | null,
): { options: KpiCardFlatOptions; parts: KpiPartsMap } {
  const baseOptions: KpiCardFlatOptions = { ...(options ?? {}) };
  let nextParts = mergeKpiPartsWithOptions(parts, baseOptions);

  if (preset === "free") {
    nextParts = seedKpiPartsFreeLayoutFrames(nextParts);
    return { options: baseOptions, parts: nextParts };
  }

  const frames = KPI_LAYOUT_PRESET_FRAMES[preset];
  nextParts = seedKpiPartsFreeLayoutFrames(nextParts);
  for (const [kind, frame] of Object.entries(frames)) {
    if (
      kind !== "card" &&
      kind !== "title" &&
      kind !== "value" &&
      kind !== "hint" &&
      kind !== "icon" &&
      kind !== "comparison" &&
      kind !== "progress" &&
      kind !== "sparkline"
    ) {
      continue;
    }
    nextParts = upsertKpiPartState(nextParts, { kind }, { frame });
  }

  if (preset === "ban") {
    baseOptions.showComparison = true;
    if (baseOptions.comparisonMode == null || baseOptions.comparisonMode === "none") {
      baseOptions.comparisonMode = "previous";
    }
    baseOptions.showSparkline = true;
    baseOptions.showProgress = false;
    nextParts = upsertKpiPartState(nextParts, { kind: "comparison" }, { visible: true });
    nextParts = upsertKpiPartState(nextParts, { kind: "sparkline" }, { visible: true });
    nextParts = upsertKpiPartState(nextParts, { kind: "progress" }, { visible: false });
  }
  if (preset === "scorecard") {
    baseOptions.showComparison = true;
    if (baseOptions.comparisonMode == null || baseOptions.comparisonMode === "none") {
      baseOptions.comparisonMode = "target";
    }
    baseOptions.showProgress = true;
    baseOptions.showSparkline = false;
    nextParts = upsertKpiPartState(nextParts, { kind: "comparison" }, { visible: true });
    nextParts = upsertKpiPartState(nextParts, { kind: "progress" }, { visible: true });
    nextParts = upsertKpiPartState(nextParts, { kind: "sparkline" }, { visible: false });
  }

  nextParts = mergeKpiPartsWithOptions(nextParts, baseOptions);
  return { options: baseOptions, parts: nextParts };
}

export function applyKpiAddElementChoice(
  choiceId: KpiAddElementChoiceId,
  options?: KpiCardFlatOptions | null,
  parts?: KpiPartsMap | null,
): { options: KpiCardFlatOptions; parts: KpiPartsMap } {
  switch (choiceId) {
    case "title:on":
      return applyKpiElementVisibility("kpiTitle", true, options, parts);
    case "title:off":
      return applyKpiElementVisibility("kpiTitle", false, options, parts);
    case "hint:on":
      return applyKpiElementVisibility("kpiHint", true, options, parts);
    case "hint:off":
      return applyKpiElementVisibility("kpiHint", false, options, parts);
    case "icon:on":
      return applyKpiElementVisibility("kpiIcon", true, options, parts);
    case "icon:off":
      return applyKpiElementVisibility("kpiIcon", false, options, parts);
    case "comparison:off":
      return applyKpiElementVisibility("kpiComparison", false, options, parts);
    case "comparison:target": {
      const enabled = applyKpiElementVisibility("kpiComparison", true, options, parts);
      return {
        options: { ...enabled.options, comparisonMode: "target" },
        parts: enabled.parts,
      };
    }
    case "comparison:previous": {
      const enabled = applyKpiElementVisibility("kpiComparison", true, options, parts);
      return {
        options: { ...enabled.options, comparisonMode: "previous" },
        parts: enabled.parts,
      };
    }
    case "progress:on":
      return applyKpiElementVisibility("kpiProgress", true, options, parts);
    case "progress:off":
      return applyKpiElementVisibility("kpiProgress", false, options, parts);
    case "sparkline:on":
      return applyKpiElementVisibility("kpiSparkline", true, options, parts);
    case "sparkline:off":
      return applyKpiElementVisibility("kpiSparkline", false, options, parts);
    case "layout:compact":
      return applyKpiLayoutPreset("compact", options, parts);
    case "layout:ban":
      return applyKpiLayoutPreset("ban", options, parts);
    case "layout:scorecard":
      return applyKpiLayoutPreset("scorecard", options, parts);
    case "layout:free":
      return applyKpiLayoutPreset("free", options, parts);
    default: {
      const _exhaustive: never = choiceId;
      return _exhaustive;
    }
  }
}

export function applyKpiAddElementChoiceWithParts(
  choiceId: KpiAddElementChoiceId,
  options?: KpiCardFlatOptions | null,
  parts?: KpiPartsMap | null,
): { options: KpiCardFlatOptions; parts: KpiPartsMap } {
  return applyKpiAddElementChoice(choiceId, options, parts);
}

export function isKpiAddElementChoiceActive(
  choiceId: KpiAddElementChoiceId,
  options?: KpiCardFlatOptions | null,
  parts?: KpiPartsMap | null,
): boolean {
  switch (choiceId) {
    case "title:on":
      return isKpiElementEnabled("kpiTitle", options, parts);
    case "title:off":
      return !isKpiElementEnabled("kpiTitle", options, parts);
    case "hint:on":
      return isKpiElementEnabled("kpiHint", options, parts);
    case "hint:off":
      return !isKpiElementEnabled("kpiHint", options, parts);
    case "icon:on":
      return isKpiElementEnabled("kpiIcon", options, parts);
    case "icon:off":
      return !isKpiElementEnabled("kpiIcon", options, parts);
    case "comparison:off":
      return !isKpiElementEnabled("kpiComparison", options, parts);
    case "comparison:target":
      return (
        isKpiElementEnabled("kpiComparison", options, parts) &&
        (options?.comparisonMode ?? "target") === "target"
      );
    case "comparison:previous":
      return (
        isKpiElementEnabled("kpiComparison", options, parts) &&
        options?.comparisonMode === "previous"
      );
    case "progress:on":
      return isKpiElementEnabled("kpiProgress", options, parts);
    case "progress:off":
      return !isKpiElementEnabled("kpiProgress", options, parts);
    case "sparkline:on":
      return isKpiElementEnabled("kpiSparkline", options, parts);
    case "sparkline:off":
      return !isKpiElementEnabled("kpiSparkline", options, parts);
    case "layout:compact":
    case "layout:ban":
    case "layout:scorecard":
    case "layout:free":
      return false;
    default: {
      const _exhaustive: never = choiceId;
      return _exhaustive;
    }
  }
}

export function kpiElementIdForAddChoice(choiceId: KpiAddElementChoiceId): KpiElementId {
  if (choiceId.startsWith("title:")) return "kpiTitle";
  if (choiceId.startsWith("hint:")) return "kpiHint";
  if (choiceId.startsWith("icon:")) return "kpiIcon";
  if (choiceId.startsWith("comparison:")) return "kpiComparison";
  if (choiceId.startsWith("progress:")) return "kpiProgress";
  if (choiceId.startsWith("sparkline:")) return "kpiSparkline";
  return "kpiCard";
}

export { kpiOptionsToParts };
