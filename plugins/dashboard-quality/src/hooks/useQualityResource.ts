import { useCallback, useEffect, useState } from "react";

type UseQualityResourceOptions = {
  enabled?: boolean;
};

type UseQualityResourceResult<T> = {
  data: T | null;
  loading: boolean;
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
  const enabled = options.enabled !== false;

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function run() {
      try {
        setError(null);
        setLoading(true);

        const result = await fetcher(controller.signal);
        setData(result);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error ? err.message : "Erro ao carregar dados de qualidade"
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => controller.abort();
    // fetcher é estável via deps primitivos passados pelo caller
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, reloadKey, ...deps]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return { data, loading, error, reload };
}
