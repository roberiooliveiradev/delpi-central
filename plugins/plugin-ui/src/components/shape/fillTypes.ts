import { clampAlpha, colorToCss, cssToColorValue } from "./colorUtils";

export const MAX_GRADIENT_STOPS = 8;
export const MIN_GRADIENT_STOPS = 2;

export type DelpiFillSolid = { kind: "solid"; color: string };

export type DelpiGradientStop = {
  color: string;
  position: number;
  opacity?: number;
};

export type DelpiFillGradient = {
  kind: "gradient";
  angle: number;
  stops: DelpiGradientStop[];
};

export type DelpiFillNone = { kind: "none" };

export type DelpiFill = DelpiFillSolid | DelpiFillGradient | DelpiFillNone;

export type DelpiFillKind = "solid" | "gradient";

export function normalizeFillAngle(angle: number): number {
  if (!Number.isFinite(angle)) return 180;
  return ((Math.round(angle) % 360) + 360) % 360;
}

export function normalizeGradientStops(stops: readonly DelpiGradientStop[]): DelpiGradientStop[] {
  const cleaned = stops
    .map((stop) => ({
      color: typeof stop.color === "string" && stop.color.trim() ? stop.color.trim() : "#000000",
      position: Number.isFinite(stop.position) ? Math.min(100, Math.max(0, stop.position)) : 0,
      ...(stop.opacity != null ? { opacity: clampAlpha(stop.opacity) } : {}),
    }))
    .sort((a, b) => a.position - b.position)
    .slice(0, MAX_GRADIENT_STOPS);

  if (cleaned.length >= MIN_GRADIENT_STOPS) return cleaned;
  const first = cleaned[0] ?? { color: "#0f172a", position: 0 };
  const secondColor = varyStopColor(first.color);
  return [
    { ...first, position: 0 },
    { color: secondColor, position: 100 },
  ];
}

export function solidFromFill(fill: DelpiFill | undefined): string {
  if (!fill || fill.kind === "none") return "transparent";
  if (fill.kind === "solid") return fill.color;
  return fill.stops[0]?.color ?? "transparent";
}

export function fillToCssBackground(fill: DelpiFill | undefined): string {
  if (!fill || fill.kind === "none") return "transparent";
  if (fill.kind === "solid") return fill.color;
  const angle = normalizeFillAngle(fill.angle);
  const stops = normalizeGradientStops(fill.stops)
    .map((stop) => `${stopCssColor(stop)} ${stop.position}%`)
    .join(", ");
  return `linear-gradient(${angle}deg, ${stops})`;
}

export function stopsFromLegacyFromTo(from: string, to: string): DelpiGradientStop[] {
  return normalizeGradientStops([
    { color: from, position: 0 },
    { color: to, position: 100 },
  ]);
}

function stopCssColor(stop: DelpiGradientStop): string {
  if (stop.opacity == null || stop.opacity >= 1) return stop.color;
  const value = cssToColorValue(stop.color);
  return colorToCss({ ...value, alpha: clampAlpha(stop.opacity) });
}

function varyStopColor(color: string): string {
  const { hex } = cssToColorValue(color, "#1e3a5f");
  if (hex === "#1e3a5f") return "#0f172a";
  return "#1e3a5f";
}
