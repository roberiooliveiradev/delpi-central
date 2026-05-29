import { useCallback, useLayoutEffect, useRef } from "react";

export type UseAutoGrowTextareaOptions = {
  value: string;
  /** Espaço reservado abaixo do campo até a borda da viewport (px). */
  bottomInset?: number;
  /** Fração da altura visível da viewport (ex.: 0.25 = 25%). */
  maxHeightViewportRatio?: number;
  /** Teto opcional de altura em px (além do ratio). */
  maxHeightCapPx?: number;
  /** Ajusta largura ao conteúdo (até o teto). */
  autoWidth?: boolean;
  /** Largura mínima em px quando autoWidth está ativo. */
  minWidthPx?: number;
  /** Largura máxima em px quando autoWidth está ativo. */
  maxWidthCapPx?: number;
  /** Margem horizontal reservada na viewport para largura máxima. */
  maxWidthViewportInset?: number;
};

function getViewportHeight(): number {
  if (typeof window === "undefined") {
    return 0;
  }

  return window.visualViewport?.height ?? window.innerHeight;
}

function measureTextareaContentHeight(element: HTMLTextAreaElement): number {
  const previous = {
    height: element.style.height,
    minHeight: element.style.minHeight,
    maxHeight: element.style.maxHeight,
    overflow: element.style.overflow,
  };

  element.style.overflow = "hidden";
  element.style.height = "auto";
  element.style.minHeight = "0";
  element.style.maxHeight = "none";

  const contentHeight = element.scrollHeight;

  element.style.height = previous.height;
  element.style.minHeight = previous.minHeight;
  element.style.maxHeight = previous.maxHeight;
  element.style.overflow = previous.overflow;

  return contentHeight;
}

function measureTextareaContentWidth(element: HTMLTextAreaElement): number {
  const previous = {
    width: element.style.width,
    minWidth: element.style.minWidth,
  };

  element.style.width = "0";
  element.style.minWidth = "0";

  const contentWidth = element.scrollWidth;

  element.style.width = previous.width;
  element.style.minWidth = previous.minWidth;

  return contentWidth;
}

function getViewportWidth(): number {
  if (typeof window === "undefined") {
    return 0;
  }

  return window.visualViewport?.width ?? window.innerWidth;
}

export function useAutoGrowTextarea({
  value,
  bottomInset = 16,
  maxHeightViewportRatio,
  maxHeightCapPx,
  autoWidth = false,
  minWidthPx = 0,
  maxWidthCapPx = 736,
  maxWidthViewportInset = 72,
}: UseAutoGrowTextareaOptions) {
  const ref = useRef<HTMLTextAreaElement>(null);

  const syncHeight = useCallback(() => {
    const element = ref.current;

    if (!element) {
      return;
    }

    const computed = getComputedStyle(element);
    const minHeightPx = Number.parseFloat(computed.minHeight) || 0;
    const contentHeight = measureTextareaContentHeight(element);
    const viewportHeight = getViewportHeight();
    const spaceBelow = Math.max(
      minHeightPx,
      viewportHeight - element.getBoundingClientRect().top - bottomInset,
    );

    const ratioCap =
      maxHeightViewportRatio != null
        ? Math.floor(viewportHeight * maxHeightViewportRatio)
        : null;

    const caps = [spaceBelow];

    if (ratioCap != null) {
      caps.push(ratioCap);
    }

    if (maxHeightCapPx != null) {
      caps.push(maxHeightCapPx);
    }

    const maxHeight = Math.min(...caps);
    const nextHeight = Math.min(Math.max(contentHeight, minHeightPx), maxHeight);

    element.style.height = `${nextHeight}px`;
    element.style.maxHeight = `${maxHeight}px`;
    element.style.overflowY = contentHeight > maxHeight ? "auto" : "hidden";

    if (autoWidth) {
      const minWidthFromStyle = Number.parseFloat(computed.minWidth) || 0;
      const minWidth = Math.max(minWidthPx, minWidthFromStyle);
      const contentWidth = measureTextareaContentWidth(element);
      const viewportWidth = getViewportWidth();
      const viewportMax = Math.max(minWidth, viewportWidth - maxWidthViewportInset);
      const maxWidth = Math.min(maxWidthCapPx, viewportMax);
      const nextWidth = Math.min(Math.max(contentWidth, minWidth), maxWidth);

      element.style.width = `${nextWidth}px`;
      element.style.maxWidth = `${maxWidth}px`;
      element.style.overflowX = contentWidth > maxWidth ? "auto" : "hidden";
    }
  }, [
    autoWidth,
    bottomInset,
    maxHeightCapPx,
    maxHeightViewportRatio,
    maxWidthCapPx,
    maxWidthViewportInset,
    minWidthPx,
  ]);

  useLayoutEffect(() => {
    syncHeight();
  }, [value, syncHeight]);

  useLayoutEffect(() => {
    const element = ref.current;

    if (!element) {
      return;
    }

    const handleResize = () => syncHeight();

    window.addEventListener("resize", handleResize);

    const visualViewport = window.visualViewport;

    visualViewport?.addEventListener("resize", handleResize);
    visualViewport?.addEventListener("scroll", handleResize);

    const observer =
      typeof ResizeObserver !== "undefined"
        ? new ResizeObserver(handleResize)
        : null;

    observer?.observe(element);

    if (typeof document !== "undefined" && document.fonts?.ready) {
      void document.fonts.ready.then(handleResize);
    }

    return () => {
      window.removeEventListener("resize", handleResize);
      visualViewport?.removeEventListener("resize", handleResize);
      visualViewport?.removeEventListener("scroll", handleResize);
      observer?.disconnect();
    };
  }, [syncHeight]);

  return { ref, syncHeight };
}
