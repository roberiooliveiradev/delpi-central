import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

import { resolveViewportPixelSize } from "./viewportPixelSize";

export type DesignViewportFitMode = "contain" | "cover";

type Props = {
  viewportProfile?: string | null;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
  style?: CSSProperties;
  /**
   * `contain` (padrão) — letterbox/pillarbox sem cortar.
   * `cover` — preenche o container (pode cortar bordas do slide).
   */
  fit?: DesignViewportFitMode;
};

/**
 * Pasteboard dentro do layer com `transform: scale`.
 * Ancestral com `overflow: hidden` + transform clipa filhos ao border-box do
 * elemento transformado — sem bleed, logo/card com frame negativo some na
 * borda da moldura (quebra paridade com o editor).
 */
export const DESIGN_VIEWPORT_BLEED_RATIO = 0.5;

export type DesignViewportBleedSize = {
  bleedX: number;
  bleedY: number;
  outerW: number;
  outerH: number;
};

export function computeDesignViewportBleedSize(
  designWidth: number,
  designHeight: number,
  bleedRatio: number = DESIGN_VIEWPORT_BLEED_RATIO,
): DesignViewportBleedSize {
  const bleedX = designWidth * bleedRatio;
  const bleedY = designHeight * bleedRatio;
  return {
    bleedX,
    bleedY,
    outerW: designWidth + 2 * bleedX,
    outerH: designHeight + 2 * bleedY,
  };
}

/** Escala uniforme do slide de design no retângulo do container. */
export function computeDesignViewportScale(
  containerWidth: number,
  containerHeight: number,
  designWidth: number,
  designHeight: number,
  fit: DesignViewportFitMode = "contain",
): number {
  if (containerWidth <= 0 || containerHeight <= 0 || designWidth <= 0 || designHeight <= 0) {
    return 0;
  }
  const sx = containerWidth / designWidth;
  const sy = containerHeight / designHeight;
  return fit === "cover" ? Math.max(sx, sy) : Math.min(sx, sy);
}

/**
 * Renderiza o slide no tamanho de design do `viewportProfile` e aplica escala
 * uniforme para encaixar no container.
 *
 * - `contain` — letterbox/pillarbox sem cortar (prévia, kiosk e editor).
 * - `cover` — preenche o container (pode cortar bordas; só sob demanda).
 *
 * O stage transformado inclui pasteboard (bleed) ao redor do retângulo de
 * design — itens fora da moldura pintam no letterbox, como no editor.
 * Clip físico permanece no container / `.tdp-stage` / kiosk.
 */
export function DesignViewportStage({
  viewportProfile,
  children,
  className,
  contentClassName,
  style,
  fit = "contain",
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState<number | null>(null);
  const { width, height } = resolveViewportPixelSize(viewportProfile);
  const { bleedX, bleedY, outerW, outerH } = computeDesignViewportBleedSize(width, height);

  useLayoutEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const updateScale = () => {
      const next = computeDesignViewportScale(
        node.clientWidth,
        node.clientHeight,
        width,
        height,
        fit,
      );
      if (next > 0) setScale(next);
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(node);
    return () => observer.disconnect();
  }, [fit, height, width]);

  const ready = scale != null && scale > 0;

  return (
    <div
      ref={containerRef}
      className={["tdp-design-viewport", className].filter(Boolean).join(" ")}
      style={{
        position: "absolute",
        inset: 0,
        width: "auto",
        height: "auto",
        overflow: "hidden",
        ...style,
      }}
    >
      <div
        className={["tdp-design-viewport__stage", contentClassName].filter(Boolean).join(" ")}
        style={{
          width: outerW,
          height: outerH,
          position: "absolute",
          left: "50%",
          top: "50%",
          marginLeft: -outerW / 2,
          marginTop: -outerH / 2,
          transform: ready ? `scale(${scale})` : "scale(0)",
          transformOrigin: "center center",
          visibility: ready ? "visible" : "hidden",
          overflow: "hidden",
        }}
      >
        <div
          className="tdp-design-viewport__design"
          data-viewport={viewportProfile || "1080p"}
          style={{
            position: "absolute",
            left: bleedX,
            top: bleedY,
            width,
            height,
            overflow: "visible",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
