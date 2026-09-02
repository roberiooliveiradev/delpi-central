import { useEffect, useRef } from "react";

import { resolveDeviceLiveRefreshIntervalMs } from "../utils/deviceLiveRefreshInterval";

type UseDeviceLiveRefreshOptions = {
  enabled: boolean;
  pollIntervalMs: number | null | undefined;
  onTick: () => void | Promise<void>;
};

/**
 * Agenda refresh periódico alinhado ao pollIntervalMs do device (módulo canônico).
 * Evita sobreposição: se o tick anterior ainda corre, o próximo é pulado.
 */
export function useDeviceLiveRefresh({
  enabled,
  pollIntervalMs,
  onTick,
}: UseDeviceLiveRefreshOptions): void {
  const onTickRef = useRef(onTick);
  onTickRef.current = onTick;

  useEffect(() => {
    if (!enabled) return;

    const intervalMs = resolveDeviceLiveRefreshIntervalMs(pollIntervalMs);
    let cancelled = false;
    let inFlight = false;

    const run = async () => {
      if (cancelled || inFlight) return;
      inFlight = true;
      try {
        await onTickRef.current();
      } catch {
        // Falha silenciosa no tick live — erros manuais usam fluxos explícitos.
      } finally {
        inFlight = false;
      }
    };

    const timer = window.setInterval(() => {
      void run();
    }, intervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [enabled, pollIntervalMs]);
}
