import { useCallback, useEffect, useState } from "react";

import { fetchOpPendencies } from "../api/ppcApi";
import type { OpPendencyPayload, PpcBranch } from "../types";

/** Consulta separada do OTD: uma falha MyWEG não derruba a Gestão à Vista. */
export function useOpPendencies(branch: PpcBranch) {
  const [data, setData] = useState<OpPendencyPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  const reload = useCallback(() => setRefreshToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setData(null);
    setError(null);
    fetchOpPendencies({ branch, refresh: refreshToken > 0, signal: controller.signal })
      .then((payload) => {
        if (controller.signal.aborted) return;
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Pendências indisponíveis.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, refreshToken]);

  return { data, loading, error, reload };
}
