import { useCallback, useEffect, useState } from "react";

import { getPedidosVendaAbertos } from "../api/pedidosVendaAbertosApi";
import type { PedidosVendaAbertosData } from "../types/pedidosVendaAbertos";

type UsePedidosVendaAbertosResult = {
  data: PedidosVendaAbertosData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function usePedidosVendaAbertos(): UsePedidosVendaAbertosResult {
  const [data, setData] = useState<PedidosVendaAbertosData | null>(null);
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
        const result = await getPedidosVendaAbertos(controller.signal);
        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Não foi possível carregar os dados.";
        setError(message);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [reloadKey]);

  return { data, loading, error, reload };
}
