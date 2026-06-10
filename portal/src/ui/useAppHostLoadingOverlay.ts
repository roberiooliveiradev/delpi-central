import { useEffect, useRef, useState } from "react";

const SHOW_DELAY_MS = 180;
const MIN_VISIBLE_MS = 450;
const FADE_OUT_MS = 340;

type Options = {
  /** Chave que reinicia o ciclo (troca de app, entry, reload). */
  resetKey: string;
  /** Conteúdo do app pronto para exibir. */
  ready: boolean;
};

export function useAppHostLoadingOverlay({ resetKey, ready }: Options) {
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);

  const visibleRef = useRef(false);
  const showStartedAtRef = useRef<number | null>(null);
  const showDelayTimerRef = useRef<number | null>(null);
  const hideTimerRef = useRef<number | null>(null);
  const fadeTimerRef = useRef<number | null>(null);

  const clearTimers = () => {
    if (showDelayTimerRef.current != null) {
      window.clearTimeout(showDelayTimerRef.current);
      showDelayTimerRef.current = null;
    }
    if (hideTimerRef.current != null) {
      window.clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
    if (fadeTimerRef.current != null) {
      window.clearTimeout(fadeTimerRef.current);
      fadeTimerRef.current = null;
    }
  };

  useEffect(() => {
    clearTimers();
    setVisible(false);
    setExiting(false);
    visibleRef.current = false;
    showStartedAtRef.current = null;
  }, [resetKey]);

  useEffect(() => {
    clearTimers();

    if (ready) {
      if (!visibleRef.current) {
        return;
      }

      const elapsed =
        showStartedAtRef.current != null
          ? Date.now() - showStartedAtRef.current
          : MIN_VISIBLE_MS;
      const waitMs = Math.max(0, MIN_VISIBLE_MS - elapsed);

      hideTimerRef.current = window.setTimeout(() => {
        setExiting(true);
        fadeTimerRef.current = window.setTimeout(() => {
          setVisible(false);
          setExiting(false);
          visibleRef.current = false;
          showStartedAtRef.current = null;
        }, FADE_OUT_MS);
      }, waitMs);

      return clearTimers;
    }

    showDelayTimerRef.current = window.setTimeout(() => {
      setVisible(true);
      setExiting(false);
      visibleRef.current = true;
      showStartedAtRef.current = Date.now();
    }, SHOW_DELAY_MS);

    return clearTimers;
  }, [ready, resetKey]);

  return {
    visible,
    exiting,
    fadeOutMs: FADE_OUT_MS,
  };
}
