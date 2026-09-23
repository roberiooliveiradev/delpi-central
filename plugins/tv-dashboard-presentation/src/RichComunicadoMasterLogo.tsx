import type { CSSProperties } from "react";

import { DELPI_BRAND_LOGO_FRAME } from "./delpiBrandLogo";
import { getDelpiBrandLogoConfig } from "./delpiBrandTheme";

export type RichComunicadoMasterLogoProps = {
  url?: string | null;
  frame?: { x?: number; y?: number; w?: number; h?: number } | null;
  opacity?: number;
  /** Classe CSS (editor: td-composer__master-logo; TV: tdp-comunicado__master-logo). */
  className?: string;
};

/**
 * Logo master canônico — editor e apresentação usam o mesmo layout %.
 * Posição/opacidade: ``delpiBrandTheme.json``.
 * zIndex mínimo 1 no paint (acima do grid z=0); ainda abaixo dos blocos de dados (≥2).
 */
export function RichComunicadoMasterLogo({
  url,
  frame,
  opacity = 1,
  className = "tdp-comunicado__master-logo delpi-ui-comunicado__master-logo",
}: RichComunicadoMasterLogoProps) {
  if (!url) return null;
  const logo = getDelpiBrandLogoConfig();
  const paintZ = Math.max(1, logo.zIndex ?? 0);
  const style: CSSProperties = {
    position: "absolute",
    left: `${frame?.x ?? DELPI_BRAND_LOGO_FRAME.x}%`,
    top: `${frame?.y ?? DELPI_BRAND_LOGO_FRAME.y}%`,
    width: `${frame?.w ?? DELPI_BRAND_LOGO_FRAME.w}%`,
    height: `${frame?.h ?? DELPI_BRAND_LOGO_FRAME.h}%`,
    opacity,
    zIndex: paintZ,
    pointerEvents: "none",
    objectFit: "contain",
    objectPosition: logo.backgroundPosition,
  };
  return (
    <img
      className={className}
      src={url}
      alt=""
      draggable={false}
      aria-hidden
      style={style}
    />
  );
}
