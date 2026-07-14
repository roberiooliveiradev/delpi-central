/**
 * Partes endereçáveis do bloco filtro (input) — espelho enxuto de kpiCardParts.
 */

import type {
  CSSProperties,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
} from "react";

import { AUTOMATIC_TEXT_COLOR, isAutomaticTextColor, resolvePaintTextColor } from "../shape/colorUtils";

export const INPUT_PART_DATA_ATTR = "data-input-part";

export type InputPartRef =
  | { kind: "frame" }
  | { kind: "icon" }
  | { kind: "label" }
  | { kind: "badge" }
  | { kind: "control" };

export type InputPartStyle = {
  fill?: string;
  color?: string;
  fontFamily?: string;
  fontSize?: number;
  fontWeight?: string | number;
  fontStyle?: string;
  textDecoration?: string;
  textAlign?: "left" | "center" | "right" | "justify";
  opacity?: number;
  stroke?: string;
  strokeWidth?: number;
  borderRadius?: number;
  boxShadow?: string;
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  iconSize?: number;
};

export type InputPartFrame = {
  x: number;
  y: number;
  w?: number;
  h?: number;
};

export type InputPartState = {
  visible?: boolean;
  style?: InputPartStyle;
  frame?: InputPartFrame;
};

export type InputPartsMap = Record<string, InputPartState>;

export type InputPartResizeHandle = "nw" | "n" | "ne" | "e" | "se" | "s" | "sw" | "w";

export const INPUT_PART_RESIZE_HANDLES: InputPartResizeHandle[] = [
  "nw",
  "n",
  "ne",
  "e",
  "se",
  "s",
  "sw",
  "w",
];

export type InputPartCapabilities = {
  movable: boolean;
  editable: boolean;
  deletable: boolean;
  resizable: boolean;
};

const INPUT_PART_KIND_CAPABILITIES: Record<InputPartRef["kind"], InputPartCapabilities> = {
  frame: { movable: false, editable: false, deletable: false, resizable: false },
  icon: { movable: true, editable: false, deletable: true, resizable: true },
  label: { movable: true, editable: false, deletable: true, resizable: true },
  badge: { movable: true, editable: false, deletable: true, resizable: true },
  control: { movable: true, editable: false, deletable: false, resizable: true },
};

export const INPUT_PART_DEFAULT_FRAMES: Record<InputPartRef["kind"], InputPartFrame> = {
  frame: { x: 0, y: 0, w: 100, h: 100 },
  icon: { x: 2, y: 18, w: 12, h: 64 },
  label: { x: 16, y: 8, w: 52, h: 36 },
  badge: { x: 70, y: 8, w: 28, h: 28 },
  control: { x: 16, y: 48, w: 80, h: 44 },
};

export const INPUT_PART_FONT_SIZE_DEFAULTS = {
  label: 14,
  badge: 11,
  control: 14,
} as const;

export type InputTextPartKind = keyof typeof INPUT_PART_FONT_SIZE_DEFAULTS;

export const INPUT_TEXT_PART_KINDS = ["label", "badge", "control"] as const;

export const INPUT_ICON_DEFAULT_SIZE_PX = 20;

export type InputFilterInteraction = {
  selectedPart?: InputPartRef | null;
  onPartPointerDown?: (ref: InputPartRef, event: ReactPointerEvent) => void;
  onPartDoubleClick?: (ref: InputPartRef, event: ReactPointerEvent | ReactMouseEvent) => void;
  onPartMovePointerDown?: (ref: InputPartRef, event: ReactPointerEvent) => void;
  onPartResizePointerDown?: (
    ref: InputPartRef,
    event: ReactPointerEvent,
    handle: InputPartResizeHandle,
  ) => void;
};

export function isInputTextPartKind(kind: InputPartRef["kind"]): kind is InputTextPartKind {
  return (INPUT_TEXT_PART_KINDS as readonly string[]).includes(kind);
}

export function resolveInputPartFontSize(
  kind: InputTextPartKind,
  style?: InputPartStyle | null,
): number {
  const explicit = style?.fontSize;
  if (explicit != null && Number.isFinite(explicit) && explicit > 0) {
    return Math.round(explicit);
  }
  return INPUT_PART_FONT_SIZE_DEFAULTS[kind];
}

export function serializeInputPartRef(ref: InputPartRef): string {
  return ref.kind;
}

export function parseInputPartRef(raw: string | null | undefined): InputPartRef | null {
  const value = (raw ?? "").trim();
  if (
    value === "frame" ||
    value === "icon" ||
    value === "label" ||
    value === "badge" ||
    value === "control"
  ) {
    return { kind: value };
  }
  return null;
}

export function isInputPartRefEqual(a?: InputPartRef | null, b?: InputPartRef | null): boolean {
  if (!a || !b) return false;
  return a.kind === b.kind;
}

export function inputPartCapabilities(ref: InputPartRef): InputPartCapabilities {
  return INPUT_PART_KIND_CAPABILITIES[ref.kind];
}

