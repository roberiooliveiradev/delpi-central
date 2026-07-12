/**
 * Catálogo de elementos do KPI (ligar/desligar famílias de partes) — espelho de seriesChartElementCatalog.
 */

import type { KpiCardFlatOptions, KpiPartRef, KpiPartsMap } from "./kpiCardParts";
import {
  kpiOptionsToParts,
  mergeKpiPartsWithOptions,
  partsToKpiOptions,
  upsertKpiPartState,
} from "./kpiCardParts";

export type KpiElementId = "kpiTitle" | "kpiValue" | "kpiHint" | "kpiIcon" | "kpiCard";

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
];

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
  if (elementId === "kpiHint") {
    if (state?.visible === false) return false;
    return Boolean(options?.subtitle?.trim() || state?.content?.trim() || state?.visible === true);
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
  if (elementId === "kpiHint" && !enabled) nextOptions.subtitle = undefined;
  if (elementId === "kpiHint" && enabled && !nextOptions.subtitle) {
    nextOptions.subtitle = " ";
    nextParts = upsertKpiPartState(nextParts, ref, { visible: true, content: " " });
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

export { kpiOptionsToParts };
