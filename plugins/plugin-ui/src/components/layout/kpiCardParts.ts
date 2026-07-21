/**
 * Partes endereçáveis do card KPI — mesmo padrão de ChartPartRef / TablePartRef.
 */

import type {
  CSSProperties,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
} from "react";

import type { MetricKpiCardTone } from "../layout/MetricKpiCard";
import { AUTOMATIC_TEXT_COLOR, isAutomaticTextColor, resolvePaintTextColor } from "../shape/colorUtils";
import { applyTextEffectStyleToCss } from "../shape/textEffectStyle";
import { DECK_KPI_DEFAULTS } from "../../theme/deckColorCatalog";
import { resolveTextPartColumnBoxLayout } from "../../utils/textPartBoxLayout";

export const KPI_PART_DATA_ATTR = "data-kpi-part";

export type KpiPartRef =
  | { kind: "card" }
  | { kind: "title" }
  | { kind: "value" }
  | { kind: "hint" }
  | { kind: "icon" }
  /** Card individual em KPI multi-métrica (seleção no palco). */
  | { kind: "metricCard"; field: string };

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
  /** Sombra do box (CSS box-shadow) — tipicamente na parte `card`. */
  boxShadow?: string;
  /** Sombra tipográfica (CSS text-shadow). */
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  textReflection?: boolean;
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
  /** Arrastar parte já selecionada (frame % relativo ao card). */
  onPartMovePointerDown?: (ref: KpiPartRef, event: ReactPointerEvent) => void;
  /** Resize pelos handles (paridade com chart_view). */
  onPartResizePointerDown?: (
    ref: KpiPartRef,
    event: ReactPointerEvent,
    handle: KpiPartResizeHandle,
  ) => void;
  /** Materializa frame % medido no DOM (seleção sem frame prévio). */
  onPartFrameChange?: (ref: KpiPartRef, frame: KpiPartFrame) => void;
  /** Handle amarelo — raio dos cantos da parte (px). */
  onPartCornerAdjustPointerDown?: (ref: KpiPartRef, event: ReactPointerEvent) => void;
};

export type KpiPartResizeHandle = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";

export const KPI_PART_RESIZE_HANDLES: KpiPartResizeHandle[] = [
  "nw",
  "n",
  "ne",
  "e",
  "se",
  "s",
  "sw",
  "w",
];

export type KpiPartCapabilities = {
  movable: boolean;
  editable: boolean;
  deletable: boolean;
  resizable: boolean;
};

const KPI_PART_KIND_CAPABILITIES: Record<KpiPartRef["kind"], KpiPartCapabilities> = {
  /** Fundo: geometria % do bloco (escopo de parte — não confunde com resize global do widget). */
  card: { movable: true, editable: false, deletable: false, resizable: true },
  title: { movable: true, editable: true, deletable: true, resizable: true },
  value: { movable: true, editable: false, deletable: false, resizable: true },
  hint: { movable: true, editable: true, deletable: true, resizable: true },
  icon: { movable: true, editable: false, deletable: true, resizable: true },
  metricCard: { movable: false, editable: true, deletable: false, resizable: false },
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
  valueFormat?: "number" | "percent" | "compact" | "raw" | "currency";
};

/** Frame padrão do ícone (canto superior direito). */
export const KPI_ICON_DEFAULT_FRAME: KpiPartFrame = { x: 78, y: 8, w: 18, h: 30 };

/**
 * Frames iniciais (%). Card = fundo relativo ao bloco; demais = relativos ao card.
 * Empilhamento balanceado (rótulo → valor → hint) com ícone no canto — usar sempre em lote.
 */
export const KPI_PART_DEFAULT_FRAMES: Record<
  "card" | "title" | "value" | "hint" | "icon",
  KpiPartFrame
> = {
  card: { x: 0, y: 0, w: 100, h: 100 },
  title: { x: 5, y: 8, w: 70, h: 16 },
  value: { x: 5, y: 26, w: 90, h: 48 },
  hint: { x: 5, y: 78, w: 72, h: 14 },
  icon: KPI_ICON_DEFAULT_FRAME,
};

