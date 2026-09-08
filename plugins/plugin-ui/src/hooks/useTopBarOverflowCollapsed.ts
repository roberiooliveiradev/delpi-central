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
 * Largura intrínseca da row (`max-content`), não do wrapper `width: 100%`.
 *
 * Contrato CSS (obrigatório): `.delpi-ui-topbar__row--measure` sem
 * `min-width: 100%` — senão needed ≥ available sempre que cabe e a
 * histerese trava o hamburger. Ver `topBarMeasureRow.structural.test.mjs`.
 */
export function resolveTopBarMeasureNeededWidth(measureEl: HTMLElement): number {
  const content =
    measureEl.querySelector<HTMLElement>(".delpi-ui-topbar__row--measure") ??
    (measureEl.firstElementChild instanceof HTMLElement
      ? measureEl.firstElementChild
      : null);
  if (content) {
    return Math.max(content.scrollWidth, content.offsetWidth);
  }
  return measureEl.scrollWidth;
}

export function shouldKeepTopBarOverflowCollapsed(options: {
  needed: number;
  available: number;
  previouslyCollapsed: boolean;
  tolerancePx?: number;
  expandHysteresisPx?: number;
}): boolean {
  const {
    needed,
    available,
    previouslyCollapsed,
    tolerancePx = 2,
    expandHysteresisPx = TOPBAR_OVERFLOW_EXPAND_HYSTERESIS_PX,
  } = options;
  if (needed > available + tolerancePx) return true;
  if (previouslyCollapsed && needed > available - expandHysteresisPx) {
    return true;
  }
  return false;
}

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
      const needed = resolveTopBarMeasureNeededWidth(measureEl);
      setCollapsed((prev) =>
        shouldKeepTopBarOverflowCollapsed({
          needed,
          available,
          previouslyCollapsed: prev,
          tolerancePx,
          expandHysteresisPx,
        }),
      );
    };

    check();

    const ro = new ResizeObserver(check);
    ro.observe(measureEl);
    const content = measureEl.firstElementChild;
    if (content instanceof Element) ro.observe(content);
    const host = measureEl.parentElement;
    if (host) ro.observe(host);

    return () => ro.disconnect();
  }, [enabled, measureRef, tolerancePx, expandHysteresisPx]);

  return { collapsed };
}

export type UseTopBarOverflowCollapsedResult = ReturnType<typeof useTopBarOverflowCollapsed>;
