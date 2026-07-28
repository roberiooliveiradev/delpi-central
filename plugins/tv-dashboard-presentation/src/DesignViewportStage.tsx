import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

import {
  measurePresentationViewportSize,
  resolvePresentationFitMode,
  type PresentationFitMode,
  type PresentationFitResolved,
  type PresentationFitSurface,
} from "./presentationFitPolicy";
import { resolveViewportPixelSize } from "./viewportPixelSize";

/** @deprecated Use `PresentationFitMode` — mantido para imports existentes. */
export type DesignViewportFitMode = PresentationFitMode;

type Props = {
  viewportProfile?: string | null;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
  style?: CSSProperties;
  /**
   * Superfície de consumo — alimenta a política canônica (`presentationFitPolicy`).
   * Default: `preview` (contain).
   */
  surface?: PresentationFitSurface;
  /**
   * `auto` (padrão) resolve contain|cover pela surface + orientação.
   * `contain` / `cover` forçam o modo (overrides).
   */
  fit?: PresentationFitMode;
};

/**
 * Bleed zero na apresentação/prévia: o stage escala só a moldura de design.
 * Conteúdo com frame fora de 0–100% é clipado em `__design` (`overflow: hidden`).
 * Pasteboard (itens visíveis fora da moldura) existe só no editor.
 */
export const DESIGN_VIEWPORT_BLEED_RATIO = 0;

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
  fit: PresentationFitResolved = "contain",
): number {
  if (containerWidth <= 0 || containerHeight <= 0 || designWidth <= 0 || designHeight <= 0) {
    return 0;
  }
  const sx = containerWidth / designWidth;
  const sy = containerHeight / designHeight;
  return fit === "cover" ? Math.max(sx, sy) : Math.min(sx, sy);
}

/**
 * Caixa de layout pós-escala (o que webviews/kiosk medem em scrollWidth).
 * Diferente do box pré-`transform: scale`, que permanece no tamanho de design
 * e desloca o «ajustar à tela» de apps como Open Pen Drive.
 */
export function computeDesignViewportLayoutBox(
  outerW: number,
  outerH: number,
  scale: number,
): { width: number; height: number } {
  if (!(scale > 0) || !(outerW > 0) || !(outerH > 0)) {
    return { width: 0, height: 0 };
  }
  return { width: outerW * scale, height: outerH * scale };
}

/**
 * Renderiza o slide no tamanho de design do `viewportProfile` e aplica escala
 * uniforme para encaixar no container (prévia admin, TV pública, filmstrip).
 *
 * - Posições/tamanhos: frames `%` intactos (sem reconstruir layout).
 * - Clip: o que está fora da moldura 1080p não pinta no letterbox.
 * - Layout box = tamanho visual (scale via `transform-origin: top left`).
 * - Fit: `presentationFitPolicy` (kiosk≈cover / preview≈contain / orientação).
 * - Editor: pasteboard em `.td-composer__canvas` — não usa este stage.
 */
export function DesignViewportStage({
  viewportProfile,
  children,
  className,
  contentClassName,
  style,
  surface = "preview",
  fit = "auto",
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState<number | null>(null);
  const [resolvedFit, setResolvedFit] = useState<PresentationFitResolved>("contain");
  const { width, height } = resolveViewportPixelSize(viewportProfile);
  const { bleedX, bleedY, outerW, outerH } = computeDesignViewportBleedSize(width, height);

  useLayoutEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const updateScale = () => {
      const { width: cw, height: ch } = measurePresentationViewportSize(node);
      const nextFit = resolvePresentationFitMode({
        surface,
        fit,
        designWidth: width,
        designHeight: height,
        containerWidth: cw,
        containerHeight: ch,
      });
      const next = computeDesignViewportScale(cw, ch, width, height, nextFit);
      if (next > 0) {
        setResolvedFit(nextFit);
        setScale(next);
      }
    };

    updateScale();
    const observer = new ResizeObserver(updateScale);
    observer.observe(node);
    const vv = typeof window !== "undefined" ? window.visualViewport : null;
    vv?.addEventListener("resize", updateScale);
    vv?.addEventListener("scroll", updateScale);
    window.addEventListener("orientationchange", updateScale);
    return () => {
      observer.disconnect();
      vv?.removeEventListener("resize", updateScale);
      vv?.removeEventListener("scroll", updateScale);
      window.removeEventListener("orientationchange", updateScale);
    };
  }, [fit, height, surface, width]);

  const ready = scale != null && scale > 0;
  const layout = computeDesignViewportLayoutBox(outerW, outerH, scale ?? 0);

  return (
    <div
      ref={containerRef}
      className={["tdp-design-viewport", className].filter(Boolean).join(" ")}
      data-fit={resolvedFit}
      data-surface={surface}
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
        className="tdp-design-viewport__frame"
        data-layout-w={ready ? Math.round(layout.width) : undefined}
        data-layout-h={ready ? Math.round(layout.height) : undefined}
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: layout.width,
          height: layout.height,
          marginLeft: -layout.width / 2,
          marginTop: -layout.height / 2,
          overflow: "hidden",
          visibility: ready ? "visible" : "hidden",
        }}
      >
        <div
          className={["tdp-design-viewport__stage", contentClassName].filter(Boolean).join(" ")}
          style={{
            width: outerW,
            height: outerH,
            transform: ready ? `scale(${scale})` : "scale(0)",
            transformOrigin: "top left",
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
              overflow: "hidden",
            }}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
