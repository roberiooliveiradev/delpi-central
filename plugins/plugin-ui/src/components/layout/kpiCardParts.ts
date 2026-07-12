/**
 * Partes endereçáveis do card KPI — mesmo padrão de ChartPartRef / TablePartRef.
 */

import type { MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent } from "react";

import type { MetricKpiCardTone } from "../layout/MetricKpiCard";

export const KPI_PART_DATA_ATTR = "data-kpi-part";

export type KpiPartRef =
  | { kind: "card" }
  | { kind: "title" }
  | { kind: "value" }
  | { kind: "hint" }
  | { kind: "icon" };

export type KpiPartStyle = {
  fill?: string;
  color?: string;
  fontWeight?: string | number;
  opacity?: number;
  /** Contorno do card (herda chrome de forma). */
  stroke?: string;
  strokeWidth?: number;
  /** Cantos arredondados do card (px). */
  borderRadius?: number;
};

export type KpiPartState = {
  visible?: boolean;
  style?: KpiPartStyle;
  content?: string;
};

export type KpiPartsMap = Record<string, KpiPartState>;

export type KpiCardInteraction = {
  selectedPart?: KpiPartRef | null;
  editingPart?: KpiPartRef | null;
  onPartPointerDown?: (ref: KpiPartRef, event: ReactPointerEvent) => void;
  onPartDoubleClick?: (ref: KpiPartRef, event: ReactPointerEvent | ReactMouseEvent) => void;
  onPartContentCommit?: (ref: KpiPartRef, content: string) => void;
  onPartEditCancel?: () => void;
};

export type KpiPartCapabilities = {
  movable: boolean;
  editable: boolean;
  deletable: boolean;
  resizable: boolean;
};

const KPI_PART_KIND_CAPABILITIES: Record<KpiPartRef["kind"], KpiPartCapabilities> = {
  card: { movable: false, editable: false, deletable: false, resizable: false },
  title: { movable: false, editable: true, deletable: true, resizable: false },
  value: { movable: false, editable: false, deletable: false, resizable: false },
  hint: { movable: false, editable: true, deletable: true, resizable: false },
  icon: { movable: false, editable: false, deletable: true, resizable: false },
};

/** Options flat do card (legado / inspetor) — espelho de SeriesChartOptions. */
export type KpiCardFlatOptions = {
  title?: string;
  subtitle?: string;
  unit?: string;
  iconName?: string;
  showIcon?: boolean;
  /** Quando false, oculta o rótulo (persistido como `title.visible`). */
  showTitle?: boolean;
  tone?: MetricKpiCardTone;
  valueColor?: string;
  backgroundColor?: string;
  valueFormat?: "number" | "percent" | "compact" | "raw";
};

export function serializeKpiPartRef(ref: KpiPartRef): string {
  return ref.kind;
}

export function parseKpiPartRef(raw: string | null | undefined): KpiPartRef | null {
  const value = (raw ?? "").trim();
  if (value === "card" || value === "title" || value === "value" || value === "hint" || value === "icon") {
    return { kind: value };
  }
  return null;
}

export function isKpiPartRefEqual(a?: KpiPartRef | null, b?: KpiPartRef | null): boolean {
  if (!a || !b) return false;
  return a.kind === b.kind;
}

export function kpiPartCapabilities(ref: KpiPartRef): KpiPartCapabilities {
  return KPI_PART_KIND_CAPABILITIES[ref.kind];
}

export function kpiPartAllowsDelete(ref: KpiPartRef): boolean {
  return kpiPartCapabilities(ref).deletable;
}

export function kpiPartAllowsEdit(ref: KpiPartRef): boolean {
  return kpiPartCapabilities(ref).editable;
}

export function getKpiPartState(
  parts: KpiPartsMap | null | undefined,
  ref: KpiPartRef,
): KpiPartState | undefined {
  return parts?.[serializeKpiPartRef(ref)];
}

export function upsertKpiPartState(
  parts: KpiPartsMap | null | undefined,
  ref: KpiPartRef,
  patch: KpiPartState,
): KpiPartsMap {
  const key = serializeKpiPartRef(ref);
  const prev = parts?.[key] ?? {};
  return {
    ...(parts ?? {}),
    [key]: {
      ...prev,
      ...patch,
      style: patch.style ? { ...prev.style, ...patch.style } : prev.style,
    },
  };
}

export function kpiPartDomProps(ref: KpiPartRef, selectedPart?: KpiPartRef | null) {
  const selected = isKpiPartRefEqual(ref, selectedPart);
  return {
    [KPI_PART_DATA_ATTR]: serializeKpiPartRef(ref),
    "aria-selected": selected ? true : undefined,
  };
}

