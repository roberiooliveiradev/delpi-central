import { useCallback, useEffect, useState } from "react";

import { getOpsAbertas, getOpenOrdersTotvs } from "../api/openOrdersTotvsApi";
import type { OpsAbertasData } from "../types/openOps";
import type { OpenOrdersTotvsData } from "../types/openOrdersTotvs";

type UseOpenOrdersTotvsResult = {
  data: OpenOrdersTotvsData | null;
  opsData: OpsAbertasData | null;
  opsWarning: string | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useOpenOrdersTotvs(
  sellerId?: string | null,
): UseOpenOrdersTotvsResult {
  const [data, setData] = useState<OpenOrdersTotvsData | null>(null);
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

        const pedidosPromise = getOpenOrdersTotvs(controller.signal, {
          sellerId: sellerId || null,
        });
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
  }, [reloadKey, sellerId]);

  return { data, opsData, opsWarning, loading, error, reload };
}
