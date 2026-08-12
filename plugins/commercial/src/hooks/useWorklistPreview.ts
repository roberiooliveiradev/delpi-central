import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getMyWorklist, type CommercialTaskDto, type WorklistData } from "../api/worklistApi";
import { useCommercialWorklistSync } from "../app/CommercialRealtimeProvider";

export type WorklistPreviewBucket = "overdue" | "today" | "later";

export type WorklistPreviewItem = {
  task: CommercialTaskDto;
  bucket: WorklistPreviewBucket;
};

export type WorklistPreviewCounts = {
  overdue: number;
  today: number;
  later: number;
  open: number;
};

export type WorklistPreview = {
  counts: WorklistPreviewCounts;
  items: WorklistPreviewItem[];
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export const WORKLIST_PREVIEW_LIMIT = 5;

const EMPTY_COUNTS: WorklistPreviewCounts = { overdue: 0, today: 0, later: 0, open: 0 };
const LOAD_ERROR = "Não foi possível carregar suas tarefas.";

/**
 * Prévia única da worklist (uma chamada por sessão de tela) para consumidores que
 * só precisam de contagens e das primeiras tarefas — Início hoje, chrome depois.
 * Ordem: atrasadas → hoje → depois.
 */
export function useWorklistPreview(options?: {
  enabled?: boolean;
  limit?: number;
}): WorklistPreview {
  const enabled = options?.enabled ?? true;
  const limit = options?.limit ?? WORKLIST_PREVIEW_LIMIT;
  const [data, setData] = useState<WorklistData | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);

  const reload = useCallback(() => {
    requestRef.current?.abort();
    if (!enabled) {
      requestRef.current = null;
      setData(null);
      setError(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    void getMyWorklist({ signal: controller.signal })
      .then((worklist) => {
        if (controller.signal.aborted) return;
        setData(worklist);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(err instanceof Error ? err.message : LOAD_ERROR);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, [enabled]);

  useEffect(() => {
    reload();
    return () => requestRef.current?.abort();
  }, [reload]);

  useCommercialWorklistSync(reload, enabled);

  const counts = useMemo<WorklistPreviewCounts>(() => {
    if (!data) return EMPTY_COUNTS;
    return {
      overdue: data.counts?.overdue ?? 0,
      today: data.counts?.today ?? 0,
      later: data.counts?.later ?? 0,
      open: data.counts?.open ?? 0,
    };
  }, [data]);

  const items = useMemo<WorklistPreviewItem[]>(() => {
    if (!data) return [];
    const buckets: Array<[WorklistPreviewBucket, CommercialTaskDto[]]> = [
      ["overdue", data.overdue ?? []],
      ["today", data.today ?? []],
      ["later", data.later ?? []],
    ];
    const ordered: WorklistPreviewItem[] = [];
    for (const [bucket, tasks] of buckets) {
      for (const task of tasks) {
        if (ordered.length >= limit) return ordered;
        ordered.push({ task, bucket });
      }
    }
    return ordered;
  }, [data, limit]);

  return { counts, items, loading, error, reload };
}