/** Partes do layout livre (sem o fundo `card`). */
export const KPI_FREE_LAYOUT_PART_KINDS = ["title", "value", "hint", "icon"] as const;

export type KpiFreeLayoutPartKind = (typeof KPI_FREE_LAYOUT_PART_KINDS)[number];

export const KPI_ICON_DEFAULT_SIZE_PX = 36;
export const KPI_ICON_DEFAULT_RADIUS_PX = 12;

/**
 * Track do handle amarelo de cantos — mesmo padrão do `cornerSpec` (bloco/forma).
 * Move ao longo do topo (12%→50%); valor 0–0.5 = fração do lado curto.
 */
const KPI_CORNER_TRACK_START = 12;
const KPI_CORNER_TRACK_END = 50;
const KPI_CORNER_TRACK = KPI_CORNER_TRACK_END - KPI_CORNER_TRACK_START;
const KPI_CORNER_ADJ_MAX = 0.5;

function clampKpiCorner(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function borderRadiusPxToKpiCornerAdj(px: number, shortSidePx: number): number {
  if (!(shortSidePx > 0)) return clampKpiCorner(px / 64, 0, KPI_CORNER_ADJ_MAX);
  return clampKpiCorner(px / shortSidePx, 0, KPI_CORNER_ADJ_MAX);
}

export function kpiCornerAdjToBorderRadiusPx(adj: number, shortSidePx: number): number {
  return Math.round(
    clampKpiCorner(adj, 0, KPI_CORNER_ADJ_MAX) * Math.max(0, shortSidePx),
  );
}

/** Posição % do handle amarelo no bbox da parte (igual chrome do bloco). */
export function kpiPartCornerAdjustCssPosition(
  borderRadiusPx: number,
  shortSidePx: number,
): { left: string; top: string } {
  const adj = borderRadiusPxToKpiCornerAdj(borderRadiusPx, shortSidePx);
  const x = clampKpiCorner(
    KPI_CORNER_TRACK_START + (adj / KPI_CORNER_ADJ_MAX) * KPI_CORNER_TRACK,
    KPI_CORNER_TRACK_START,
    KPI_CORNER_TRACK_END,
  );
  return { left: `${x}%`, top: "0%" };
}

/** Converte ponteiro local X (0–100 % no bbox) → ajuste 0–0.5. */
export function kpiPartCornerAdjFromLocalX(localX: number): number {
  return clampKpiCorner(
    ((localX - KPI_CORNER_TRACK_START) / KPI_CORNER_TRACK) * KPI_CORNER_ADJ_MAX,
    0,
    KPI_CORNER_ADJ_MAX,
  );
}

/** Tipografia padrão das partes — mesma base da ribbon Formatar / slide TV. */
export const KPI_PART_FONT_SIZE_DEFAULTS = {
  title: 18,
  /** Valor do card — legível no deck TV sem depender de FitText agressivo. */
  value: 40,
  hint: 14,
} as const;

export type KpiTextPartKind = keyof typeof KPI_PART_FONT_SIZE_DEFAULTS;
export type KpiFramePartKind = keyof typeof KPI_PART_DEFAULT_FRAMES;

export function resolveKpiPartFontSize(
  kind: KpiTextPartKind,
  style?: KpiPartStyle | null,
): number {
  const explicit = style?.fontSize;
  if (explicit != null && Number.isFinite(explicit) && explicit > 0) {
    return Math.round(explicit);
  }
  return KPI_PART_FONT_SIZE_DEFAULTS[kind];
}

export function kpiPartAllowsFrame(ref: KpiPartRef): boolean {
  return (
    ref.kind === "card" ||
    ref.kind === "title" ||
    ref.kind === "value" ||
    ref.kind === "hint" ||
    ref.kind === "icon"
  );
}

/**
 * Alvo do chrome Preench./Contorno na ribbon Forma.
 * Sem parte → seleção global do widget (sem chrome de fundo).
 * Fundo do KPI = parte `card` selecionada explicitamente.
 */
export function resolveKpiShapeChromePartRef(
  selectedPart: KpiPartRef | null | undefined,
): KpiPartRef | null {
  if (!selectedPart) return null;
  if (selectedPart.kind === "card" || kpiPartAllowsFrame(selectedPart)) {
    return selectedPart;
  }
  return null;
}

export function defaultKpiPartFrame(kind: KpiFramePartKind): KpiPartFrame {
  return { ...KPI_PART_DEFAULT_FRAMES[kind] };
}

export function clampKpiPartFrame(frame: KpiPartFrame): KpiPartFrame {
  const w = Math.max(4, Math.min(100, frame.w ?? KPI_ICON_DEFAULT_FRAME.w ?? 14));
  const h = Math.max(4, Math.min(100, frame.h ?? KPI_ICON_DEFAULT_FRAME.h ?? 28));
  return {
    x: Math.max(0, Math.min(100 - w, frame.x)),
    y: Math.max(0, Math.min(100 - h, frame.y)),
    w,
    h,
  };
}

/** Aplica delta % de resize no frame da parte (igual handles do bloco/chart). */
export function resizeKpiPartFrame(
  frame: KpiPartFrame,
  handle: KpiPartResizeHandle,
  dx: number,
  dy: number,
): KpiPartFrame {
  let x = frame.x;
  let y = frame.y;
  let w = frame.w ?? 20;
  let h = frame.h ?? 20;
  switch (handle) {
    case "se":
      w += dx;
      h += dy;
      break;
    case "e":
      w += dx;
      break;
    case "s":
      h += dy;
      break;
    case "n":
      y += dy;
      h -= dy;
      break;
    case "w":
      x += dx;
      w -= dx;
      break;
    case "ne":
      y += dy;
      h -= dy;
      w += dx;
      break;
    case "nw":
      x += dx;
      y += dy;
      w -= dx;
      h -= dy;
      break;
    case "sw":
      x += dx;
      w -= dx;
      h += dy;
      break;
    default:
      break;
  }
  return clampKpiPartFrame({ x, y, w, h });
}

/**
 * Raiz de coordenadas % das partes.
 * Fundo (`card`) = shell do bloco; demais = article do card.
 */
export function resolveKpiPartFrameRoot(
  fromEl: HTMLElement | null,
  ref?: KpiPartRef | null,
): HTMLElement | null {
  if (!fromEl) return null;
  if (ref?.kind === "card") {
    return fromEl.closest(".delpi-kpi-card-shell");
  }
  return fromEl.closest(".delpi-kpi-card");
}

export function resolveKpiPartFrame(
  state: KpiPartState | null | undefined,
): KpiPartFrame | null {
  if (!state?.frame) return null;
  return clampKpiPartFrame(state.frame);
}

/** Fill/borda de caixa ativos (não transparentes / espessura > 0). */
export function kpiPartHasBoxPaint(style?: KpiPartStyle | null): boolean {
  if (!style) return false;
  const fill = style.fill?.trim();
  const hasFill = Boolean(fill && fill !== "transparent" && fill !== "none");
  const stroke = style.stroke?.trim();
  const strokeWidth = style.strokeWidth ?? 0;
  const hasStroke = Boolean(stroke && stroke !== "transparent" && stroke !== "none" && strokeWidth > 0);
  return hasFill || hasStroke;
}

/**
 * Layout absoluto (% do card) + chrome (raio/fundo/contorno).
 * Sem frame: se há fill/borda em parte textual, a caixa abraça o conteúdo
 * (não estica com flex:1 do valor). A parte `card` é a moldura do bloco —
 * nunca encolhe com fit-content.
 */
export function resolveKpiPartLayoutStyle(
  state: KpiPartState | null | undefined,
  options?: { iconSizeFallback?: boolean; partKind?: KpiPartRef["kind"] },
): CSSProperties {
  const style = state?.style;
  const frame = resolveKpiPartFrame(state);
  const css: CSSProperties = {};

  if (style?.fill != null && style.fill !== "") css.background = style.fill;
  /* Nunca gravar sentinel `auto` em CSS — inválido e perde para accent do tema. */
  if (style?.color && !isAutomaticTextColor(style.color)) {
    css.color = style.color;
  }
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
  if (style?.boxShadow != null && style.boxShadow !== "") {
    css.boxShadow = style.boxShadow;
  }
  if (style?.opacity != null) css.opacity = style.opacity;

  if (frame) {
    css.position = "absolute";
    css.left = `${frame.x}%`;
    css.top = `${frame.y}%`;
    css.width = `${frame.w}%`;
    css.height = `${frame.h}%`;
    css.maxWidth = "100%";
    css.maxHeight = "100%";
    css.minWidth = 0;
    css.minHeight = 0;
    css.alignSelf = "auto";
    css.zIndex = 2;
    css.boxSizing = "border-box";
    css.margin = 0;
    // Moldura `card` recebe overflow via CSS do host; conteúdo framed clipa no card.
    if (options?.partKind !== "card") {
      css.overflow = "hidden";
    }
  } else if (kpiPartHasBoxPaint(style) && options?.partKind !== "card") {
    // Evita que fill do valor (flex:1) pinte o card inteiro.
    css.flex = "0 0 auto";
    css.alignSelf = "flex-start";
    css.width = "fit-content";
    css.maxWidth = "100%";
    css.boxSizing = "border-box";
  } else if (
    options?.iconSizeFallback &&
    style?.iconSize != null &&
    Number.isFinite(style.iconSize) &&
    style.iconSize > 0
  ) {
    const size = Math.max(16, Math.min(160, Math.round(style.iconSize)));
    css.width = `${size}px`;
    css.height = `${size}px`;
  }

  return css;
}

/** @deprecated Preferir `resolveKpiPartFrame`. */
export function resolveKpiIconFrame(
  state: KpiPartState | null | undefined,
): KpiPartFrame | null {
  return resolveKpiPartFrame(state);
}

/** Rótulos de chrome de caixa — distinguem fundo do card vs caixa da parte textual. */
export function kpiPartBoxChromeLabels(kind: KpiPartRef["kind"]): {
  fill: string;
  stroke: string;
  fillShort: string;
  strokeShort: string;
} {
  if (kind === "card") {
    return {
      fill: "Fundo do card",
      stroke: "Contorno do card",
      fillShort: "Fundo",
      strokeShort: "Contorno",
    };
  }
  if (kind === "icon") {
    return {
      fill: "Fundo do ícone",
      stroke: "Contorno do ícone",
      fillShort: "Fundo",
      strokeShort: "Contorno",
    };
  }
  return {
    fill: "Fundo da caixa",
    stroke: "Borda da caixa",
    fillShort: "Fundo caixa",
    strokeShort: "Borda caixa",
  };
}

/** Tipografia (fonte / efeitos de texto / parágrafo) — title, value, hint. */
export function kpiPartSupportsTypography(ref: KpiPartRef | null | undefined): boolean {
  return Boolean(ref && (ref.kind === "title" || ref.kind === "value" || ref.kind === "hint"));
}

/** Estilo do box do ícone a partir de `kpiParts.icon` (cores, raio, frame/% ou size px). */
export function resolveKpiIconBoxStyle(
  state: KpiPartState | null | undefined,
  contrastBackground?: string | null,
): CSSProperties {
  const css = resolveKpiPartLayoutStyle(state, { iconSizeFallback: true });
  const rawColor = state?.style?.color?.trim();
  if (!rawColor) {
    return css;
  }

  const iconFill = state?.style?.fill;
  const contrastBg =
    iconFill && iconFill !== "transparent" && iconFill !== "none"
      ? iconFill
      : (contrastBackground ?? DECK_KPI_DEFAULTS.backgroundColor);

  /* Cor do glyph — escolha do usuário (ou Automático vs fundo); nunca sentinel `auto` no CSS. */
  const fg = isAutomaticTextColor(rawColor)
    ? resolvePaintTextColor(AUTOMATIC_TEXT_COLOR, contrastBg)
    : rawColor;
  if (fg) {
    css.color = fg;
    (css as Record<string, string>)["--delpi-kpi-icon-fg"] = fg;
  }
  return css;
}

export function serializeKpiPartRef(ref: KpiPartRef): string {
  if (ref.kind === "metricCard") return `metricCard:${ref.field}`;
  return ref.kind;
}

export function parseKpiPartRef(raw: string | null | undefined): KpiPartRef | null {
  const value = (raw ?? "").trim();
  if (value === "card" || value === "title" || value === "value" || value === "hint" || value === "icon") {
    return { kind: value };
  }
  if (value.startsWith("metricCard:")) {
    const field = value.slice("metricCard:".length).trim();
    return field ? { kind: "metricCard", field } : null;
  }
  return null;
}

export function isKpiPartRefEqual(a?: KpiPartRef | null, b?: KpiPartRef | null): boolean {
  if (!a || !b) return false;
  if (a.kind !== b.kind) return false;
  if (a.kind === "metricCard" && b.kind === "metricCard") {
    return a.field === b.field;
  }
  return true;
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

export function kpiPartAllowsMove(ref: KpiPartRef): boolean {
  return kpiPartCapabilities(ref).movable;
}

export function kpiPartAllowsResize(ref: KpiPartRef): boolean {
  return kpiPartCapabilities(ref).resizable;
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

/**
 * Aplica frames default a todas as partes visíveis ainda sem frame.
 * Nunca uma parte isolada — evita híbrido flex+absolute que quebra o stack.
 */
export function seedKpiPartsFreeLayoutFrames(
  parts: KpiPartsMap | null | undefined,
): KpiPartsMap {
  let next = parts ?? {};
  for (const kind of KPI_FREE_LAYOUT_PART_KINDS) {
    const ref: KpiPartRef = { kind };
    const state = getKpiPartState(next, ref);
    if (!state || state.visible === false) continue;
    if (resolveKpiPartFrame(state)) continue;
    next = upsertKpiPartState(next, ref, { frame: defaultKpiPartFrame(kind) });
  }
  return next;
}

/** Remove frames das partes de conteúdo — volta ao fluxo flex do card. */
export function clearKpiPartsFreeLayoutFrames(
  parts: KpiPartsMap | null | undefined,
): KpiPartsMap {
  let next = parts ?? {};
  for (const kind of KPI_FREE_LAYOUT_PART_KINDS) {
    next = upsertKpiPartState(next, { kind }, { frame: null });
  }
  return next;
}

/**
 * Materializa frames % a partir do DOM atual (layout flex) para todas as partes
 * ainda sem frame. Usar no 1º move/resize — nunca só na parte clicada.
 */
export function materializeMissingKpiPartFramesFromRoot(
  root: HTMLElement,
  parts: KpiPartsMap | null | undefined,
): KpiPartsMap {
  let next = parts ?? {};
  const card =
    root.classList.contains("delpi-kpi-card")
      ? root
      : (root.querySelector(".delpi-kpi-card") ?? root.closest(".delpi-kpi-card"));
  if (!(card instanceof HTMLElement)) return next;

  for (const host of card.querySelectorAll(`[${KPI_PART_DATA_ATTR}]`)) {
    if (!(host instanceof HTMLElement)) continue;
    const ref = parseKpiPartRef(host.getAttribute(KPI_PART_DATA_ATTR));
    if (!ref || ref.kind === "card") continue;
    if (resolveKpiPartFrame(getKpiPartState(next, ref))) continue;
    const frameRoot = resolveKpiPartFrameRoot(host, ref);
    if (!frameRoot) continue;
    const rect = frameRoot.getBoundingClientRect();
    const el = host.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) continue;
    next = upsertKpiPartState(next, ref, {
      frame: clampKpiPartFrame({
        x: ((el.left - rect.left) / rect.width) * 100,
        y: ((el.top - rect.top) / rect.height) * 100,
        w: Math.max(8, (el.width / rect.width) * 100),
        h: Math.max(4, (el.height / rect.height) * 100),
      }),
    });
  }
  return next;
}

/** Partes tipográficas irmãs (Excel: Apply to All em texto do KPI). */
export const KPI_TEXT_PART_KINDS = ["title", "value", "hint"] as const;

export function isKpiTextPartKind(kind: KpiPartRef["kind"]): kind is KpiTextPartKind {
  return (KPI_TEXT_PART_KINDS as readonly string[]).includes(kind);
}

/**
 * Replica o estilo da parte tipográfica selecionada em title/value/hint.
 * Card/ícone não têm irmãos tipográficos — retorna o mapa inalterado.
 */
export function applyKpiPartStyleToSiblingParts(
  parts: KpiPartsMap | null | undefined,
  from: KpiPartRef,
  style: KpiPartStyle,
): KpiPartsMap {
  if (!isKpiTextPartKind(from.kind)) {
    return parts ?? {};
  }
  let next = parts ?? {};
  for (const kind of KPI_TEXT_PART_KINDS) {
    next = upsertKpiPartState(next, { kind }, { style });
  }
  return next;
}

export function kpiPartDomProps(ref: KpiPartRef, selectedPart?: KpiPartRef | null) {
  const selected = isKpiPartRefEqual(ref, selectedPart);
  return {
    [KPI_PART_DATA_ATTR]: serializeKpiPartRef(ref),
    "aria-selected": selected ? true : undefined,
  };
}

/** Tipografia + alinhamento de parte textual do KPI (title/value/hint).
 * Alinhamento usa caixa flex em coluna (mesmo contrato das caixas de texto do deck).
 * `flexPart` é legado — valor default vertical = middle; título/hint = top.
 */
export function resolveKpiPartTypographyStyle(
  style: KpiPartStyle | null | undefined,
  options?: { flexPart?: boolean; fillHost?: boolean },
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
  applyTextEffectStyleToCss(style, css);

  const applyBox =
    Boolean(style.textAlign) ||
    Boolean(style.verticalAlign) ||
    options?.flexPart === true;
  if (applyBox) {
    Object.assign(
      css,
      resolveTextPartColumnBoxLayout({
        textAlign: style.textAlign,
        verticalAlign: style.verticalAlign,
        defaultVerticalAlign: options?.flexPart ? "middle" : "top",
        fillHost: options?.fillHost !== false,
      }),
    );
  }

  return Object.keys(css).length > 0 ? css : undefined;
}

export function bindKpiPartPointer(ref: KpiPartRef, interaction?: KpiCardInteraction | null) {
  const interactive = Boolean(interaction?.onPartPointerDown || interaction?.onPartDoubleClick);
  const selected = isKpiPartRefEqual(ref, interaction?.selectedPart);
  const editing = isKpiPartRefEqual(ref, interaction?.editingPart);
  const dom = kpiPartDomProps(ref, interaction?.selectedPart);
  const moveWhenSelected = kpiPartAllowsMove(ref);

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
      if (editing) {
        event.stopPropagation();
        return;
      }
      event.stopPropagation();
      interaction?.onPartPointerDown?.(ref, event);
      if (moveWhenSelected && selected) {
        interaction?.onPartMovePointerDown?.(ref, event);
      }
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
        fill: options?.backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor,
        borderRadius: DECK_KPI_DEFAULTS.borderRadius,
        stroke: DECK_KPI_DEFAULTS.borderColor,
        strokeWidth: DECK_KPI_DEFAULTS.borderWidth,
        boxShadow: DECK_KPI_DEFAULTS.boxShadow,
      },
    },
    title: {
      visible: options?.showTitle !== false,
      content: options?.title,
      style: {
        fontSize: KPI_PART_FONT_SIZE_DEFAULTS.title,
        fontWeight: 600,
        color: AUTOMATIC_TEXT_COLOR,
      },
    },
    value: {
      visible: true,
      style: {
        color: options?.valueColor ?? AUTOMATIC_TEXT_COLOR,
        fontSize: KPI_PART_FONT_SIZE_DEFAULTS.value,
        fontWeight: 700,
      },
    },
    hint: {
      visible: Boolean(options?.subtitle?.trim()),
      content: options?.subtitle,
      style: {
        fontSize: KPI_PART_FONT_SIZE_DEFAULTS.hint,
        fontWeight: 500,
        color: AUTOMATIC_TEXT_COLOR,
      },
    },
    icon: {
      visible: options?.showIcon !== false,
      style: {
        borderRadius: KPI_ICON_DEFAULT_RADIUS_PX,
        iconSize: KPI_ICON_DEFAULT_SIZE_PX,
      },
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
