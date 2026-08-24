import { useEffect, useMemo, useState } from "react";

import {
  fetchPublicDeliveryMapProgress,
  type DeliveryMapOpProgress,
  type PublicDeliveryMapPayload,
} from "./api";
import {
  chunkDeliveryMapProgressOrders,
  collectDeliveryMapProgressOrderBatches,
  DELIVERY_MAP_PROGRESS_BATCH_SIZE,
} from "./deliveryMapProgress";

const POLL_MS = 15_000;

async function fetchProgressForOrders(
  token: string,
  branch: string,
  orders: readonly string[],
  signal: AbortSignal,
): Promise<Record<string, DeliveryMapOpProgress>> {
  const merged: Record<string, DeliveryMapOpProgress> = {};
  for (const chunk of chunkDeliveryMapProgressOrders(orders, DELIVERY_MAP_PROGRESS_BATCH_SIZE)) {
    if (signal.aborted) break;
    const items = await fetchPublicDeliveryMapProgress(token, branch, chunk);
    Object.assign(merged, items);
  }
  return merged;
}

export function usePublicDeliveryMapProgress(
  token: string,
  branch: string,
  payload: PublicDeliveryMapPayload | null,
): Record<string, DeliveryMapOpProgress> {
  const [items, setItems] = useState<Record<string, DeliveryMapOpProgress>>({});
  const batches = useMemo(() => collectDeliveryMapProgressOrderBatches(payload), [payload]);
  const batchesKey = useMemo(
    () => `${batches.priority.join(",")}|${batches.deferred.join(",")}`,
    [batches.deferred, batches.priority],
  );

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    async function loadProgress() {
      const { priority, deferred } = batches;
      if (priority.length === 0 && deferred.length === 0) {
        setItems({});
        return;
      }

      try {
        if (priority.length > 0) {
          const priorityItems = await fetchProgressForOrders(
            token,
            branch,
            priority,
            controller.signal,
          );
          if (cancelled || controller.signal.aborted) return;
          setItems((prev) => ({ ...prev, ...priorityItems }));
        }

        if (deferred.length > 0) {
          const deferredItems = await fetchProgressForOrders(
            token,
            branch,
            deferred,
            controller.signal,
          );
          if (cancelled || controller.signal.aborted) return;
          setItems((prev) => ({ ...prev, ...deferredItems }));
        }
      } catch {
        if (controller.signal.aborted) return;
      }
    }

    void loadProgress();
    const timer = window.setInterval(() => {
      void loadProgress();
    }, POLL_MS);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(timer);
    };
  }, [token, branch, batches, batchesKey]);

  return items;
}
