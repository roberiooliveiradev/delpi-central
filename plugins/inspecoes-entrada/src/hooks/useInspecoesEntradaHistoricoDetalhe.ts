import { useCallback, useEffect, useState } from "react";

import { fetchInspecoesEntradaHistoricoDetalhe } from "../api/inspecoesEntradaApi";
import type { InspecoesEntradaHistoricoDetalhe } from "../types/inspecoesEntradaHistoricoDetalhe";

type UseInspecoesEntradaHistoricoDetalheResult = {
  data: InspecoesEntradaHistoricoDetalhe | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useInspecoesEntradaHistoricoDetalhe(
  branch: string,
  inspectionId: string | null,
): UseInspecoesEntradaHistoricoDetalheResult {
  const [data, setData] = useState<InspecoesEntradaHistoricoDetalhe | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    if (!inspectionId) return;

    const resolvedInspectionId = inspectionId;
    const controller = new AbortController();

    async function run() {
      setLoading(true);
      setError(null);

      try {
        const result = await fetchInspecoesEntradaHistoricoDetalhe(
          { branch, inspection_id: resolvedInspectionId },
          controller.signal,
        );
        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar o detalhe da inspeção.";
        setData(null);
        setError(message);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [branch, inspectionId, reloadKey]);

  if (!inspectionId) {
    return { data: null, loading: false, error: null, reload };
  }

  return { data, loading, error, reload };
}
