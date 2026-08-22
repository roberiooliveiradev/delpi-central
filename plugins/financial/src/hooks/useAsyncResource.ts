import { useCallback, useEffect, useState } from "react";

type Loader<T> = (signal: AbortSignal) => Promise<T>;

/**
 * Carregamento assíncrono com recarga manual.
 *
 * `deps` entra na lista de dependências do efeito — passe valores primitivos
 * (filial, datas, filtros), não objetos recriados a cada render.
 */
export function useAsyncResource<T>(loader: Loader<T>, deps: unknown[], fallbackError: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    loader(controller.signal)
      .then((payload) => {
        if (controller.signal.aborted) return;
        setData(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : fallbackError);
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadToken]);

  return { data, loading, error, reload };
}
