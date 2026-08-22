import { useEffect, useState } from "react";

import { fetchSubplugins } from "../api/financialApi";
import { copy } from "../content/copy";
import type { Subplugin } from "../types";

export function useSubplugins() {
  const [items, setItems] = useState<Subplugin[]>([]);
  const [canExport, setCanExport] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchSubplugins(controller.signal)
      .then((payload) => {
        setItems(payload.items ?? []);
        setCanExport(Boolean(payload.capabilities?.export));
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.subpluginsError);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  return { items, canExport, loading, error };
}
