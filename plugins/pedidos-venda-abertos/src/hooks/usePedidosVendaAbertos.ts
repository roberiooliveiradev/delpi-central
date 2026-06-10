import { useCallback, useEffect, useState } from "react";

import { getOpsAbertas, getPedidosVendaAbertos } from "../api/pedidosVendaAbertosApi";
import type { OpsAbertasData } from "../types/opsAbertas";
import type { PedidosVendaAbertosData } from "../types/pedidosVendaAbertos";

type UsePedidosVendaAbertosResult = {
  data: PedidosVendaAbertosData | null;
  opsData: OpsAbertasData | null;
  opsWarning: string | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function usePedidosVendaAbertos(): UsePedidosVendaAbertosResult {
  const [data, setData] = useState<PedidosVendaAbertosData | null>(null);
  const [opsData, setOpsData] = useState<OpsAbertasData | null>(null);
  const [opsWarning, setOpsWarning] = useState<string | null>(null);
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
        setOpsWarning(null);

        const pedidosPromise = getPedidosVendaAbertos(controller.signal);
        const opsPromise = getOpsAbertas(controller.signal).catch((opsError) => {
          if (controller.signal.aborted) {
            throw opsError;
          }
          const message =
            opsError instanceof Error
              ? opsError.message
              : "Não foi possível carregar OPs abertas.";
          setOpsWarning(message);
          return null;
        });

        const [pedidosResult, opsResult] = await Promise.all([pedidosPromise, opsPromise]);
        setData(pedidosResult);
        setOpsData(opsResult);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar os dados.";
        setError(message);
        setData(null);
        setOpsData(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [reloadKey]);

  return { data, opsData, opsWarning, loading, error, reload };
}
