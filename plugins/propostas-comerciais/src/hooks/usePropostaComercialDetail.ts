import { useCallback, useEffect, useState } from "react";

import { getPropostaComercial } from "../api/propostasComerciaisApi";
import type { PropostaComercialDetail } from "../types/propostasComerciais";

type UsePropostaComercialDetailResult = {
  data: PropostaComercialDetail | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function usePropostaComercialDetail(
  propostaInterna: string,
): UsePropostaComercialDetailResult {
  const [data, setData] = useState<PropostaComercialDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const code = propostaInterna.trim();

    if (!code) {
      setData(null);
      setError("Proposta inválida.");
      setLoading(false);
      return () => controller.abort();
    }

    async function run() {
      try {
        setLoading(true);
        setError(null);
        const result = await getPropostaComercial(code, controller.signal);
        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar a proposta.";
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
  }, [propostaInterna, reloadKey]);

  return { data, loading, error, reload };
}
