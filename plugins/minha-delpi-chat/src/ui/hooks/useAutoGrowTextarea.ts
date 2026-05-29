import { useCallback, useLayoutEffect, useRef } from "react";

export type UseAutoGrowTextareaOptions = {
  value: string;
  /** Espaço reservado abaixo do campo até a borda da viewport (px). */
  bottomInset?: number;
  /** Teto absoluto de altura (px). */
  maxHeightCapPx?: number;
};

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

export function useAutoGrowTextarea({
  value,
  bottomInset = 16,
  maxHeightCapPx = 280,
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
    const viewportLimit = Math.max(
      minHeightPx,
      window.innerHeight - element.getBoundingClientRect().top - bottomInset,
    );
    const maxHeight = Math.min(maxHeightCapPx, viewportLimit);
    const nextHeight = Math.min(Math.max(contentHeight, minHeightPx), maxHeight);

    element.style.height = `${nextHeight}px`;
    element.style.overflowY = contentHeight > maxHeight ? "auto" : "hidden";
  }, [bottomInset, maxHeightCapPx]);

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
      observer?.disconnect();
    };
  }, [syncHeight]);

  return { ref, syncHeight };
}
