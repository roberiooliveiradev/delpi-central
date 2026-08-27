import { colorToCss, cssToColorValue, clampAlpha } from "./colorUtils";
import {
  DEFAULT_AMBIENT_SHADOW_LAYER,
  DEFAULT_BOX_SHADOW_MODEL,
  parseBoxShadowStack,
  type BoxShadowModel,
} from "./boxShadowModel";

/** Uma camada de `text-shadow` (sem inset/spread — limitação CSS). */
export type TextShadowModel = {
  offsetX: number;
  offsetY: number;
  blur: number;
  /** Hex `#rrggbb`. */
  colorHex: string;
  /** Opacidade 0–1. */
  opacity: number;
};

/** Pilha de camadas (CSS separado por vírgula). */
export type TextShadowStack = {
  layers: TextShadowModel[];
};

export const MAX_TEXT_SHADOW_LAYERS = 2;

export const DEFAULT_TEXT_SHADOW_MODEL: TextShadowModel = {
  offsetX: DEFAULT_BOX_SHADOW_MODEL.offsetX,
  offsetY: DEFAULT_BOX_SHADOW_MODEL.offsetY,
  blur: DEFAULT_BOX_SHADOW_MODEL.blur,
  colorHex: DEFAULT_BOX_SHADOW_MODEL.colorHex,
  opacity: DEFAULT_BOX_SHADOW_MODEL.opacity,
};

export const DEFAULT_AMBIENT_TEXT_SHADOW_LAYER: TextShadowModel = {
  offsetX: DEFAULT_AMBIENT_SHADOW_LAYER.offsetX,
  offsetY: DEFAULT_AMBIENT_SHADOW_LAYER.offsetY,
  blur: DEFAULT_AMBIENT_SHADOW_LAYER.blur,
  colorHex: DEFAULT_AMBIENT_SHADOW_LAYER.colorHex,
  opacity: DEFAULT_AMBIENT_SHADOW_LAYER.opacity,
};

const LENGTH_RE = /(-?\d+(?:\.\d+)?)(px|pt|em|rem|%)?/i;

function parseLengthPx(token: string): number | null {
  const match = token.trim().match(LENGTH_RE);
  if (!match) return null;
  const value = Number(match[1]);
  if (!Number.isFinite(value)) return null;
  const unit = (match[2] ?? "px").toLowerCase();
  if (unit === "px" || unit === "") return value;
  if (unit === "pt") return value * (96 / 72);
  return value;
}

function formatLengthPx(value: number): string {
  const rounded = Math.round(value * 100) / 100;
  if (rounded === 0) return "0";
  return `${rounded}px`;
}

function clampShadowNumber(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, value));
}

export function clampTextShadowModel(model: TextShadowModel): TextShadowModel {
  return {
    offsetX: clampShadowNumber(model.offsetX, -80, 80),
    offsetY: clampShadowNumber(model.offsetY, -80, 80),
    blur: clampShadowNumber(model.blur, 0, 120),
    colorHex: model.colorHex,
    opacity: clampAlpha(model.opacity),
  };
}

function layersEqual(a: TextShadowModel, b: TextShadowModel): boolean {
  return (
    a.offsetX === b.offsetX &&
    a.offsetY === b.offsetY &&
    a.blur === b.blur &&
    a.colorHex === b.colorHex &&
    Math.abs(a.opacity - b.opacity) < 0.001
  );
}

/** Compara duas strings text-shadow pela geometria/cor (ignora formatação). */
export function textShadowsEqual(a?: string | null, b?: string | null): boolean {
  const left = (a ?? "").trim();
  const right = (b ?? "").trim();
  if (left === right) return true;
  const stackA = parseTextShadowStack(left);
  const stackB = parseTextShadowStack(right);
  if (!stackA || !stackB) return false;
  if (stackA.layers.length !== stackB.layers.length) return false;
  return stackA.layers.every((layer, index) => layersEqual(layer, stackB.layers[index]!));
}

/** Serializa uma camada para CSS `text-shadow`. */
export function formatTextShadow(model: TextShadowModel): string {
  const next = clampTextShadowModel(model);
  const color = colorToCss({ hex: next.colorHex, alpha: next.opacity });
  return [
    formatLengthPx(next.offsetX),
    formatLengthPx(next.offsetY),
    formatLengthPx(next.blur),
    color,
  ].join(" ");
}

/** Serializa a pilha completa. */
export function formatTextShadowStack(stack: TextShadowStack): string {
  return stack.layers.map((layer) => formatTextShadow(layer)).join(", ");
}

function splitShadowLayers(css: string): string[] {
  const layers: string[] = [];
  let depth = 0;
  let start = 0;
  for (let i = 0; i < css.length; i += 1) {
    const ch = css[i];
    if (ch === "(") depth += 1;
    else if (ch === ")") depth = Math.max(0, depth - 1);
    else if (ch === "," && depth === 0) {
      layers.push(css.slice(start, i).trim());
      start = i + 1;
    }
  }
  const tail = css.slice(start).trim();
  if (tail) layers.push(tail);
  return layers;
}

