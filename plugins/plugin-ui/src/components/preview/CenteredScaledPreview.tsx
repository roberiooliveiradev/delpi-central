import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

export type CenteredScaledPreviewProps = {
  /** Largura de referência do conteúdo (ex.: palco 16:9 canônico). */
  referenceWidth: number;
  /** Altura de referência do conteúdo. */
  referenceHeight: number;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
};

/**
 * Encaixa conteúdo em um retângulo fixo com escala uniforme e centralização —
 * mesmo padrão visual de `object-fit: contain`.
 *
 * Importante: o box de layout permanece no tamanho de referência; a escala é só
 * visual. Centraliza com left/top 50% + margem negativa (não depende de flex no
 * filho gigante), e só revela após medir o container — evita flash `scale(1)`
 * que mostra só um canto branco do slide 1080p no filmstrip.
 */
export function CenteredScaledPreview({
  referenceWidth,
  referenceHeight,
  children,
  className,
  contentClassName,
}: CenteredScaledPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState<number | null>(null);

  useLayoutEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const updateScale = () => {
      const width = node.clientWidth;
      const height = node.clientHeight;
      if (width > 0 && height > 0 && referenceWidth > 0 && referenceHeight > 0) {
        setScale(Math.min(width / referenceWidth, height / referenceHeight));
      }
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(node);
    return () => observer.disconnect();
  }, [referenceHeight, referenceWidth]);

  const ready = scale != null && scale > 0;

  return (
    <div
      ref={containerRef}
      className={["delpi-ui-centered-scaled-preview", className].filter(Boolean).join(" ")}
    >
      <div
        className={["delpi-ui-centered-scaled-preview__content", contentClassName]
          .filter(Boolean)
          .join(" ")}
        style={{
          width: referenceWidth,
          height: referenceHeight,
          position: "absolute",
          left: "50%",
          top: "50%",
          marginLeft: -referenceWidth / 2,
          marginTop: -referenceHeight / 2,
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
