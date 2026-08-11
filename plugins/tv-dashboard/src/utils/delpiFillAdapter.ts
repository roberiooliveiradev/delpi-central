import {
  fillToCssBackground,
  normalizeFillAngle,
  normalizeGradientStops,
  solidFromFill,
  stopsFromLegacyFromTo,
  type DelpiFill,
  type DelpiFillKind,
  type DelpiGradientStop,
} from "@delpi/plugin-ui/index";
import type { ComunicadoBackground, ComunicadoBlockStyle } from "@delpi/tv-dashboard-presentation";

/** TV liga Cor + Gradiente; RichText e outros hosts hex-only não passam isto. */
export const TV_ALLOWED_FILL_KINDS: readonly DelpiFillKind[] = ["solid", "gradient"];

export function backgroundToFill(background: ComunicadoBackground | undefined): DelpiFill {
  if (!background || background.type === "image") {
    return { kind: "solid", color: "#ffffff" };
  }
  if (background.type === "color") {
    if (!background.value || background.value === "transparent") return { kind: "none" };
    return { kind: "solid", color: background.value };
  }
  const stops =
    background.stops && background.stops.length >= 2
      ? normalizeGradientStops(background.stops)
      : stopsFromLegacyFromTo(background.from, background.to);
  return {
    kind: "gradient",
    angle: normalizeFillAngle(background.angle ?? 180),
    stops,
  };
}

export function fillToBackground(fill: DelpiFill): ComunicadoBackground {
  if (fill.kind === "none") return { type: "color", value: "transparent" };
  if (fill.kind === "solid") return { type: "color", value: fill.color };
  const stops = normalizeGradientStops(fill.stops);
  return {
    type: "gradient",
    from: stops[0]?.color ?? "#0f172a",
    to: stops[stops.length - 1]?.color ?? "#1e3a5f",
    angle: normalizeFillAngle(fill.angle),
    stops,
  };
}

export function styleToFill(
  style:
    | Pick<ComunicadoBlockStyle, "fill" | "fillPaint" | "backgroundColor">
    | null
    | undefined,
): DelpiFill {
  if (style?.fillPaint) return style.fillPaint;
  const hex = style?.fill ?? style?.backgroundColor;
  if (!hex || hex === "transparent") return { kind: "none" };
  return { kind: "solid", color: hex };
}

export function styleToStrokeFill(
  style: Pick<ComunicadoBlockStyle, "stroke" | "strokePaint" | "borderColor"> | null | undefined,
): DelpiFill {
  if (style?.strokePaint) return style.strokePaint;
  const hex = style?.stroke ?? style?.borderColor;
  if (!hex || hex === "transparent") return { kind: "none" };
  return { kind: "solid", color: hex };
}

export function styleToColorFill(
  style: Pick<ComunicadoBlockStyle, "color" | "colorPaint"> | null | undefined,
): DelpiFill {
  if (style?.colorPaint) return style.colorPaint;
  if (!style?.color || style.color === "transparent") return { kind: "none" };
  return { kind: "solid", color: style.color };
}

export function fillToFillStylePatch(fill: DelpiFill): Partial<ComunicadoBlockStyle> {
  if (fill.kind === "none") {
    return { fill: "transparent", backgroundColor: "transparent", fillPaint: undefined };
  }
  if (fill.kind === "solid") {
    return { fill: fill.color, backgroundColor: fill.color, fillPaint: undefined };
  }
  const hex = solidFromFill(fill);
  return { fill: hex, backgroundColor: hex, fillPaint: fill };
}

export function fillToStrokeStylePatch(
  fill: DelpiFill,
  extra?: Partial<ComunicadoBlockStyle>,
): Partial<ComunicadoBlockStyle> {
  if (fill.kind === "none") {
    return { stroke: "transparent", borderColor: "transparent", strokePaint: undefined, ...extra };
  }
  if (fill.kind === "solid") {
    return { stroke: fill.color, borderColor: fill.color, strokePaint: undefined, ...extra };
  }
  const hex = solidFromFill(fill);
  return { stroke: hex, borderColor: hex, strokePaint: fill, ...extra };
}

export function fillToColorStylePatch(fill: DelpiFill): Partial<ComunicadoBlockStyle> {
  if (fill.kind === "none") {
    return { color: "transparent", colorPaint: undefined };
  }
  if (fill.kind === "solid") {
    return { color: fill.color, colorPaint: undefined };
  }
  return { color: solidFromFill(fill), colorPaint: fill };
}

export function hexFromFill(fill: DelpiFill | undefined, fallback = "transparent"): string {
  if (!fill) return fallback;
  const hex = solidFromFill(fill);
  return hex || fallback;
}

export function cssBackgroundFromFill(fill: DelpiFill | undefined, fallback = "transparent"): string {
  if (!fill) return fallback;
  return fillToCssBackground(fill);
}

export type { DelpiFill, DelpiFillKind, DelpiGradientStop };
