import { useCallback, useEffect, useState } from "react";

import { listDowntimeReasons, type DowntimeReason } from "../api/downtimeReasonsApi";

type State = {
  items: DowntimeReason[];
  loading: boolean;
  error: string | null;
};

export function useDowntimeReasons() {
  const [state, setState] = useState<State>({ items: [], loading: true, error: null });

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const data = await listDowntimeReasons(signal);
      if (signal?.aborted) return;
      setState({ items: data.items, loading: false, error: null });
    } catch (error) {
      if (signal?.aborted) return;
      setState((prev) => ({
        items: prev.items,
        loading: false,
        error: error instanceof Error ? error.message : "Falha ao carregar motivos de parada.",
      }));
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setState((prev) => ({ ...prev, loading: true, error: null }));
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const reload = useCallback(() => load(), [load]);

  const upsert = useCallback((reason: DowntimeReason) => {
    setState((prev) => ({
      ...prev,
      items: prev.items.some((item) => item.code === reason.code)
        ? prev.items.map((item) => (item.code === reason.code ? reason : item))
        : [...prev.items, reason],
    }));
  }, []);

  return { ...state, reload, upsert };
}
