import { useCallback, useEffect, useState } from "react";

import { formatCommercialApiError } from "../utils/formatCommercialApiError";

type UseCommercialResourceOptions = {
  enabled?: boolean;
  cacheTtlMs?: number;
  cacheKey?: string;
};

type CacheEntry<T> = {
  data: T;
  fetchedAt: number;
};

const resourceCache = new Map<string, CacheEntry<unknown>>();
const DEFAULT_CACHE_TTL_MS = 60_000;

type UseCommercialResourceResult<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useCommercialResource<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[],
  options: UseCommercialResourceOptions = {}
): UseCommercialResourceResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(options.enabled !== false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
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

        if (!cached || !isCacheFresh) {
          setLoading(true);
        }

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
          const message = formatCommercialApiError(err);
          if (message) {
            setError(message);
          }
        }
      } finally {
        if (!controller.signal.aborted) {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, reloadKey, cacheKey, cacheTtlMs, ...deps]);

  const reload = useCallback(() => {
    if (cacheKey) {
      resourceCache.delete(cacheKey);
    }
    setReloadKey((prev) => prev + 1);
  }, [cacheKey]);

  return { data, loading, error, reload };
}
