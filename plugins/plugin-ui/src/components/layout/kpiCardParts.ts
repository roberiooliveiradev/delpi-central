/**
 * Partes endereçáveis do card KPI — mesmo padrão de ChartPartRef / TablePartRef.
 */

import type {
  CSSProperties,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
} from "react";

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
  fontFamily?: string;
  fontSize?: number;
  fontWeight?: string | number;
  fontStyle?: string;
  textDecoration?: string;
  textAlign?: "left" | "center" | "right" | "justify";
  verticalAlign?: "top" | "middle" | "bottom";
  opacity?: number;
  /** Contorno do card/ícone (herda chrome de forma). */
  stroke?: string;
  strokeWidth?: number;
  /** Cantos arredondados (px). */
  borderRadius?: number;
  /**
   * Tamanho do box do ícone em px quando sem `frame`.
   * Com `frame`, largura/altura vêm de `frame.w`/`frame.h` (% do card).
   */
  iconSize?: number;
};

/** Frame relativo ao card (0–100%), como chartParts title/legend. */
export type KpiPartFrame = {
  x: number;
  y: number;
  w?: number;
  h?: number;
};

export type KpiPartState = {
  visible?: boolean;
  style?: KpiPartStyle;
  content?: string;
  /** Posição/tamanho do ícone (% do card). */
  frame?: KpiPartFrame;
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
  icon: { movable: true, editable: false, deletable: true, resizable: true },
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

/** Frame padrão do ícone (canto superior direito). */
export const KPI_ICON_DEFAULT_FRAME: KpiPartFrame = { x: 78, y: 8, w: 14, h: 28 };

export const KPI_ICON_DEFAULT_SIZE_PX = 44;
export const KPI_ICON_DEFAULT_RADIUS_PX = 14;

export function clampKpiPartFrame(frame: KpiPartFrame): KpiPartFrame {
  const w = Math.max(4, Math.min(80, frame.w ?? KPI_ICON_DEFAULT_FRAME.w ?? 14));
  const h = Math.max(4, Math.min(80, frame.h ?? KPI_ICON_DEFAULT_FRAME.h ?? 28));
  return {
    x: Math.max(0, Math.min(100 - w, frame.x)),
    y: Math.max(0, Math.min(100 - h, frame.y)),
    w,
    h,
  };
}

export function resolveKpiIconFrame(
  state: KpiPartState | null | undefined,
): KpiPartFrame | null {
  if (!state?.frame) return null;
  return clampKpiPartFrame(state.frame);
}

/** Estilo do box do ícone a partir de `kpiParts.icon` (cores, raio, frame/% ou size px). */
export function resolveKpiIconBoxStyle(
  state: KpiPartState | null | undefined,
): CSSProperties {
  const style = state?.style;
  const frame = resolveKpiIconFrame(state);
  const css: CSSProperties = {};

  if (style?.fill != null && style.fill !== "") css.background = style.fill;
  if (style?.color) css.color = style.color;
  if (style?.stroke != null && style.stroke !== "") {
    css.borderColor = style.stroke;
    css.borderStyle = "solid";
  }
  if (style?.strokeWidth != null) {
    css.borderWidth = `${Math.max(0, style.strokeWidth)}px`;
    if (style.strokeWidth > 0 && !css.borderStyle) css.borderStyle = "solid";
  }
  if (style?.borderRadius != null) {
    css.borderRadius = `${Math.max(0, style.borderRadius)}px`;
  }
  if (style?.opacity != null) css.opacity = style.opacity;

  if (frame) {
    css.position = "absolute";
    css.left = `${frame.x}%`;
    css.top = `${frame.y}%`;
    css.width = `${frame.w}%`;
    css.height = `${frame.h}%`;
    css.alignSelf = "auto";
    css.zIndex = 2;
  } else if (style?.iconSize != null && Number.isFinite(style.iconSize) && style.iconSize > 0) {
    const size = Math.max(16, Math.min(160, Math.round(style.iconSize)));
    css.width = `${size}px`;
    css.height = `${size}px`;
  }

  return css;
}

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

export type KpiPartStatePatch = Omit<KpiPartState, "frame" | "style"> & {
  style?: Partial<KpiPartStyle>;
  /** `null` remove o frame (ex.: voltar ao tamanho em px). */
  frame?: KpiPartFrame | null;
};

export function upsertKpiPartState(
  parts: KpiPartsMap | null | undefined,
  ref: KpiPartRef,
  patch: KpiPartStatePatch,
): KpiPartsMap {
  const key = serializeKpiPartRef(ref);
  const prev = parts?.[key] ?? {};
  const nextFrame =
    patch.frame === null
      ? undefined
      : patch.frame !== undefined
        ? clampKpiPartFrame({ ...(prev.frame ?? {}), ...patch.frame })
        : prev.frame;
  const { frame: _ignored, ...restPatch } = patch;
  return {
    ...(parts ?? {}),
    [key]: {
      ...prev,
      ...restPatch,
      style: patch.style ? { ...prev.style, ...patch.style } : prev.style,
      frame: nextFrame,
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

/** Tipografia + alinhamento de parte textual do KPI (title/value/hint). */
export function resolveKpiPartTypographyStyle(
  style: KpiPartStyle | null | undefined,
  options?: { flexPart?: boolean },
): CSSProperties | undefined {
  if (!style) return undefined;
  const css: CSSProperties = {};
  if (style.fontFamily) css.fontFamily = style.fontFamily;
  if (style.fontSize != null && Number.isFinite(style.fontSize)) {
    css.fontSize = `${style.fontSize}px`;
  }
  if (style.fontWeight != null) css.fontWeight = style.fontWeight;
  if (style.fontStyle) css.fontStyle = style.fontStyle;
  if (style.textDecoration) css.textDecoration = style.textDecoration;
  if (style.color) css.color = style.color;
  if (style.textAlign) css.textAlign = style.textAlign;

  const flexPart = options?.flexPart ?? false;
  if (flexPart) {
    if (style.textAlign === "left") css.justifyContent = "flex-start";
    else if (style.textAlign === "right") css.justifyContent = "flex-end";
    else if (style.textAlign === "center" || style.textAlign === "justify") {
      css.justifyContent = "center";
    }
    if (style.verticalAlign === "top") css.alignItems = "flex-start";
    else if (style.verticalAlign === "middle") css.alignItems = "center";
    else if (style.verticalAlign === "bottom") css.alignItems = "flex-end";
  } else {
    if (style.textAlign) {
      css.width = "100%";
      css.display = "flex";
      css.flexWrap = "wrap";
      css.justifyContent =
        style.textAlign === "right"
          ? "flex-end"
          : style.textAlign === "center" || style.textAlign === "justify"
            ? "center"
            : "flex-start";
    }
  }

  return Object.keys(css).length > 0 ? css : undefined;
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
      frame: state.frame ?? fromOptions[key]?.frame,
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
