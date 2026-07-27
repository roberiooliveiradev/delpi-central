import type { CSSProperties } from "react";

export type RichComunicadoMasterLogoProps = {
  url?: string | null;
  frame?: { x?: number; y?: number; w?: number; h?: number } | null;
  opacity?: number;
  /** Classe CSS (editor: td-composer__master-logo; TV: tdp-comunicado__master-logo). */
  className?: string;
};

/**
 * Logo master canônico — editor e apresentação usam o mesmo layout %.
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
    left: `${frame?.x ?? 2}%`,
    top: `${frame?.y ?? 2}%`,
    width: `${frame?.w ?? 12}%`,
    height: `${frame?.h ?? 10}%`,
    opacity,
    zIndex: 0,
    pointerEvents: "none",
    /* Aspas: URLs com query (`?access_token=`) ou caracteres especiais. */
    backgroundImage: `url(${JSON.stringify(url)})`,
    backgroundSize: "contain",
    backgroundRepeat: "no-repeat",
    backgroundPosition: "center",
  };
  return <div className={className} aria-hidden style={style} />;
}
