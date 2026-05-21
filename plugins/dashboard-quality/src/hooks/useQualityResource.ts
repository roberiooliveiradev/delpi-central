import { useCallback, useEffect, useState } from "react";

import { formatQualityApiError } from "../utils/formatQualityApiError";
import {
  beginSingleRequestProgress,
  EMPTY_REQUEST_PROGRESS,
  finishSingleRequestProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

type UseQualityResourceOptions = {
  enabled?: boolean;
  /** TTL do cache em ms (stale-while-revalidate). */
  cacheTtlMs?: number;
  /** Chave estável; omitir desativa cache. */
  cacheKey?: string;
};

type CacheEntry<T> = {
  data: T;
  fetchedAt: number;
};

const resourceCache = new Map<string, CacheEntry<unknown>>();

const DEFAULT_CACHE_TTL_MS = 30_000;

type UseQualityResourceResult<T> = {
  data: T | null;
  loading: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  reload: () => void;
};

export function useQualityResource<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[],
  options: UseQualityResourceOptions = {}
): UseQualityResourceResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(options.enabled !== false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );
  const enabled = options.enabled !== false;
  const cacheKey = options.cacheKey;
  const cacheTtlMs = options.cacheTtlMs ?? DEFAULT_CACHE_TTL_MS;

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const cached = cacheKey
      ? (resourceCache.get(cacheKey) as CacheEntry<T> | undefined)
      : undefined;
    const cacheAge = cached ? Date.now() - cached.fetchedAt : Number.POSITIVE_INFINITY;
    const isCacheFresh = Boolean(cached && cacheAge < cacheTtlMs);

    if (cached) {
      setData(cached.data);
    }

    async function run() {
      try {
        setError(null);

        if (!cached) {
          setLoading(true);
        } else if (!isCacheFresh) {
          setLoading(true);
        }

        beginSingleRequestProgress(setRequestProgress);
        const result = await fetcher(controller.signal);

        if (cacheKey) {
          resourceCache.set(cacheKey, {
            data: result,
            fetchedAt: Date.now(),
          });
        }

        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;

        if (!cached) {
          const message = formatQualityApiError(err);
          if (message) {
            setError(message);
          }
        }
      } finally {
        if (!controller.signal.aborted) {
          finishSingleRequestProgress(setRequestProgress, false);
          setLoading(false);
        }
      }
    }

    if (isCacheFresh) {
      setLoading(false);
      return () => controller.abort();
    }

    void run();

    return () => controller.abort();
    // fetcher é estável via deps primitivos passados pelo caller
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, reloadKey, cacheKey, cacheTtlMs, ...deps]);

  const reload = useCallback(() => {
    if (cacheKey) {
      resourceCache.delete(cacheKey);
    }
    setReloadKey((prev) => prev + 1);
  }, [cacheKey]);

  return { data, loading, requestProgress, error, reload };
}