export function inputPartAllowsDelete(ref: InputPartRef): boolean {
  return inputPartCapabilities(ref).deletable;
}

export function inputPartAllowsMove(ref: InputPartRef): boolean {
  return inputPartCapabilities(ref).movable;
}

export function inputPartAllowsResize(ref: InputPartRef): boolean {
  return inputPartCapabilities(ref).resizable;
}

export function inputPartAllowsFrame(ref: InputPartRef): boolean {
  return (
    ref.kind === "icon" ||
    ref.kind === "label" ||
    ref.kind === "badge" ||
    ref.kind === "control"
  );
}

export function inputPartSupportsTypography(ref: InputPartRef | null | undefined): boolean {
  return Boolean(ref && isInputTextPartKind(ref.kind));
}

export function getInputPartState(
  parts: InputPartsMap | null | undefined,
  ref: InputPartRef,
): InputPartState | undefined {
  return parts?.[serializeInputPartRef(ref)];
}

export function isInputPartVisible(
  parts: InputPartsMap | null | undefined,
  ref: InputPartRef,
): boolean {
  const state = getInputPartState(parts, ref);
  if (state?.visible === false) return false;
  return true;
}

export function clampInputPartFrame(frame: InputPartFrame): InputPartFrame {
  const w = Math.max(4, Math.min(100, frame.w ?? 20));
  const h = Math.max(4, Math.min(100, frame.h ?? 20));
  return {
    x: Math.max(0, Math.min(100 - w, frame.x)),
    y: Math.max(0, Math.min(100 - h, frame.y)),
    w,
    h,
  };
}

export function defaultInputPartFrame(kind: InputPartRef["kind"]): InputPartFrame {
  return { ...INPUT_PART_DEFAULT_FRAMES[kind] };
}

export function resolveInputPartFrame(
  state: InputPartState | null | undefined,
): InputPartFrame | null {
  if (!state?.frame) return null;
  return clampInputPartFrame(state.frame);
}

export type InputPartStatePatch = Omit<InputPartState, "frame" | "style"> & {
  style?: Partial<InputPartStyle>;
  frame?: InputPartFrame | null;
};

