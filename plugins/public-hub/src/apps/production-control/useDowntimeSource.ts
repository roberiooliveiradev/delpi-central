import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchDowntimeSource, type WorkCenterDowntimeSource } from "./api";

export type DowntimeSourceError = {
  message: string;
  retryable: boolean;
};

type SourceResult = {
  /** Escopo (token|filial|CT) que produziu este resultado. */
  key: string;
  resolution: WorkCenterDowntimeSource | null;
  error: DowntimeSourceError | null;
};

/**
 * Fonte oficial de paradas do posto (Etapa 1) — resolvida pelo backend,
 * consulta pública sem sessão. Resultado chaveado por escopo: resposta de
 * outro CT nunca decide a fonte do posto atual. unavailable é resposta
 * válida — nunca cai para TOTVS.
 */
export function useDowntimeSource(
  token: string,
  branch: string,
  workCenter: string | null,
): {
  source: WorkCenterDowntimeSource["source"] | null;
  resolution: WorkCenterDowntimeSource | null;
  loading: boolean;
  error: DowntimeSourceError | null;
  reload: () => void;
} {
  const currentKey = `${token}|${branch}|${workCenter}`;
  const [result, setResult] = useState<SourceResult | null>(null);
  const inFlightRef = useRef(false);
  const pendingRef = useRef(false);
  const requestRef = useRef({ token, branch, workCenter });

  useEffect(() => {
    requestRef.current = { token, branch, workCenter };
  }, [token, branch, workCenter]);

  const reload = useCallback(async () => {
    if (inFlightRef.current) {
      pendingRef.current = true;
      return;
    }
    inFlightRef.current = true;
    try {
      do {
        pendingRef.current = false;
        const request = requestRef.current;
        const key = `${request.token}|${request.branch}|${request.workCenter}`;
        if (!request.workCenter) continue;
        try {
          const resolution = await fetchDowntimeSource(
            request.token,
            request.branch,
            request.workCenter,
          );
          setResult({ key, resolution, error: null });
        } catch (err) {
          setResult((prev) => ({
            key,
            // refetch falhou: preserva a última resolução do mesmo escopo.
            resolution: prev?.key === key ? prev.resolution : null,
            error: {
              message:
                err instanceof Error
                  ? err.message
                  : "Fonte de paradas do posto indisponível.",
              retryable: true,
            },
          }));
        }
      } while (pendingRef.current);
    } finally {
      inFlightRef.current = false;
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, workCenter, branch]);

  const scoped = result?.key === currentKey ? result : null;
  const resolution = scoped?.resolution ?? null;
  const error = scoped?.error ?? null;
  const loading = Boolean(workCenter && !scoped);

  return useMemo(
    () => ({
      source: resolution?.source ?? null,
      resolution,
      loading,
      error,
      reload: () => void reload(),
    }),
    [resolution, loading, error, reload],
  );
}
