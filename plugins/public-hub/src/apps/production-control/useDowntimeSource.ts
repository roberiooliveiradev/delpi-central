import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchDowntimeSource, type WorkCenterDowntimeSource } from "./api";

/** Cadência de revalidação — mesma régua do watch diário do posto. */
const SOURCE_WATCH_MS = 30_000;
/**
 * Janela máxima em que a última resolução sobrevive a refetches falhos.
 * Depois dela a fonte antiga não é mais exibida como válida: a superfície
 * mostra indisponibilidade real com retry — nunca dados de outra fonte.
 */
const SOURCE_STALE_MS = 5 * 60_000;

export type DowntimeSourceError = {
  message: string;
  retryable: boolean;
};

type SourceResult = {
  /** Escopo (token|filial|CT) que produziu este resultado. */
  key: string;
  resolution: WorkCenterDowntimeSource | null;
  /** Marca da última resolução bem-sucedida — limita a preservação em erro. */
  resolvedAt: number;
  error: DowntimeSourceError | null;
};

/**
 * Fonte oficial de paradas do posto (Etapa 1) — resolvida pelo backend,
 * consulta pública sem sessão. Resultado chaveado por escopo: resposta de
 * outro CT nunca decide a fonte do posto atual. unavailable é resposta
 * válida — nunca cai para TOTVS.
 *
 * Revalidação (Etapa 4 rework): tablet aberto por horas percebe vínculo
 * novo/removido via watch de 30s (só com aba visível), retorno de aba e
 * reconexão do WS — o vínculo do sensor não emite evento próprio. Falha
 * de refetch preserva a última resolução apenas dentro de SOURCE_STALE_MS;
 * além da janela a fonte antiga deixa de valer e a tela mostra o erro.
 */
export function useDowntimeSource(
  token: string,
  branch: string,
  workCenter: string | null,
  realtimeConnected = false,
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
          setResult({ key, resolution, resolvedAt: Date.now(), error: null });
        } catch (err) {
          setResult((prev) => {
            const prior =
              prev?.key === key && prev.resolution !== null ? prev : null;
            // Refetch falhou: preserva a última resolução do mesmo escopo só
            // dentro da janela de frescor — fora dela a fonte antiga deixa de
            // ser válida e a superfície mostra indisponibilidade + retry.
            const fresh =
              prior !== null &&
              Date.now() - prior.resolvedAt <= SOURCE_STALE_MS;
            return {
              key,
              resolution: fresh ? prior.resolution : null,
              resolvedAt: prior?.resolvedAt ?? 0,
              error: {
                message:
                  err instanceof Error
                    ? err.message
                    : "Fonte de paradas do posto indisponível.",
                retryable: true,
              },
            };
          });
        }
      } while (pendingRef.current);
    } finally {
      inFlightRef.current = false;
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, workCenter, branch]);

  // Watch periódico + retorno de aba: a troca de vínculo do sensor não emite
  // evento — sem isso um CT que virou MES continuaria exibindo TOTVS até a
  // página ser aberta de novo.
  useEffect(() => {
    const tick = () => {
      if (document.visibilityState === "hidden") return;
      void reload();
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") void reload();
    };
    const timer = window.setInterval(tick, SOURCE_WATCH_MS);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [reload]);

  // Reconexão do WS: o tablet pode ter ficado offline — revalida a fonte.
  const wasConnectedRef = useRef(realtimeConnected);
  useEffect(() => {
    const was = wasConnectedRef.current;
    wasConnectedRef.current = realtimeConnected;
    if (!was && realtimeConnected) void reload();
  }, [realtimeConnected, reload]);

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