export function upsertInputPartState(
  parts: InputPartsMap | null | undefined,
  ref: InputPartRef,
  patch: InputPartStatePatch,
): InputPartsMap {
  const key = serializeInputPartRef(ref);
  const prev = parts?.[key] ?? {};
  const nextFrame =
    patch.frame === null
      ? undefined
      : patch.frame !== undefined
        ? clampInputPartFrame({ ...(prev.frame ?? {}), ...patch.frame })
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

export function mergeInputParts(
  parts: InputPartsMap | null | undefined,
): InputPartsMap {
  return { ...(parts ?? {}) };
}

export function normalizeInputPartsForLoad(
  parts: unknown,
): InputPartsMap | undefined {
  if (!parts || typeof parts !== "object") return undefined;
  let next: InputPartsMap = {};
  for (const [key, raw] of Object.entries(parts as Record<string, unknown>)) {
    const ref = parseInputPartRef(key);
    if (!ref || !raw || typeof raw !== "object") continue;
    const state = raw as Record<string, unknown>;
    const style =
      state.style && typeof state.style === "object"
        ? ({ ...(state.style as InputPartStyle) } as InputPartStyle)
        : undefined;
    const frameRaw = state.frame;
    const frame =
      frameRaw && typeof frameRaw === "object"
        ? clampInputPartFrame(frameRaw as InputPartFrame)
        : undefined;
    next = {
      ...next,
      [key]: {
        ...(typeof state.visible === "boolean" ? { visible: state.visible } : {}),
        ...(style ? { style } : {}),
        ...(frame ? { frame } : {}),
      },
    };
  }
  return Object.keys(next).length > 0 ? next : undefined;
}

export function resizeInputPartFrame(
  frame: InputPartFrame,
  handle: InputPartResizeHandle,
  dx: number,
  dy: number,
): InputPartFrame {
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
  return clampInputPartFrame({ x, y, w, h });
}

export function resolveInputPartFrameRoot(fromEl: HTMLElement | null): HTMLElement | null {
  if (!fromEl) return null;
  return fromEl.closest(".tdp-comunicado__input-block");
}

export function findInputPartFromTarget(target: EventTarget | null): InputPartRef | null {
  if (!(target instanceof Element)) return null;
  const host = target.closest(`[${INPUT_PART_DATA_ATTR}]`);
  if (!(host instanceof HTMLElement)) return null;
  return parseInputPartRef(host.getAttribute(INPUT_PART_DATA_ATTR));
}

export function bindInputPartPointer(
  ref: InputPartRef,
  interaction?: InputFilterInteraction | null,
): {
  onPointerDown?: (event: ReactPointerEvent) => void;
  onDoubleClick?: (event: ReactMouseEvent) => void;
} {
  if (!interaction) return {};
  return {
    onPointerDown: (event) => {
      const selected =
        interaction.selectedPart && isInputPartRefEqual(interaction.selectedPart, ref);
      if (selected && inputPartAllowsMove(ref) && interaction.onPartMovePointerDown) {
        interaction.onPartMovePointerDown(ref, event);
        return;
      }
      interaction.onPartPointerDown?.(ref, event);
    },
    onDoubleClick: (event) => {
      event.stopPropagation();
      interaction.onPartDoubleClick?.(ref, event);
    },
  };
}

function inputPartHasBoxPaint(style?: InputPartStyle | null): boolean {
  if (!style) return false;
  const fill = style.fill?.trim();
  const hasFill = Boolean(fill && fill !== "transparent" && fill !== "none");
  const stroke = style.stroke?.trim();
  const strokeWidth = style.strokeWidth ?? 0;
  const hasStroke = Boolean(
    stroke && stroke !== "transparent" && stroke !== "none" && strokeWidth > 0,
  );
  return hasFill || hasStroke;
}

export function resolveInputPartLayoutStyle(
  state: InputPartState | null | undefined,
  options?: { iconSizeFallback?: boolean; partKind?: InputPartRef["kind"] },
): CSSProperties {
  const style = state?.style;
  const frame = resolveInputPartFrame(state);
  const css: CSSProperties = {};

  if (style?.fill != null && style.fill !== "") css.background = style.fill;
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
  if (style?.fontFamily) css.fontFamily = style.fontFamily;
  if (style?.fontSize != null && style.fontSize > 0) css.fontSize = `${style.fontSize}px`;
  if (style?.fontWeight != null) css.fontWeight = style.fontWeight;
  if (style?.fontStyle) css.fontStyle = style.fontStyle;
  if (style?.textDecoration) css.textDecoration = style.textDecoration;
  if (style?.textAlign) css.textAlign = style.textAlign;
  if (style?.textShadow) css.textShadow = style.textShadow;

  if (frame) {
    css.position = "absolute";
    css.left = `${frame.x}%`;
    css.top = `${frame.y}%`;
    css.width = `${frame.w}%`;
    css.height = `${frame.h}%`;
    css.alignSelf = "auto";
    css.zIndex = 2;
    css.boxSizing = "border-box";
    css.margin = 0;
  } else if (inputPartHasBoxPaint(style) && options?.partKind !== "frame") {
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
    const size = Math.max(12, Math.min(160, Math.round(style.iconSize)));
    css.width = `${size}px`;
    css.height = `${size}px`;
  }

  return css;
}

export function resolveInputIconBoxStyle(
  state: InputPartState | null | undefined,
  contrastBackground?: string | null,
): CSSProperties {
  const css = resolveInputPartLayoutStyle(state, { iconSizeFallback: true, partKind: "icon" });
  const rawColor = state?.style?.color?.trim();
  if (!rawColor) return css;
  const iconFill = state?.style?.fill;
  const contrastBg =
    iconFill && iconFill !== "transparent" && iconFill !== "none"
      ? iconFill
      : (contrastBackground ?? "transparent");
  const fg = isAutomaticTextColor(rawColor)
    ? resolvePaintTextColor(AUTOMATIC_TEXT_COLOR, contrastBg)
    : rawColor;
  if (fg) css.color = fg;
  return css;
}

export function materializeMissingInputPartFramesFromRoot(
  root: HTMLElement,
  parts: InputPartsMap | null | undefined,
): InputPartsMap {
  let next = parts ?? {};
  const host =
    root.classList.contains("tdp-comunicado__input-block")
      ? root
      : (root.closest(".tdp-comunicado__input-block") as HTMLElement | null);
  if (!host) return next;

  for (const el of host.querySelectorAll(`[${INPUT_PART_DATA_ATTR}]`)) {
    if (!(el instanceof HTMLElement)) continue;
    const ref = parseInputPartRef(el.getAttribute(INPUT_PART_DATA_ATTR));
    if (!ref || ref.kind === "frame") continue;
    if (resolveInputPartFrame(getInputPartState(next, ref))) continue;
    const rect = host.getBoundingClientRect();
    const box = el.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) continue;
    next = upsertInputPartState(next, ref, {
      frame: clampInputPartFrame({
        x: ((box.left - rect.left) / rect.width) * 100,
        y: ((box.top - rect.top) / rect.height) * 100,
        w: Math.max(8, (box.width / rect.width) * 100),
        h: Math.max(4, (box.height / rect.height) * 100),
      }),
    });
  }
  return next;
}

export function inputPartBoxChromeLabels(kind: InputPartRef["kind"]): {
  fill: string;
  stroke: string;
  fillShort: string;
  strokeShort: string;
} {
  if (kind === "frame") {
    return {
      fill: "Fundo do filtro",
      stroke: "Contorno do filtro",
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

/** Resolve parte de chrome Preench./Contorno — frame ou null (global). */
export function resolveInputShapeChromePartRef(
  selectedPart: InputPartRef | null | undefined,
): InputPartRef | null {
  if (!selectedPart) return null;
  if (selectedPart.kind === "frame") return selectedPart;
  return selectedPart;
}
