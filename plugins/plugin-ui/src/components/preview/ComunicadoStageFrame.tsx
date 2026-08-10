import type { CSSProperties, ReactNode } from "react";

import {
  comunicadoStageBemClasses,
  ensureComunicadoDualClass,
} from "../../utils/comunicadoStageBem";

export type ComunicadoStageFrameProps = {
  children: ReactNode;
  style?: CSSProperties;
  /** Classes do root (default: native-screen + dual comunicado). */
  className?: string;
  /** Classes do palco interno (default: dual `__stage`). */
  stageClassName?: string;
  /**
   * Camada de fundo (ex.: imagem cover) — irmã do palco, atrás dos blocos.
   * Cor/gradiente continuam em `style` no root.
   */
  backgroundLayer?: ReactNode;
};

/**
 * Moldura presentacional do slide personalizado (fundo + stage).
 * Domínio TV (blocos, fonts, master) fica em `tv-dashboard-presentation`.
 * CSS: `styles/comunicado-stage.css` (`.delpi-ui-comunicado*`).
 */
export function ComunicadoStageFrame({
  children,
  style,
  className,
  stageClassName,
  backgroundLayer,
}: ComunicadoStageFrameProps) {
  const bem = comunicadoStageBemClasses("tdp");
  return (
    <div className={ensureComunicadoDualClass(className ?? bem.root)} style={style}>
      {backgroundLayer}
      <div className={ensureComunicadoDualClass(stageClassName ?? bem.stage)}>{children}</div>
    </div>
  );
}
