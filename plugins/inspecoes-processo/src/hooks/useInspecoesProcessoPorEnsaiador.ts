import { useCallback, useEffect, useState } from "react";

import { getPorEnsaiador } from "../api/inspecoesProcessoApi";
import type { InspecoesProcessoPorEnsaiadorItem } from "../types/api";
import type { DashboardKpiPeriod } from "./useInspecoesProcessoResumo";

export const POR_ENSAIADOR_LIMIT = 10;

type UseInspecoesProcessoPorEnsaiadorResult = {
  items: InspecoesProcessoPorEnsaiadorItem[];
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useInspecoesProcessoPorEnsaiador(
  branch: string,
  refreshToken = 0,
  period?: DashboardKpiPeriod,
): UseInspecoesProcessoPorEnsaiadorResult {
  const [items, setItems] = useState<InspecoesProcessoPorEnsaiadorItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const startDate = period?.startDate;
  const endDate = period?.endDate;
  const enabled = period?.enabled ?? true;

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function run() {
      setLoading(true);
      setError(null);
      setItems([]);

      try {
        const ranking = await getPorEnsaiador(branch, {
          limit: POR_ENSAIADOR_LIMIT,
          start_date: startDate,
          end_date: endDate,
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setItems(Array.isArray(ranking) ? ranking.slice(0, POR_ENSAIADOR_LIMIT) : []);
        setError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItems([]);
        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar os indicadores por ensaiador.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => {
      controller.abort();
    };
  }, [branch, reloadKey, refreshToken, startDate, endDate, enabled]);

  return { items, loading, error, reload };
}
