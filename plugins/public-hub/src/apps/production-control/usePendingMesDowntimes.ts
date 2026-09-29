import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchPendingMesDowntimes,
  isAuthError,
  type PendingMesDowntime,
} from "./api";

type Options = {
  token: string;
  sessionToken: string | null;
  branch: string;
  workCenter: string | null;
  /** Sinal de reconciliação — muda a cada evento de lifecycle no WS. */
  refreshSignal?: number;
};

/**
 * Paradas encerradas do posto ainda sem motivo (inclui runs finalizados).
 * Requer sessão de bancada; refetch é por sinal explícito, sem polling.
 */
export function usePendingMesDowntimes({
  token,
  sessionToken,
  branch,
  workCenter,
  refreshSignal = 0,
}: Options) {
  const [items, setItems] = useState<PendingMesDowntime[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);
  const requestRef = useRef({ token, sessionToken, branch, workCenter });

  useEffect(() => {
    requestRef.current = { token, sessionToken, branch, workCenter };
  }, [token, sessionToken, branch, workCenter]);

  const refresh = useCallback(async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    try {
      const request = requestRef.current;
      if (!request.sessionToken || !request.workCenter) {
        setItems(null);
        return;
      }
      try {
        const next = await fetchPendingMesDowntimes(
          request.token,
          request.sessionToken,
          request.branch,
          request.workCenter,
        );
        setItems(next);
        setError(null);
      } catch (err) {
        if (isAuthError(err)) {
          setItems(null);
          setError(null);
          return;
        }
        setError(err instanceof Error ? err.message : "Paradas sem motivo indisponíveis.");
      }
    } finally {
      inFlightRef.current = false;
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh, sessionToken, workCenter, refreshSignal]);

  return { items, error, refresh };
}
