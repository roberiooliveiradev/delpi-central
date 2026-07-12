import { colorToCss, cssToColorValue, clampAlpha } from "./colorUtils";

/** Modelo estruturado de uma sombra drop (Fase 1 — uma camada). */
export type BoxShadowModel = {
  offsetX: number;
  offsetY: number;
  blur: number;
  spread: number;
  /** Hex `#rrggbb`. */
  colorHex: string;
  /** Opacidade 0–1. */
  opacity: number;
};

export const DEFAULT_BOX_SHADOW_MODEL: BoxShadowModel = {
  offsetX: 0,
  offsetY: 4,
  blur: 14,
  spread: 0,
  colorHex: "#000000",
  opacity: 0.28,
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
  // CSS aceita `0` sem unidade; alinha aos presets do comunicado.
  if (rounded === 0) return "0";
  return `${rounded}px`;
}

/** Compara duas strings box-shadow pela geometria/cor (ignora formatação). */
export function boxShadowsEqual(a?: string | null, b?: string | null): boolean {
  const left = (a ?? "").trim();
  const right = (b ?? "").trim();
  if (left === right) return true;
  const modelA = parseBoxShadow(left);
  const modelB = parseBoxShadow(right);
  if (!modelA || !modelB) return false;
  return (
    modelA.offsetX === modelB.offsetX &&
    modelA.offsetY === modelB.offsetY &&
    modelA.blur === modelB.blur &&
    modelA.spread === modelB.spread &&
    modelA.colorHex === modelB.colorHex &&
    Math.abs(modelA.opacity - modelB.opacity) < 0.001
  );
}

function clampShadowNumber(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, value));
}

export function clampBoxShadowModel(model: BoxShadowModel): BoxShadowModel {
  return {
    offsetX: clampShadowNumber(model.offsetX, -80, 80),
    offsetY: clampShadowNumber(model.offsetY, -80, 80),
    blur: clampShadowNumber(model.blur, 0, 120),
    spread: clampShadowNumber(model.spread, -40, 60),
    colorHex: model.colorHex,
    opacity: clampAlpha(model.opacity),
  };
}

/** Serializa o modelo para CSS `box-shadow` (uma camada externa). */
export function formatBoxShadow(model: BoxShadowModel): string {
  const next = clampBoxShadowModel(model);
  const color = colorToCss({ hex: next.colorHex, alpha: next.opacity });
  const parts = [
    formatLengthPx(next.offsetX),
    formatLengthPx(next.offsetY),
    formatLengthPx(next.blur),
  ];
  if (next.spread !== 0) {
    parts.push(formatLengthPx(next.spread));
  }
  parts.push(color);
  return parts.join(" ");
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

/**
 * Interpreta a primeira camada de um `box-shadow` CSS.
 * Retorna `null` se vazio / none / inválido.
 */
export function parseBoxShadow(css?: string | null): BoxShadowModel | null {
  const raw = (css ?? "").trim();
  if (!raw || raw.toLowerCase() === "none") return null;

  const firstLayer = splitShadowLayers(raw)[0] ?? "";
  if (!firstLayer) return null;

  let rest = firstLayer.replace(/^inset\s+/i, "").trim();

  // Cor no final: rgba()/rgb()/#hex
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
    offsetX,
    offsetY,
    blur,
    spread,
    colorHex: color.hex,
    opacity: color.alpha > 0 ? color.alpha : DEFAULT_BOX_SHADOW_MODEL.opacity,
  });
}

/** Modelo efetivo para edição: parse ou default se sem sombra. */
export function resolveBoxShadowModel(css?: string | null): BoxShadowModel {
  return parseBoxShadow(css) ?? { ...DEFAULT_BOX_SHADOW_MODEL };
}

export function patchBoxShadow(
  css: string | undefined,
  patch: Partial<BoxShadowModel>,
): string {
  const base = resolveBoxShadowModel(css);
  return formatBoxShadow({ ...base, ...patch });
}
