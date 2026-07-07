import type { LucideIcon } from "lucide-react";
import * as LucideIcons from "lucide-react";
import type { CSSProperties } from "react";

import type { ComunicadoIconBlock } from "./comunicadoTypes";

export function resolveComunicadoLucideIcon(name: string): LucideIcon {
  const Icon = (LucideIcons as unknown as Record<string, LucideIcon | undefined>)[name];
  return Icon ?? LucideIcons.Star;
}

export function ComunicadoIconGraphic({
  block,
  style,
}: {
  block: ComunicadoIconBlock;
  style?: CSSProperties;
}) {
  const Icon = resolveComunicadoLucideIcon(block.iconName);
  const color = block.style?.color ?? "#ffffff";
  const strokeWidth = block.style?.strokeWidth ?? 2;

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
