import { useCallback, useEffect, useState } from "react";
import { fetchPublicWorkCenterPerformance, type PublicWorkCenterPerformance } from "./api";

/** Eficiência e paradas vêm do TOTVS e mudam em minutos — a fila é que precisa de 15s. */
const PERFORMANCE_POLL_MS = 300_000;

export type WorkCenterPerformanceState = {
  data: PublicWorkCenterPerformance | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useWorkCenterPerformance(
  token: string,
  branch: string,
  workCenter: string | null,
  days?: number,
): WorkCenterPerformanceState {
  const [data, setData] = useState<PublicWorkCenterPerformance | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generation, setGeneration] = useState(0);

  const reload = useCallback(() => setGeneration((value) => value + 1), []);

  useEffect(() => {
    if (!workCenter) {
      setData(null);
      setError(null);
      return;
    }

    let active = true;
    setLoading(true);

    void fetchPublicWorkCenterPerformance(token, branch, workCenter, days)
      .then((next) => {
        if (!active) return;
        setData(next);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        // Indisponibilidade de desempenho nunca derruba a fila: só apaga os chips.
        setData(null);
        setError(err instanceof Error ? err.message : "Desempenho do posto indisponível.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [token, branch, workCenter, days, generation]);

  useEffect(() => {
    if (!workCenter) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "hidden") return;
      reload();
    }, PERFORMANCE_POLL_MS);
    return () => window.clearInterval(timer);
  }, [workCenter, reload]);

  return { data, loading, error, reload };
}
