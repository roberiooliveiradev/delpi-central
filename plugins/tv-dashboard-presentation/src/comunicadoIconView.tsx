import {
  DECK_COLOR_SURFACE,
  DECK_SHAPE_DEFAULTS,
  ensureComunicadoDualClass,
  resolveLucideIconOrFallback,
} from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import type { CSSProperties } from "react";

import {
  applyCssShapePaints,
  applyFillPaintBackground,
  resolveStyleStrokeCss,
} from "./comunicadoFillPaint";
import type { ComunicadoIconBlock } from "./comunicadoTypes";

/** Cores legadas tratadas como «sem escolha explícita» → accent das formas. */
const LEGACY_ICON_COLORS = new Set([
  "#ffffff",
  "#fff",
  "white",
  DECK_COLOR_SURFACE.toLowerCase(),
]);

export function resolveComunicadoLucideIcon(name: string): LucideIcon {
  return resolveLucideIconOrFallback(name, "Star");
}

/** Cor do traço do ícone — padrão alinhado ao preenchimento das formas. */
export function resolveComunicadoIconColor(block: ComunicadoIconBlock): string {
  // Escolha explícita no seletor grava `colorPaint` — é o sinal que distingue
  // branco escolhido pelo usuário do branco legado («sem escolha explícita»).
  const paint = block.style?.colorPaint;
  if (paint?.kind === "solid" && typeof paint.color === "string" && paint.color.trim()) {
    return paint.color;
  }
  const raw = block.style?.color;
  if (raw == null || raw === "" || LEGACY_ICON_COLORS.has(String(raw).trim().toLowerCase())) {
    return DECK_SHAPE_DEFAULTS.fill;
  }
  return String(raw);
}

/** Espessura Lucide — `iconStrokeWidth` (legado: strokeWidth sem contorno de caixa). */
export function resolveComunicadoIconStrokeWidth(block: ComunicadoIconBlock): number {
  const dedicated = block.style?.iconStrokeWidth;
  if (typeof dedicated === "number" && Number.isFinite(dedicated) && dedicated > 0) {
    return dedicated;
  }
  const style = block.style ?? {};
  const effectiveStroke = resolveStyleStrokeCss(style, "transparent");
  const hasBoxStroke = effectiveStroke !== "transparent";
  const legacy = style.strokeWidth;
  if (
    !hasBoxStroke &&
    typeof legacy === "number" &&
    Number.isFinite(legacy) &&
    legacy > 0 &&
    legacy <= 6
  ) {
    return legacy;
  }
  return 2;
}

/**
 * Chrome da caixa atrás do glifo — mesmos resolvers de fill/stroke das formas
 * (`applyCssShapePaints` / `resolveStyleStrokeCss` / `applyFillPaintBackground`).
 */
export function resolveComunicadoIconChromeStyle(
  block: ComunicadoIconBlock,
  options?: { fontScale?: number },
): CSSProperties {
  const fontScale = options?.fontScale ?? 1;
  const style = block.style ?? {};
  const css: CSSProperties = {
    width: "100%",
    height: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxSizing: "border-box",
  };

  const fillHex = style.fill ?? style.backgroundColor;
  const strokeHex = resolveStyleStrokeCss(style, "transparent");
  const strokeWidth =
    typeof style.strokeWidth === "number" && Number.isFinite(style.strokeWidth)
      ? Math.max(0, style.strokeWidth * fontScale)
      : 0;

  if (style.strokePaint?.kind === "gradient" && strokeWidth > 0) {
    applyCssShapePaints(css, {
      fillPaint: style.fillPaint,
      strokePaint: style.strokePaint,
      fillHex,
      strokeHex,
      strokeWidth,
    });
  } else {
    const hasFillPaint =
      style.fillPaint?.kind === "solid" ||
      style.fillPaint?.kind === "gradient" ||
      style.fillPaint?.kind === "none";
    const hasFillHex =
      typeof fillHex === "string" && fillHex.trim() !== "" && fillHex !== "transparent";
    if (hasFillPaint || hasFillHex) {
      applyFillPaintBackground(css, style.fillPaint, fillHex);
    }
    if (strokeHex !== "transparent" && strokeWidth > 0) {
      css.border = `${strokeWidth}px solid ${strokeHex}`;
    }
  }

  if (typeof style.borderRadius === "number" && Number.isFinite(style.borderRadius)) {
    css.borderRadius = Math.max(0, style.borderRadius * fontScale);
  }

  const shadow = typeof style.boxShadow === "string" ? style.boxShadow.trim() : "";
  if (shadow) {
    css.boxShadow = shadow;
  }

  return css;
}

export function ComunicadoIconGraphic({
  block,
  style,
  fontScale = 1,
}: {
  block: ComunicadoIconBlock;
  style?: CSSProperties;
  fontScale?: number;
}) {
  const Icon = resolveComunicadoLucideIcon(block.iconName);
  const color = resolveComunicadoIconColor(block);
  const strokeWidth = resolveComunicadoIconStrokeWidth(block);
  const chrome = resolveComunicadoIconChromeStyle(block, { fontScale });

  return (
    <div className={ensureComunicadoDualClass("tdp-comunicado__icon-wrap")} style={{ ...chrome, ...style }}>
      <Icon
        className={ensureComunicadoDualClass("tdp-comunicado__icon-svg")}
        color={color}
        strokeWidth={strokeWidth}
        aria-hidden="true"
      />
    </div>
  );
}
