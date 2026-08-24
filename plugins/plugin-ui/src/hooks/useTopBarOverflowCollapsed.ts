import { useLayoutEffect, useState, type RefObject } from "react";

export type UseTopBarOverflowCollapsedOptions = {
  enabled: boolean;
  /** Extra px before collapsing (default 2). */
  tolerancePx?: number;
};

/**
 * Collapses when the measure row needs more width than the TopBar host.
 * Used for responsive hamburger mode (no manual toggle / localStorage).
 */
export function useTopBarOverflowCollapsed(
  measureRef: RefObject<HTMLElement | null>,
  options: UseTopBarOverflowCollapsedOptions,
) {
  const { enabled, tolerancePx = 2 } = options;
  const [collapsed, setCollapsed] = useState(false);

  useLayoutEffect(() => {
    if (!enabled) {
      setCollapsed(false);
      return;
    }

    const measureEl = measureRef.current;
    if (!measureEl) return;

    const check = () => {
      const host = measureEl.parentElement;
      if (!host) return;
      const available = host.clientWidth;
      const needed = measureEl.scrollWidth;
      setCollapsed(needed > available + tolerancePx);
    };

    check();

    const ro = new ResizeObserver(check);
    ro.observe(measureEl);
    const host = measureEl.parentElement;
    if (host) ro.observe(host);

    return () => ro.disconnect();
  }, [enabled, measureRef, tolerancePx]);

  return { collapsed };
}

export type UseTopBarOverflowCollapsedResult = ReturnType<typeof useTopBarOverflowCollapsed>;
