import { useLayoutEffect, useRef, useState, type ReactNode } from "react";

export type CenteredScaledPreviewProps = {
  /** Largura de referência do conteúdo (ex.: palco 16:9 em 320px). */
  referenceWidth: number;
  /** Altura de referência do conteúdo. */
  referenceHeight: number;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
};

/**
 * Encaixa conteúdo em um retângulo fixo com escala uniforme e centralização —
 * mesmo padrão visual de `object-fit: contain` usado em `FilePreviewView` para imagens.
 */
export function CenteredScaledPreview({
  referenceWidth,
  referenceHeight,
  children,
  className,
  contentClassName,
}: CenteredScaledPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useLayoutEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const updateScale = () => {
      const width = node.clientWidth;
      const height = node.clientHeight;
      if (width > 0 && height > 0) {
        setScale(Math.min(width / referenceWidth, height / referenceHeight));
      }
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(node);
    return () => observer.disconnect();
  }, [referenceHeight, referenceWidth]);

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
          transform: `scale(${scale})`,
        }}
      >
        {children}
      </div>
    </div>
  );
}
