import { useEffect, useRef } from "react";

type Options = {
  enabled?: boolean;
  immediate?: boolean;
};

/** Polling enquanto a aba do navegador está visível. */
export function usePolling(
  callback: () => void | Promise<void>,
  intervalMs: number,
  options: Options = {},
) {
  const { enabled = true, immediate = false } = options;
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return undefined;

    const tick = () => {
      if (document.visibilityState !== "visible") return;
      void callbackRef.current();
    };

    if (immediate) {
      tick();
    }

    const intervalId = window.setInterval(tick, intervalMs);
    document.addEventListener("visibilitychange", tick);

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [enabled, immediate, intervalMs]);
}
