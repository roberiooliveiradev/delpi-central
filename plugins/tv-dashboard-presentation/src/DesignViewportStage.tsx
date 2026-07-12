import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

import { resolveViewportPixelSize } from "./viewportPixelSize";

type Props = {
  viewportProfile?: string | null;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
  style?: CSSProperties;
};

/**
 * Renderiza o slide no tamanho de design do `viewportProfile` e aplica escala
 * uniforme (`object-fit: contain`) para preencher o container sem distorcer.
 */
export function DesignViewportStage({
  viewportProfile,
  children,
  className,
  contentClassName,
  style,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState<number | null>(null);
  const { width, height } = resolveViewportPixelSize(viewportProfile);

  useLayoutEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const updateScale = () => {
      const cw = node.clientWidth;
      const ch = node.clientHeight;
      if (cw > 0 && ch > 0 && width > 0 && height > 0) {
        setScale(Math.min(cw / width, ch / height));
      }
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(node);
    return () => observer.disconnect();
  }, [height, width]);

  const ready = scale != null && scale > 0;

  return (
    <div
      ref={containerRef}
      className={["tdp-design-viewport", className].filter(Boolean).join(" ")}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
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
