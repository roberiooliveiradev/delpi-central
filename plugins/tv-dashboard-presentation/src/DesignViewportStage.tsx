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
 * uniforme para preencher o container sem distorcer (`object-fit: contain`).
 *
 * O container usa `position: absolute; inset: 0` para medir a área real do palco.
 * `position: relative` + `height: 100%` quebrava a prévia/kiosk quando a cadeia
 * de altura % colapsava ou um ancestral limitava a largura — o slide ficava
 * “flutuando” com faixas vazias em todos os lados.
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
        data-viewport={viewportProfile || "1080p"}
        style={{
          width,
          height,
          position: "absolute",
          left: "50%",
          top: "50%",
          marginLeft: -width / 2,
          marginTop: -height / 2,
          transform: ready ? `scale(${scale})` : "scale(0)",
          transformOrigin: "center center",
          visibility: ready ? "visible" : "hidden",
        }}
      >
        {children}
      </div>
    </div>
  );
}
