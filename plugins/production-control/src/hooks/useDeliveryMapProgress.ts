import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { fetchDeliveryMapProgress } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { DeliveryMapOpProgress, DeliveryMapPayload, PpcBranch } from "../types";

const POLL_MS = 15_000;

function collectProductionOrders(payload: DeliveryMapPayload | null): string[] {
  if (!payload) return [];
  const orders = new Set<string>();
  for (const section of payload.sections) {
    for (const row of section.rows) {
      if (row.production_order) orders.add(row.production_order);
    }
  }
  return Array.from(orders);
}

export function useDeliveryMapProgress(
  branch: PpcBranch,
  payload: DeliveryMapPayload | null,
): Record<string, DeliveryMapOpProgress> {
  const [items, setItems] = useState<Record<string, DeliveryMapOpProgress>>({});
  const orders = useMemo(() => collectProductionOrders(payload), [payload]);
  const ordersKey = useMemo(() => orders.join(","), [orders]);
  const inFlightRef = useRef(false);

  const refresh = useCallback(async () => {
    if (orders.length === 0) {
      setItems({});
      return;
    }
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    try {
      const response = await fetchDeliveryMapProgress({ branch, orders });
      setItems(response.items ?? {});
    } catch {
      /* mantém último progresso conhecido */
    } finally {
      inFlightRef.current = false;
    }
  }, [branch, orders]);

  useEffect(() => {
    void refresh();
  }, [refresh, ordersKey]);

  useEffect(() => {
    if (orders.length === 0) return undefined;
    const timer = window.setInterval(() => {
      void refresh();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [orders.length, refresh, ordersKey]);

  return items;
}

export function deliveryMapProgressAriaLabel(progress: DeliveryMapOpProgress): string {
  return copy.deliveryMap.progressAria(progress);
}
