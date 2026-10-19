import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchMesWorkCenterPeriod,
  isAuthError,
  type MesWorkCenterPeriod,
} from "./api";
import { spCivilDayKey } from "./workCenterActivity";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";
import type { WorkCenterActivityError } from "./useWorkCenterActivity";

/** Razões que alteram agregados do período — pieces_updated fora. */
const PERIOD_REASONS = new Set([
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
  /** Janela em dias civis SP — faz parte do escopo da consulta. */
  days?: number;
  runRealtimeEvent?: MachineLoadRealtimeEvent | null;
  realtimeConnected?: boolean;
  onAuthError?: (err: unknown) => void;
};

type PeriodResult = {
  /** Escopo (token|sessão|filial|CT|dias) que produziu este resultado. */
  key: string;
  data: MesWorkCenterPeriod | null;
  error: WorkCenterActivityError | null;
};

function scopeKey(
  token: string,
  sessionToken: string | null,
  branch: string,
  workCenter: string | null,
  days: number,
): string {
  return `${token}|${sessionToken}|${branch}|${workCenter}|${days}`;
}

/**
 * Resumo MES do posto por período (Etapa 4) — mesmo contrato de escopo,
 * single-flight e reconciliação do hook diário. Resposta de outro
 * CT/sessão/período nunca é exibida como atual; 401 tardio de escopo
 * substituído não invalida a sessão vigente.
 */
export function useMesWorkCenterPeriod({
  token,
  sessionToken,
  branch,
  workCenter,
  days = 7,
  runRealtimeEvent = null,
  realtimeConnected = false,
  onAuthError,
}: Options) {
  const currentKey = scopeKey(token, sessionToken, branch, workCenter, days);
  const [result, setResult] = useState<PeriodResult | null>(null);
  const inFlightRef = useRef(false);
  const pendingRef = useRef(false);
  const onAuthErrorRef = useRef(onAuthError);
  const requestRef = useRef({ token, sessionToken, branch, workCenter, days });
  const dayKeyRef = useRef(spCivilDayKey());

  useEffect(() => {
    onAuthErrorRef.current = onAuthError;
  }, [onAuthError]);

  useEffect(() => {
    requestRef.current = { token, sessionToken, branch, workCenter, days };
  }, [token, sessionToken, branch, workCenter, days]);

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
          request.days,
        );
        if (!request.sessionToken || !request.workCenter) {
          continue;
        }
        try {
          const next = await fetchMesWorkCenterPeriod(
            request.token,
            request.sessionToken,
            request.branch,
            request.workCenter,
            request.days,
          );
          setResult({ key, data: next, error: null });
        } catch (err) {
          // Escopo vigente no momento da resposta — 401 de sessão/CT
          // substituídos não pode derrubar a sessão atual.
          const live = requestRef.current;
          const stale =
            key !==
            scopeKey(
              live.token,
              live.sessionToken,
              live.branch,
              live.workCenter,
              live.days,
            );
          if (isAuthError(err)) {
            setResult({ key, data: null, error: null });
            if (!stale) onAuthErrorRef.current?.(err);
          } else {
            const status =
              err instanceof Error && "status" in err
                ? (err as { status?: number }).status
                : undefined;
            setResult((prev) => ({
              key,
              data: prev?.key === key ? prev.data : null,
              error: {
                message:
                  err instanceof Error
                    ? err.message
                    : "Desempenho MES do posto indisponível.",
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

  // Carga inicial / troca de CT, filial, sessão ou período.
  useEffect(() => {
    void refresh();
  }, [refresh, sessionToken, workCenter, branch, days]);

  // Transições do posto no WS — classificação incluída (muda motivos).
  useEffect(() => {
    const scoped =
      (!runRealtimeEvent?.branch || runRealtimeEvent.branch === branch) &&
      (!runRealtimeEvent?.workCenter ||
        runRealtimeEvent.workCenter === workCenter);
    if (
      runRealtimeEvent?.type === "production_run_updated" &&
      PERIOD_REASONS.has(runRealtimeEvent.reason) &&
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

  // Retorno de aba inativa + virada do dia civil SP (a janela muda).
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

  const scoped = result?.key === currentKey ? result : null;
  const data = scoped?.data ?? null;
  const error = scoped?.error ?? null;
  const loading = Boolean(sessionToken && workCenter && !scoped);

  return useMemo(
    () => ({ data, error, loading, refresh }),
    [data, error, loading, refresh],
  );
}
