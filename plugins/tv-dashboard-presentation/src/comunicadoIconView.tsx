import { DECK_COLOR_SURFACE, DECK_SHAPE_DEFAULTS, resolveLucideIconOrFallback } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import type { CSSProperties } from "react";

import type { ComunicadoIconBlock } from "./comunicadoTypes";
import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

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
  const stroke = block.style?.stroke;
  const hasBoxStroke =
    typeof stroke === "string" && stroke.trim() !== "" && stroke !== "transparent";
  const legacy = block.style?.strokeWidth;
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
 * Chrome da caixa atrás do glifo (paridade com formas): fill, contorno, raio, sombra.
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

  const fill = style.fill;
  if (typeof fill === "string" && fill.trim() && fill !== "transparent") {
    css.backgroundColor = fill;
  }

  const stroke = style.stroke;
  const strokeWidth = style.strokeWidth;
  if (
    typeof stroke === "string" &&
    stroke.trim() &&
    stroke !== "transparent" &&
    typeof strokeWidth === "number" &&
    strokeWidth > 0
  ) {
    css.border = `${Math.max(0, strokeWidth * fontScale)}px solid ${stroke}`;
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
