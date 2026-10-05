import {
  forwardRef,
  type CSSProperties,
  type HTMLAttributes,
  type ReactNode,
} from "react";

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
} & Omit<HTMLAttributes<HTMLDivElement>, "className" | "style" | "children"> & {
    [dataAttr: `data-${string}`]: string | number | boolean | undefined;
  };

/**
 * Moldura presentacional do slide personalizado (fundo + stage).
 * Domínio TV (blocos, fonts, master) fica em `tv-dashboard-presentation`.
 * CSS: `styles/comunicado-stage.css` (`.delpi-ui-comunicado*`).
 *
 * Aceita `ref` e atributos extras no root — o editor ancora medições de
 * drag e handlers de context menu no mesmo elemento da moldura.
 */
export const ComunicadoStageFrame = forwardRef<
  HTMLDivElement,
  ComunicadoStageFrameProps
>(function ComunicadoStageFrame(
  {
    children,
    style,
    className,
    stageClassName,
    backgroundLayer,
    ...rest
  },
  ref,
) {
  const bem = comunicadoStageBemClasses("tdp");
  return (
    <div
      ref={ref}
      className={ensureComunicadoDualClass(className ?? bem.root)}
      style={style}
      {...rest}
    >
      {backgroundLayer}
      <div className={ensureComunicadoDualClass(stageClassName ?? bem.stage)}>{children}</div>
    </div>
  );
});
