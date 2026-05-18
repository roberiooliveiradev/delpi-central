import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";

type UseResizablePaneOptions = {
  storageKey: string;
  defaultWidth?: number;
  minWidth?: number;
  maxWidthRatio?: number;
  enabledMediaQuery?: string;
};

function readStoredWidth(storageKey: string, defaultWidth: number): number {
  if (typeof window === "undefined") {
    return defaultWidth;
  }

  const stored = window.localStorage.getItem(storageKey);
  const parsed = stored ? Number.parseInt(stored, 10) : Number.NaN;

  return Number.isFinite(parsed) && parsed > 0 ? parsed : defaultWidth;
}

export function useResizablePane({
  storageKey,
  defaultWidth = 420,
  minWidth = 300,
  maxWidthRatio = 0.52,
  enabledMediaQuery = "(min-width: 1181px)",
}: UseResizablePaneOptions) {
  const layoutRef = useRef<HTMLDivElement>(null);
  const widthRef = useRef(readStoredWidth(storageKey, defaultWidth));
  const [paneWidth, setPaneWidth] = useState(() => widthRef.current);
  const [splitEnabled, setSplitEnabled] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia(enabledMediaQuery);

    function syncEnabled() {
      setSplitEnabled(mediaQuery.matches);
    }

    syncEnabled();
    mediaQuery.addEventListener("change", syncEnabled);

    return () => {
      mediaQuery.removeEventListener("change", syncEnabled);
    };
  }, [enabledMediaQuery]);

  const clampWidth = useCallback(
    (nextWidth: number) => {
      const layout = layoutRef.current;
      const maxWidth = layout
        ? Math.max(minWidth, layout.getBoundingClientRect().width * maxWidthRatio)
        : defaultWidth * 2;

      return Math.min(Math.max(nextWidth, minWidth), maxWidth);
    },
    [defaultWidth, maxWidthRatio, minWidth],
  );

  const applyWidth = useCallback(
    (nextWidth: number) => {
      const clamped = clampWidth(nextWidth);
      widthRef.current = clamped;
      setPaneWidth(clamped);
    },
    [clampWidth],
  );

  const persistWidth = useCallback(() => {
    window.localStorage.setItem(storageKey, String(widthRef.current));
  }, [storageKey]);

  const onSplitterPointerDown = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (!splitEnabled) {
        return;
      }

      event.preventDefault();
      event.currentTarget.setPointerCapture(event.pointerId);
      setIsDragging(true);
    },
    [splitEnabled],
  );

  useEffect(() => {
    if (!isDragging) {
      return;
    }

    function handlePointerMove(event: PointerEvent) {
      const layout = layoutRef.current;

      if (!layout) {
        return;
      }

      const rect = layout.getBoundingClientRect();
      applyWidth(rect.right - event.clientX);
    }

    function handlePointerUp() {
      setIsDragging(false);
      persistWidth();
    }

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    window.addEventListener("pointercancel", handlePointerUp);

    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
      window.removeEventListener("pointercancel", handlePointerUp);
    };
  }, [applyWidth, isDragging, persistWidth]);

  const layoutStyle = splitEnabled
    ? ({ "--builder-preview-width": `${paneWidth}px` } as CSSProperties)
    : undefined;

  return {
    layoutRef,
    layoutStyle,
    paneWidth,
    splitEnabled,
    isDragging,
    onSplitterPointerDown,
  };
}
