import { useEffect, useState } from "react";

import { fetchSubplugins } from "../api/ppcApi";
import type { Subplugin } from "../types";

export function useSubplugins() {
  const [items, setItems] = useState<Subplugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchSubplugins(controller.signal)
      .then((list) => {
        setItems(list);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar subplugins.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  return { items, loading, error };
}
