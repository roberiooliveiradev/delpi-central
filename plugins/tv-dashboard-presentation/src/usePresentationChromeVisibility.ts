import { useCallback, useEffect, useRef, useState } from "react";

/** Tempo sem atividade até ocultar badge/controles (prévia e apresentação). */
export const PRESENTATION_CHROME_HIDE_MS = 3500;

type Options = {
  enabled?: boolean;
  hideAfterMs?: number;
};

/**
 * Mostra o chrome da apresentação e agenda ocultar após inatividade.
 * Reaparece com ponteiro, toque ou teclado.
 */
export function usePresentationChromeVisibility({
  enabled = true,
  hideAfterMs = PRESENTATION_CHROME_HIDE_MS,
}: Options = {}) {
  const [visible, setVisible] = useState(true);
  const timerRef = useRef<number | null>(null);
  const visibleRef = useRef(true);

  const clearHideTimer = useCallback(() => {
    if (timerRef.current != null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const bump = useCallback(() => {
    if (!enabled) return;
    if (!visibleRef.current) {
      visibleRef.current = true;
      setVisible(true);
    }
    clearHideTimer();
    timerRef.current = window.setTimeout(() => {
      visibleRef.current = false;
      setVisible(false);
      timerRef.current = null;
    }, hideAfterMs);
  }, [clearHideTimer, enabled, hideAfterMs]);

  useEffect(() => {
    if (!enabled) {
      clearHideTimer();
      visibleRef.current = true;
      setVisible(true);
      return;
    }

    bump();

    const onActivity = () => bump();
    const opts: AddEventListenerOptions = { passive: true };
    window.addEventListener("pointermove", onActivity, opts);
    window.addEventListener("pointerdown", onActivity, opts);
    window.addEventListener("touchstart", onActivity, opts);
    window.addEventListener("keydown", onActivity, opts);
    window.addEventListener("mousemove", onActivity, opts);

    return () => {
      clearHideTimer();
      window.removeEventListener("pointermove", onActivity);
      window.removeEventListener("pointerdown", onActivity);
      window.removeEventListener("touchstart", onActivity);
      window.removeEventListener("keydown", onActivity);
      window.removeEventListener("mousemove", onActivity);
    };
  }, [bump, clearHideTimer, enabled]);

  return { visible, bump };
}