export function bindKpiPartPointer(ref: KpiPartRef, interaction?: KpiCardInteraction | null) {
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const selected = isKpiPartRefEqual(ref, interaction?.selectedPart);
  const editing = isKpiPartRefEqual(ref, interaction?.editingPart);
  const dom = kpiPartDomProps(ref, interaction?.selectedPart);

  if (!interactive) {
    return {
      ...dom,
      selected,
      editing,
      onPointerDown: undefined as undefined,
      onDoubleClick: undefined as undefined,
    };
  }

  return {
    ...dom,
    selected,
    editing,
    onPointerDown: (event: ReactPointerEvent) => {
      event.stopPropagation();
      interaction?.onPartPointerDown?.(ref, event);
    },
    onDoubleClick: (event: ReactMouseEvent) => {
      event.stopPropagation();
      event.preventDefault();
      interaction?.onPartDoubleClick?.(ref, event);
    },
  };
}

export function findKpiPartFromTarget(target: EventTarget | null): KpiPartRef | null {
  if (!(target instanceof Element)) return null;
  const host = target.closest(`[${KPI_PART_DATA_ATTR}]`);
  if (!host) return null;
  return parseKpiPartRef(host.getAttribute(KPI_PART_DATA_ATTR));
}

export function kpiOptionsToParts(options?: KpiCardFlatOptions | null): KpiPartsMap {
  return {
    card: {
      visible: true,
      style: {
        fill: options?.backgroundColor,
      },
    },
    title: {
      visible: options?.showTitle !== false,
      content: options?.title,
    },
    value: {
      visible: true,
      style: { color: options?.valueColor },
    },
    hint: {
      visible: Boolean(options?.subtitle?.trim()),
      content: options?.subtitle,
    },
    icon: {
      visible: options?.showIcon !== false,
    },
  };
}

export function partsToKpiOptions(parts?: KpiPartsMap | null): Partial<KpiCardFlatOptions> {
  if (!parts) return {};
  const patch: Partial<KpiCardFlatOptions> = {};
  const title = parts.title;
  const hint = parts.hint;
  const icon = parts.icon;
  const card = parts.card;
  const value = parts.value;
  if (title?.content != null) patch.title = title.content;
  if (title?.visible != null) patch.showTitle = title.visible !== false;
  if (hint?.content != null) patch.subtitle = hint.content;
  if (hint?.visible === false) patch.subtitle = undefined;
  if (icon?.visible != null) patch.showIcon = icon.visible !== false;
  if (card?.style?.fill !== undefined) patch.backgroundColor = card.style.fill;
  if (value?.style?.color !== undefined) patch.valueColor = value.style.color;
  return patch;
}

export function mergeKpiPartsWithOptions(
  parts: KpiPartsMap | null | undefined,
  options?: KpiCardFlatOptions | null,
): KpiPartsMap {
  const fromOptions = kpiOptionsToParts(options);
  const merged: KpiPartsMap = { ...fromOptions };
  for (const [key, state] of Object.entries(parts ?? {})) {
    merged[key] = {
      ...fromOptions[key],
      ...state,
      style: { ...fromOptions[key]?.style, ...state.style },
    };
  }
  return merged;
}

export function normalizeKpiPartsForLoad(
  parts: KpiPartsMap | null | undefined,
  options?: KpiCardFlatOptions | null,
): KpiPartsMap {
  return mergeKpiPartsWithOptions(parts, options);
}

export function deleteKpiPart(
  parts: KpiPartsMap | null | undefined,
  ref: KpiPartRef,
  options?: KpiCardFlatOptions | null,
): { parts: KpiPartsMap; options: KpiCardFlatOptions } {
  const nextParts = upsertKpiPartState(parts, ref, { visible: false });
  const nextOptions: KpiCardFlatOptions = {
    ...(options ?? {}),
    ...partsToKpiOptions(nextParts),
  };
  if (ref.kind === "icon") nextOptions.showIcon = false;
  if (ref.kind === "title") nextOptions.showTitle = false;
  if (ref.kind === "hint") nextOptions.subtitle = undefined;
  return { parts: nextParts, options: nextOptions };
}

export function isKpiPartVisible(
  parts: KpiPartsMap | null | undefined,
  ref: KpiPartRef,
  fallback = true,
): boolean {
  const state = getKpiPartState(parts, ref);
  if (state?.visible == null) return fallback;
  return state.visible !== false;
}
