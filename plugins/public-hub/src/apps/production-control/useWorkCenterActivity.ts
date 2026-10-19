import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchMesWorkCenterToday,
  isAuthError,
  type MesWorkCenterToday,
} from "./api";
import { spCivilDayKey } from "./workCenterActivity";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";

/** Razões que alteram a visão diária — pieces_updated fora, como no run. */
const ACTIVITY_REASONS = new Set([
  "run_started",
  "run_paused",
  "run_resumed",
  "run_stopped",
  "downtime_classified",
  "automatic_downtime_started",
  "automatic_downtime_ended",
]);

const DAY_WATCH_MS = 30_000;

type Options = {
  token: string;
  sessionToken: string | null;
  branch: string;
  workCenter: string | null;
  runRealtimeEvent?: MachineLoadRealtimeEvent | null;
  realtimeConnected?: boolean;
  /** 401 → o provider descarta a sessão local (mesmo mecanismo do run). */
  onAuthError?: (err: unknown) => void;
};

export type WorkCenterActivityError = {
  message: string;
  /** true quando a fonte falhou (503/unavailable) — permite nova tentativa. */
  retryable: boolean;
};

type ActivityResult = {
  /** Escopo (token|sessão|filial|CT) que produziu este resultado. */
  key: string;
  data: MesWorkCenterToday | null;
  error: WorkCenterActivityError | null;
};

function scopeKey(
  token: string,
  sessionToken: string | null,
  branch: string,
  workCenter: string | null,
): string {
  return `${token}|${sessionToken}|${branch}|${workCenter}`;
}

/**
 * Histórico diário MES do posto — leitura escopada por (branch, workCenter)
 * e sessão de bancada. Single-flight com reconciliação coalescida por WS;
 * o resultado é chaveado pelo escopo que o gerou — resposta de outro
 * CT/sessão nunca é exibida como atual.
 */
export function useWorkCenterActivity({
  token,
  sessionToken,
  branch,
  workCenter,
  runRealtimeEvent = null,
  realtimeConnected = false,
  onAuthError,
}: Options) {
  const currentKey = scopeKey(token, sessionToken, branch, workCenter);
  const [result, setResult] = useState<ActivityResult | null>(null);
  const inFlightRef = useRef(false);
  const pendingRef = useRef(false);
  const onAuthErrorRef = useRef(onAuthError);
  const requestRef = useRef({ token, sessionToken, branch, workCenter });
  // Virada do dia civil SP: a janela do backend muda — precisa de novo GET.
  const dayKeyRef = useRef(spCivilDayKey());

  useEffect(() => {
    onAuthErrorRef.current = onAuthError;
  }, [onAuthError]);

  useEffect(() => {
    requestRef.current = { token, sessionToken, branch, workCenter };
  }, [token, sessionToken, branch, workCenter]);

  const refresh = useCallback(async () => {
    if (inFlightRef.current) {
      pendingRef.current = true;
      return;
    }
    inFlightRef.current = true;
    try {
      do {
        pendingRef.current = false;
        const request = requestRef.current;
        const key = scopeKey(
          request.token,
          request.sessionToken,
          request.branch,
          request.workCenter,
        );
        if (!request.sessionToken || !request.workCenter) {
          continue;
        }
        try {
          const next = await fetchMesWorkCenterToday(
            request.token,
            request.sessionToken,
            request.branch,
            request.workCenter,
          );
          setResult({ key, data: next, error: null });
        } catch (err) {
          if (isAuthError(err)) {
            // 401: dados protegidos somem e a sessão local é invalidada.
            setResult({ key, data: null, error: null });
            onAuthErrorRef.current?.(err);
          } else {
            const status =
              err instanceof Error && "status" in err
                ? (err as { status?: number }).status
                : undefined;
            setResult((prev) => ({
              key,
              // refetch falhou: preserva o último dado bom do mesmo escopo.
              data: prev?.key === key ? prev.data : null,
              error: {
                message:
                  err instanceof Error
                    ? err.message
                    : "Atividade do posto indisponível.",
                retryable: status == null || status >= 500 || status === 0,
              },
            }));
          }
        }
      } while (pendingRef.current);
    } finally {
      inFlightRef.current = false;
    }
  }, []);

  // Carga inicial / troca de CT, filial ou sessão.
  useEffect(() => {
    void refresh();
  }, [refresh, sessionToken, workCenter, branch]);

  // Transições do posto no WS disparam reconciliação coalescida.
  useEffect(() => {
    const scoped =
      (!runRealtimeEvent?.branch || runRealtimeEvent.branch === branch) &&
      (!runRealtimeEvent?.workCenter ||
        runRealtimeEvent.workCenter === workCenter);
    if (
      runRealtimeEvent?.type === "production_run_updated" &&
      ACTIVITY_REASONS.has(runRealtimeEvent.reason) &&
      scoped
    ) {
      void refresh();
    }
  }, [runRealtimeEvent, branch, workCenter, refresh]);

  // Reconexão do WS: uma reconciliação HTTP (há eventos perdidos).
  const wasConnectedRef = useRef(realtimeConnected);
  useEffect(() => {
    const was = wasConnectedRef.current;
    wasConnectedRef.current = realtimeConnected;
    if (!was && realtimeConnected) void refresh();
  }, [realtimeConnected, refresh]);

  // Retorno de aba inativa + virada do dia civil SP.
  useEffect(() => {
    const checkDay = () => {
      const key = spCivilDayKey();
      if (key !== dayKeyRef.current) {
        dayKeyRef.current = key;
        void refresh();
      }
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        checkDay();
        void refresh();
      }
    };
    const timer = window.setInterval(checkDay, DAY_WATCH_MS);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refresh]);

  // Só vale resultado produzido pelo escopo atual — CT/sessão trocados
  // nunca exibem dados antigos como se fossem do posto selecionado.
  const scoped = result?.key === currentKey ? result : null;
  const data = scoped?.data ?? null;
  const error = scoped?.error ?? null;
  const loading = Boolean(
    sessionToken && workCenter && !scoped,
  );

  return useMemo(
    () => ({ data, error, loading, refresh }),
    [data, error, loading, refresh],
  );
}
