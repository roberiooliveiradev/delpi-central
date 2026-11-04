import { useCallback, useEffect, useState } from "react";

import {
  fetchLatestMyWegNeedBatch,
  fetchMyWegNeedBatch,
  fetchMyWegNeedBatchItems,
  fetchMyWegNeedBatches,
} from "../api/ppcApi";
import { httpErrorStatus } from "../api/httpClient";
import { copy } from "../content/copy";
import type {
  MyWegNeedsBatchListPayload,
  MyWegNeedsBatchSummary,
  MyWegNeedsItemsPayload,
  PpcBranch,
} from "../types";

export type MyWegNeedsFilters = {
  batchId: string | null;
  search: string;
  remessaFrom: string | null;
  remessaTo: string | null;
  page: number;
  pageSize: number;
};

export function useMyWegNeeds(branch: PpcBranch, filters: MyWegNeedsFilters) {
  const [latest, setLatest] = useState<MyWegNeedsBatchSummary | null>(null);
  const [selected, setSelected] = useState<MyWegNeedsBatchSummary | null>(null);
  const [history, setHistory] = useState<MyWegNeedsBatchListPayload | null>(null);
  const [items, setItems] = useState<MyWegNeedsItemsPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    if (branch !== "02") {
      setLatest(null);
      setSelected(null);
      setHistory(null);
      setItems(null);
      setError(null);
      setStatus(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setStatus(null);

    void (async () => {
      try {
        const [latestBatch, historyPayload] = await Promise.all([
          fetchLatestMyWegNeedBatch({ signal: controller.signal }).catch((err) => {
            const code = httpErrorStatus(err);
            if (code === 404) return null;
            throw err;
          }),
          fetchMyWegNeedBatches({ page: 1, pageSize: 50, signal: controller.signal }),
        ]);
        if (controller.signal.aborted) return;

        setLatest(latestBatch);
        setHistory(historyPayload);

        const preferredId = filters.batchId || latestBatch?.id || null;
        if (!preferredId) {
          setSelected(null);
          setItems(null);
          return;
        }

        const batchDetail =
          preferredId === latestBatch?.id && latestBatch
            ? latestBatch
            : await fetchMyWegNeedBatch({
                batchId: preferredId,
                signal: controller.signal,
              });
        if (controller.signal.aborted) return;
        setSelected(batchDetail);

        const itemsPayload = await fetchMyWegNeedBatchItems({
          batchId: preferredId,
          search: filters.search,
          remessaFrom: filters.remessaFrom,
          remessaTo: filters.remessaTo,
          page: filters.page,
          pageSize: filters.pageSize,
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        setItems(itemsPayload);
      } catch (err) {
        if (controller.signal.aborted) return;
        setStatus(httpErrorStatus(err));
        setError(
          err instanceof Error ? err.message : copy.mywegNeeds.loadError,
        );
        setSelected(null);
        setItems(null);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();

    return () => controller.abort();
  }, [
    branch,
    filters.batchId,
    filters.page,
    filters.pageSize,
    filters.remessaFrom,
    filters.remessaTo,
    filters.search,
    reloadToken,
  ]);

  return {
    latest,
    selected,
    history,
    items,
    loading: loading && selected === null && items === null,
    refreshing: loading && (selected !== null || items !== null),
    error,
    status,
    reload,
  };
}
