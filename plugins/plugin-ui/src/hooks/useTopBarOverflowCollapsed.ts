import { useLayoutEffect, useState, type RefObject } from "react";

/** Folga (px) exigida para reexpandir após colapso — evita oscilação RO ↔ setState. */
export const TOPBAR_OVERFLOW_EXPAND_HYSTERESIS_PX = 24;

export type UseTopBarOverflowCollapsedOptions = {
  enabled: boolean;
  /** Extra px before collapsing (default 2). */
  tolerancePx?: number;
  /** Folga para reexpandir (default `TOPBAR_OVERFLOW_EXPAND_HYSTERESIS_PX`). */
  expandHysteresisPx?: number;
};

/**
 * Collapses when the measure row needs more width than the TopBar host.
 * Used for responsive hamburger mode (no manual toggle / localStorage).
 *
 * Reexpand só com folga ≥ hysteresis — evita React #185 ao redimensionar
 * a sidebar do portal (colapsar ↔ medir ↔ expandir na fronteira).
 */
export function useTopBarOverflowCollapsed(
  measureRef: RefObject<HTMLElement | null>,
  options: UseTopBarOverflowCollapsedOptions,
) {
  const {
    enabled,
    tolerancePx = 2,
    expandHysteresisPx = TOPBAR_OVERFLOW_EXPAND_HYSTERESIS_PX,
  } = options;
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
      setCollapsed((prev) => {
        if (needed > available + tolerancePx) return true;
        if (prev && needed > available - expandHysteresisPx) return true;
        return false;
      });
    };

    check();

    const ro = new ResizeObserver(check);
    ro.observe(measureEl);
    const host = measureEl.parentElement;
    if (host) ro.observe(host);

    return () => ro.disconnect();
  }, [enabled, measureRef, tolerancePx, expandHysteresisPx]);

  return { collapsed };
}

export type UseTopBarOverflowCollapsedResult = ReturnType<typeof useTopBarOverflowCollapsed>;