function parseSingleLayer(layerCss: string): TextShadowModel | null {
  let rest = layerCss.trim();
  if (!rest) return null;

  let colorCss = "#000000";
  const rgbaMatch = rest.match(
    /(rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+(?:\s*,\s*[\d.]+)?\s*\))\s*$/i,
  );
  const hexMatch = !rgbaMatch ? rest.match(/(#[0-9a-f]{3,8})\s*$/i) : null;
  if (rgbaMatch) {
    colorCss = rgbaMatch[1];
    rest = rest.slice(0, rgbaMatch.index).trim();
  } else if (hexMatch) {
    colorCss = hexMatch[1];
    rest = rest.slice(0, hexMatch.index).trim();
  }

  const color = cssToColorValue(colorCss, "#000000");
  const tokens = rest.split(/\s+/).filter(Boolean);
  if (tokens.length < 2) return null;

  const offsetX = parseLengthPx(tokens[0]);
  const offsetY = parseLengthPx(tokens[1]);
  if (offsetX == null || offsetY == null) return null;

  const blur = tokens[2] != null ? parseLengthPx(tokens[2]) : 0;
  if (blur == null) return null;

  return clampTextShadowModel({
    offsetX,
    offsetY,
    blur,
    colorHex: color.hex,
    opacity: color.alpha > 0 ? color.alpha : DEFAULT_TEXT_SHADOW_MODEL.opacity,
  });
}

export function parseTextShadow(css?: string | null): TextShadowModel | null {
  const stack = parseTextShadowStack(css);
  return stack?.layers[0] ?? null;
}

export function parseTextShadowStack(css?: string | null): TextShadowStack | null {
  const raw = (css ?? "").trim();
  if (!raw || raw.toLowerCase() === "none") return null;

  const parts = splitShadowLayers(raw);
  if (parts.length === 0) return null;

  const layers: TextShadowModel[] = [];
  for (const part of parts) {
    const layer = parseSingleLayer(part);
    if (!layer) return null;
    layers.push(layer);
  }
  return { layers };
}

export function resolveTextShadowStack(css?: string | null): TextShadowStack {
  return parseTextShadowStack(css) ?? { layers: [{ ...DEFAULT_TEXT_SHADOW_MODEL }] };
}

export function resolveTextShadowModel(css?: string | null): TextShadowModel {
  return resolveTextShadowStack(css).layers[0] ?? { ...DEFAULT_TEXT_SHADOW_MODEL };
}

export function patchTextShadow(
  css: string | undefined,
  patch: Partial<TextShadowModel>,
  layerIndex = 0,
): string {
  const stack = resolveTextShadowStack(css);
  const index = Math.max(0, Math.min(MAX_TEXT_SHADOW_LAYERS - 1, layerIndex));
  while (stack.layers.length <= index) {
    stack.layers.push({ ...DEFAULT_AMBIENT_TEXT_SHADOW_LAYER });
  }
  const current = stack.layers[index] ?? { ...DEFAULT_TEXT_SHADOW_MODEL };
  stack.layers[index] = clampTextShadowModel({ ...current, ...patch });
  return formatTextShadowStack(stack);
}

export function addTextShadowLayer(css: string | undefined): string {
  const stack = resolveTextShadowStack(css);
  if (stack.layers.length >= MAX_TEXT_SHADOW_LAYERS) {
    return formatTextShadowStack(stack);
  }
  stack.layers.push({ ...DEFAULT_AMBIENT_TEXT_SHADOW_LAYER });
  return formatTextShadowStack(stack);
}

export function removeTextShadowLayer(css: string | undefined, layerIndex: number): string {
  const stack = resolveTextShadowStack(css);
  if (stack.layers.length <= 1) {
    return formatTextShadowStack(stack);
  }
  const index = Math.max(0, Math.min(stack.layers.length - 1, layerIndex));
  stack.layers.splice(index, 1);
  return formatTextShadowStack(stack);
}

function boxLayerToTextLayer(box: BoxShadowModel): TextShadowModel {
  return clampTextShadowModel({
    offsetX: box.offsetX,
    offsetY: box.offsetY,
    blur: box.blur,
    colorHex: box.colorHex,
    opacity: box.opacity,
  });
}

/**
 * Converte `box-shadow` CSS em `text-shadow` (omite inset; ignora spread na serialização).
 */
export function boxShadowCssToTextShadowCss(css?: string | null): string | undefined {
  const stack = parseBoxShadowStack(css);
  if (!stack?.layers.length) return undefined;
  const textLayers = stack.layers.filter((layer) => !layer.inset).map(boxLayerToTextLayer);
  if (textLayers.length === 0) return undefined;
  return formatTextShadowStack({ layers: textLayers });
}

export type TextShadowPreset = {
  id: string;
  label: string;
  /** CSS text-shadow; omitido = sem sombra. */
  value?: string;
};

/** Presets texto derivados de presets box (sem Interna). */
export function buildTextShadowPresetsFromBox(
  boxPresets: ReadonlyArray<{ key: string; label: string; value?: string }>,
): readonly TextShadowPreset[] {
  return boxPresets
    .filter((preset) => preset.key !== "inset")
    .map((preset) => ({
      id: preset.key,
      label: preset.label,
      value: preset.value ? boxShadowCssToTextShadowCss(preset.value) : undefined,
    }));
}
