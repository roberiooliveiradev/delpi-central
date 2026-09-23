import type { CSSProperties } from "react";

import { DELPI_BRAND_LOGO_FRAME } from "./delpiBrandLogo";

export type RichComunicadoMasterLogoProps = {
  url?: string | null;
  frame?: { x?: number; y?: number; w?: number; h?: number } | null;
  opacity?: number;
  /** Classe CSS (editor: td-composer__master-logo; TV: tdp-comunicado__master-logo). */
  className?: string;
};

/**
 * Logo master canônico — editor e apresentação usam o mesmo layout %.
 * Brand default: canto inferior direito (não cobre título/KPI). zIndex 0 = sob os blocos.
 * Anti-padrão: segundo overlay só no composer ou só no RichComunicadoScreen.
 */
export function RichComunicadoMasterLogo({
  url,
  frame,
  opacity = 1,
  className = "tdp-comunicado__master-logo delpi-ui-comunicado__master-logo",
}: RichComunicadoMasterLogoProps) {
  if (!url) return null;
  const style: CSSProperties = {
    position: "absolute",
    left: `${frame?.x ?? DELPI_BRAND_LOGO_FRAME.x}%`,
    top: `${frame?.y ?? DELPI_BRAND_LOGO_FRAME.y}%`,
    width: `${frame?.w ?? DELPI_BRAND_LOGO_FRAME.w}%`,
    height: `${frame?.h ?? DELPI_BRAND_LOGO_FRAME.h}%`,
    opacity,
    zIndex: 0,
    pointerEvents: "none",
    /* Aspas: URLs com query (`?access_token=`) ou caracteres especiais. */
    backgroundImage: `url(${JSON.stringify(url)})`,
    backgroundSize: "contain",
    backgroundRepeat: "no-repeat",
    backgroundPosition: "bottom right",
  };
  return <div className={className} aria-hidden style={style} />;
}
