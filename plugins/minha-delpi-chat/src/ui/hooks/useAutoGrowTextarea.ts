import { useCallback, useLayoutEffect, useRef } from "react";

export type UseAutoGrowTextareaOptions = {
  value: string;
  /** Espaço reservado abaixo do campo até a borda da viewport (px). */
  bottomInset?: number;
  /** Teto absoluto de altura (px). */
  maxHeightCapPx?: number;
};

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

    element.style.height = "0px";

    const scrollHeight = element.scrollHeight;
    const minHeight = Number.parseFloat(getComputedStyle(element).minHeight) || 0;
    const viewportLimit = Math.max(
      minHeight,
      window.innerHeight - element.getBoundingClientRect().top - bottomInset,
    );
    const maxHeight = Math.min(maxHeightCapPx, viewportLimit);
    const nextHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);

    element.style.height = `${nextHeight}px`;
    element.style.overflowY = scrollHeight > maxHeight ? "auto" : "hidden";
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

    return () => {
      window.removeEventListener("resize", handleResize);
      observer?.disconnect();
    };
  }, [syncHeight]);

  return { ref, syncHeight };
}
