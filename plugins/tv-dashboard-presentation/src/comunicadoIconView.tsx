import { DECK_COLOR_SURFACE, DECK_SHAPE_DEFAULTS, resolveLucideIconOrFallback } from "@delpi/plugin-ui/index";
import type { LucideIcon } from "lucide-react";
import type { CSSProperties } from "react";

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
  const raw = block.style?.color;
  if (raw == null || raw === "" || LEGACY_ICON_COLORS.has(String(raw).trim().toLowerCase())) {
    return DECK_SHAPE_DEFAULTS.fill;
  }
  return String(raw);
}

export function resolveComunicadoIconStrokeWidth(block: ComunicadoIconBlock): number {
  const width = block.style?.strokeWidth;
  return typeof width === "number" && Number.isFinite(width) && width > 0 ? width : 2;
}

export function ComunicadoIconGraphic({
  block,
  style,
}: {
  block: ComunicadoIconBlock;
  style?: CSSProperties;
}) {
  const Icon = resolveComunicadoLucideIcon(block.iconName);
  const color = resolveComunicadoIconColor(block);
  const strokeWidth = resolveComunicadoIconStrokeWidth(block);

  return (
    <div className="tdp-comunicado__icon-wrap" style={style}>
      <Icon
        className="tdp-comunicado__icon-svg"
        color={color}
        strokeWidth={strokeWidth}
        aria-hidden="true"
      />
    </div>
  );
}
