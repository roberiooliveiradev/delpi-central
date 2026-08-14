import { useEffect, useState } from "react";

import { getRecentlyClosedOrdersTotvs } from "../api/openOrdersTotvsApi";
import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";

type Options = {
  /** When false, skip fetch (e.g. table/cards layout). */
  enabled?: boolean;
  sellerId?: string | null;
  days?: number;
};

type Result = {
  items: OpenOrdersTotvsItem[];
  loading: boolean;
  error: string | null;
};

/**
 * Recently closed order lines for Kanban completed column (BFF only).
 */
export function useRecentlyClosedOrdersTotvs({
  enabled = true,
  sellerId = null,
  days = 30,
}: Options = {}): Result {
  const [items, setItems] = useState<OpenOrdersTotvsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setItems([]);
      setLoading(false);
      setError(null);
      return;
    }

    const controller = new AbortController();

    async function run() {
      try {
        setLoading(true);
        setError(null);
        const data = await getRecentlyClosedOrdersTotvs(controller.signal, {
          days,
          sellerId,
        });
        if (controller.signal.aborted) return;
        setItems(Array.isArray(data.items) ? data.items : []);
      } catch (err) {
        if (controller.signal.aborted) return;
        setItems([]);
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar pedidos concluídos.",
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [enabled, sellerId, days]);

  return { items, loading, error };
}
