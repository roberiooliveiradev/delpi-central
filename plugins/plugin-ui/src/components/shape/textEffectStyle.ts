/** Tipografia: text-shadow + WebKit stroke + reflexo — compartilhado KPI/chart/texto. */

import type { CSSProperties } from "react";

export type TextEffectStyleFields = {
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  /** Reflexo espelhado abaixo do texto (Chromium/`-webkit-box-reflect`). */
  textReflection?: boolean;
};

const DEFAULT_TEXT_REFLECTION =
  "below 2px linear-gradient(transparent 40%, rgba(0,0,0,0.35))";

export function applyTextEffectStyleToCss(
  style: TextEffectStyleFields | null | undefined,
  css: CSSProperties,
): void {
  if (!style) return;
  const shadow = typeof style.textShadow === "string" ? style.textShadow.trim() : "";
  if (shadow) css.textShadow = shadow;
  const strokeWidth = style.textStrokeWidth;
  const strokeColor = typeof style.textStrokeColor === "string" ? style.textStrokeColor.trim() : "";
  if (strokeWidth != null && strokeWidth > 0 && strokeColor) {
    css.WebkitTextStroke = `${strokeWidth}px ${strokeColor}`;
    (css as CSSProperties & { paintOrder?: string }).paintOrder = "stroke fill";
  }
  if (style.textReflection) {
    (css as CSSProperties & { WebkitBoxReflect?: string }).WebkitBoxReflect = DEFAULT_TEXT_REFLECTION;
  }
}
