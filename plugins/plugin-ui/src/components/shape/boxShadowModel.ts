import { colorToCss, cssToColorValue, clampAlpha } from "./colorUtils";

/** Uma camada de `box-shadow` (drop ou inset). */
export type BoxShadowModel = {
  inset: boolean;
  offsetX: number;
  offsetY: number;
  blur: number;
  spread: number;
  /** Hex `#rrggbb`. */
  colorHex: string;
  /** Opacidade 0–1. */
  opacity: number;
};

/** Pilha de camadas (CSS separado por vírgula). UI edita até {@link MAX_BOX_SHADOW_LAYERS}. */
export type BoxShadowStack = {
  layers: BoxShadowModel[];
};

/** Máximo de camadas editáveis na ribbon (contato + ambiente). */
export const MAX_BOX_SHADOW_LAYERS = 2;

export const DEFAULT_BOX_SHADOW_MODEL: BoxShadowModel = {
  inset: false,
  offsetX: 0,
  offsetY: 4,
  blur: 14,
  spread: 0,
  colorHex: "#000000",
  opacity: 0.28,
};

/** Segunda camada típica (ambiente / difusa). */
export const DEFAULT_AMBIENT_SHADOW_LAYER: BoxShadowModel = {
  inset: false,
  offsetX: 0,
  offsetY: 12,
  blur: 28,
  spread: -4,
  colorHex: "#000000",
  opacity: 0.12,
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

export function clampBoxShadowModel(model: BoxShadowModel): BoxShadowModel {
  return {
    inset: Boolean(model.inset),
    offsetX: clampShadowNumber(model.offsetX, -80, 80),
    offsetY: clampShadowNumber(model.offsetY, -80, 80),
    blur: clampShadowNumber(model.blur, 0, 120),
    spread: clampShadowNumber(model.spread, -40, 60),
    colorHex: model.colorHex,
    opacity: clampAlpha(model.opacity),
  };
}

function layersEqual(a: BoxShadowModel, b: BoxShadowModel): boolean {
  return (
    a.inset === b.inset &&
    a.offsetX === b.offsetX &&
    a.offsetY === b.offsetY &&
    a.blur === b.blur &&
    a.spread === b.spread &&
    a.colorHex === b.colorHex &&
    Math.abs(a.opacity - b.opacity) < 0.001
  );
}

/** Compara duas strings box-shadow pela geometria/cor (ignora formatação). */
export function boxShadowsEqual(a?: string | null, b?: string | null): boolean {
  const left = (a ?? "").trim();
  const right = (b ?? "").trim();
  if (left === right) return true;
  const stackA = parseBoxShadowStack(left);
  const stackB = parseBoxShadowStack(right);
  if (!stackA || !stackB) return false;
  if (stackA.layers.length !== stackB.layers.length) return false;
  return stackA.layers.every((layer, index) => layersEqual(layer, stackB.layers[index]!));
}

/** Serializa uma camada para CSS. */
export function formatBoxShadow(model: BoxShadowModel): string {
  const next = clampBoxShadowModel(model);
  const color = colorToCss({ hex: next.colorHex, alpha: next.opacity });
  const parts: string[] = [];
  if (next.inset) parts.push("inset");
  parts.push(
    formatLengthPx(next.offsetX),
    formatLengthPx(next.offsetY),
    formatLengthPx(next.blur),
  );
  if (next.spread !== 0) {
    parts.push(formatLengthPx(next.spread));
  }
  parts.push(color);
  return parts.join(" ");
}

/** Serializa a pilha completa. */
export function formatBoxShadowStack(stack: BoxShadowStack): string {
  return stack.layers.map((layer) => formatBoxShadow(layer)).join(", ");
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

function parseSingleLayer(layerCss: string): BoxShadowModel | null {
  let rest = layerCss.trim();
  if (!rest) return null;

  const inset = /^inset\b/i.test(rest);
  if (inset) {
    rest = rest.replace(/^inset\s+/i, "").trim();
  }

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
  const spread = tokens[3] != null ? parseLengthPx(tokens[3]) : 0;
  if (blur == null || spread == null) return null;

  return clampBoxShadowModel({
    inset,
    offsetX,
    offsetY,
    blur,
    spread,
    colorHex: color.hex,
    opacity: color.alpha > 0 ? color.alpha : DEFAULT_BOX_SHADOW_MODEL.opacity,
  });
}

/**
 * Interpreta a primeira camada de um `box-shadow` CSS.
 * Retorna `null` se vazio / none / inválido.
 */
export function parseBoxShadow(css?: string | null): BoxShadowModel | null {
  const stack = parseBoxShadowStack(css);
  return stack?.layers[0] ?? null;
}

/** Interpreta todas as camadas (falha se alguma for inválida). */
export function parseBoxShadowStack(css?: string | null): BoxShadowStack | null {
  const raw = (css ?? "").trim();
  if (!raw || raw.toLowerCase() === "none") return null;

  const parts = splitShadowLayers(raw);
  if (parts.length === 0) return null;

  const layers: BoxShadowModel[] = [];
  for (const part of parts) {
    const layer = parseSingleLayer(part);
    if (!layer) return null;
    layers.push(layer);
  }
  return { layers };
}

/** Pilha efetiva para edição: parse ou default de uma camada. */
export function resolveBoxShadowStack(css?: string | null): BoxShadowStack {
  return parseBoxShadowStack(css) ?? { layers: [{ ...DEFAULT_BOX_SHADOW_MODEL }] };
}

/** Modelo efetivo da primeira camada (compat Fase 1). */
export function resolveBoxShadowModel(css?: string | null): BoxShadowModel {
  return resolveBoxShadowStack(css).layers[0] ?? { ...DEFAULT_BOX_SHADOW_MODEL };
}

/**
 * Atualiza uma camada (default 0) preservando as demais.
 * Se não houver sombra, parte do default; cria camadas até o índice se necessário (até o máximo).
 */
export function patchBoxShadow(
  css: string | undefined,
  patch: Partial<BoxShadowModel>,
  layerIndex = 0,
): string {
  const stack = resolveBoxShadowStack(css);
  const index = Math.max(0, Math.min(MAX_BOX_SHADOW_LAYERS - 1, layerIndex));
  while (stack.layers.length <= index) {
    stack.layers.push({ ...DEFAULT_AMBIENT_SHADOW_LAYER });
  }
  const current = stack.layers[index] ?? { ...DEFAULT_BOX_SHADOW_MODEL };
  stack.layers[index] = clampBoxShadowModel({ ...current, ...patch });
  return formatBoxShadowStack(stack);
}

/** Adiciona segunda camada (ambiente) se ainda não existir. */
export function addBoxShadowLayer(css: string | undefined): string {
  const stack = resolveBoxShadowStack(css);
  if (stack.layers.length >= MAX_BOX_SHADOW_LAYERS) {
    return formatBoxShadowStack(stack);
  }
  const baseInset = stack.layers[0]?.inset ?? false;
  stack.layers.push({ ...DEFAULT_AMBIENT_SHADOW_LAYER, inset: baseInset });
  return formatBoxShadowStack(stack);
}

/** Remove a camada no índice (mínimo 1 camada). */
export function removeBoxShadowLayer(css: string | undefined, layerIndex: number): string {
  const stack = resolveBoxShadowStack(css);
  if (stack.layers.length <= 1) {
    return formatBoxShadowStack(stack);
  }
  const index = Math.max(0, Math.min(stack.layers.length - 1, layerIndex));
  stack.layers.splice(index, 1);
  return formatBoxShadowStack(stack);
}
