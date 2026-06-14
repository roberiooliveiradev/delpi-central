import { useCallback, useEffect, useState } from "react";

import { listPropostasComerciais } from "../api/propostasComerciaisApi";
import type { PropostaComercialListData } from "../types/propostasComerciais";

type UsePropostasComerciaisListResult = {
  data: PropostaComercialListData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function usePropostasComerciaisList(limit = 100): UsePropostasComerciaisListResult {
  const [data, setData] = useState<PropostaComercialListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      try {
        setLoading(true);
        setError(null);
        const result = await listPropostasComerciais(limit, controller.signal);
        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar as propostas.";
        setError(message);
        setData(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [limit, reloadKey]);

  return { data, loading, error, reload };
}
