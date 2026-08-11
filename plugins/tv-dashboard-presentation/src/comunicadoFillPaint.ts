import type { CSSProperties, ReactElement } from "react";
import { createElement } from "react";

import {
  fillToCssBackground,
  normalizeFillAngle,
  normalizeGradientStops,
  solidFromFill,
  type DelpiFill,
} from "@delpi/plugin-ui/index";

import type { ComunicadoBlockStyle } from "./comunicadoTypes";

export function cssAngleToSvgGradientLine(angle: number): {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
} {
  const deg = normalizeFillAngle(angle);
  const rad = (deg * Math.PI) / 180;
  const x = Math.sin(rad);
  const y = -Math.cos(rad);
  return {
    x1: 0.5 - x / 2,
    y1: 0.5 - y / 2,
    x2: 0.5 + x / 2,
    y2: 0.5 + y / 2,
  };
}

export function resolveStyleFillCss(
  style: ComunicadoBlockStyle | null | undefined,
  fallback = "transparent",
): string {
  if (style?.fillPaint) return fillToCssBackground(style.fillPaint);
  return style?.fill ?? style?.backgroundColor ?? fallback;
}

export function resolveStyleStrokeCss(
  style: ComunicadoBlockStyle | null | undefined,
  fallback = "transparent",
): string {
  if (style?.strokePaint) return solidFromFill(style.strokePaint);
  return style?.stroke ?? style?.borderColor ?? fallback;
}

export function resolveSvgPaintRef(
  paint: DelpiFill | undefined,
  hex: string,
  gradientId: string,
): string {
  if (paint?.kind === "gradient") return `url(#${gradientId})`;
  if (paint?.kind === "none") return "transparent";
  if (paint?.kind === "solid") return paint.color;
  return hex;
}

/**
 * Contorno em caixa CSS: `border-color` não aceita gradiente.
 * Camada 1 = preenchimento (padding-box); camada 2 = stroke (border-box).
 */
export function applyCssShapePaints(
  css: CSSProperties,
  params: {
    fillPaint?: DelpiFill;
    strokePaint?: DelpiFill;
    fillHex?: string;
    strokeHex?: string;
    strokeWidth: number;
  },
): void {
  const { fillPaint, strokePaint, fillHex, strokeHex = "transparent", strokeWidth } = params;
  if (strokePaint?.kind === "gradient" && strokeWidth > 0) {
    const fillColor =
      fillPaint?.kind === "solid"
        ? fillPaint.color
        : fillPaint?.kind === "none"
          ? "transparent"
          : (fillHex ?? "transparent");
    const fillLayer =
      fillPaint?.kind === "gradient"
        ? fillToCssBackground(fillPaint)
        : `linear-gradient(${fillColor}, ${fillColor})`;
    css.border = `${strokeWidth}px solid transparent`;
    css.backgroundImage = `${fillLayer}, ${fillToCssBackground(strokePaint)}`;
    css.backgroundOrigin = "border-box";
    css.backgroundClip = "padding-box, border-box";
    css.backgroundColor = "transparent";
    return;
  }
  css.border = `${strokeWidth}px solid ${
    strokePaint?.kind === "none" ? "transparent" : strokeHex
  }`;
  applyFillPaintBackground(css, fillPaint, fillHex);
}

export function applyFillPaintBackground(
  css: CSSProperties,
  paint: DelpiFill | undefined,
  hex?: string,
): void {
  if (paint?.kind === "gradient") {
    css.backgroundImage = fillToCssBackground(paint);
    css.backgroundColor = "transparent";
    return;
  }
  if (paint?.kind === "none") {
    css.backgroundColor = "transparent";
    return;
  }
  const color = paint?.kind === "solid" ? paint.color : hex;
  if (color && color !== "transparent") css.backgroundColor = color;
}

export function applyColorPaintToCss(
  css: CSSProperties,
  paint: DelpiFill | undefined,
): boolean {
  if (paint?.kind !== "gradient") return false;
  css.backgroundImage = fillToCssBackground(paint);
  css.backgroundClip = "text";
  css.WebkitBackgroundClip = "text";
  css.color = "transparent";
  css.WebkitTextFillColor = "transparent";
  return true;
}

export function createSvgLinearGradientDef(
  id: string,
  fill: DelpiFill,
): ReactElement | null {
  if (fill.kind !== "gradient") return null;
  const stops = normalizeGradientStops(fill.stops);
  const { x1, y1, x2, y2 } = cssAngleToSvgGradientLine(fill.angle);
  return createElement(
    "linearGradient",
    { id, gradientUnits: "objectBoundingBox", x1, y1, x2, y2 },
    ...stops.map((stop, index) =>
      createElement("stop", {
        key: `${stop.position}-${index}`,
        offset: `${stop.position}%`,
        stopColor: stop.color,
        stopOpacity: stop.opacity ?? 1,
      }),
    ),
  );
}
