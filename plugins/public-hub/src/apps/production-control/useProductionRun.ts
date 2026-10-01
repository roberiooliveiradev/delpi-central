import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  classifyRunDowntime,
  fetchActiveProductionRun,
  fetchMesDowntimeReasons,
  isAuthError,
  pauseProductionRun,
  resumeProductionRun,
  startProductionRun,
  stopProductionRun,
  type BenchSessionSnapshot,
  type MachineLoadOperation,
  type MesDowntimeReason,
  type ProductionRunSnapshot,
} from "./api.ts";
import {
  applyProductionRunDowntimeEvent,
  applyProductionRunPiecesSnapshot,
} from "./productionRunRealtime.ts";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";

const RUN_POLL_MS = 1_000;

type Options = {
  token: string;
  branch: string;
  workCenter: string | null;
  operation: MachineLoadOperation | null;
  /**
   * C4: a sessão do operador vem do OperatorSessionProvider — este hook só
   * consome sessionToken. onAuthError deve descartar a sessão local (401).
   */
  session: BenchSessionSnapshot | null;
  onAuthError?: () => void;
  runUpdatedSignal?: number;
  runRealtimeEvent?: MachineLoadRealtimeEvent | null;
  realtimeConnected?: boolean;
};

export function useProductionRun({
  token,
  branch,
  workCenter,
  operation,
  session,
  onAuthError,
  runUpdatedSignal = 0,
  runRealtimeEvent = null,
  realtimeConnected = false,
}: Options) {
  const [run, setRun] = useState<ProductionRunSnapshot | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [downtimeReasons, setDowntimeReasons] = useState<MesDowntimeReason[] | null>(null);
  const downtimeReasonsInFlightRef = useRef(false);
  const pollRef = useRef(0);
  const refreshInFlightRef = useRef(false);
  const refreshPendingRef = useRef(false);
  const refreshRequestRef = useRef({ token, branch, workCenter });

  useEffect(() => {
    refreshRequestRef.current = { token, branch, workCenter };
  }, [token, branch, workCenter]);

  useEffect(() => {
    queueMicrotask(() => {
      if (!workCenter) setRun(null);
    });
  }, [workCenter]);

  const dropStaleSession = useCallback(
    (err: unknown) => {
      // 401 = sessão expirada/inválida no backend: a camada de sessão limpa
      // o estado e o formulário de identificação reaparece.
      if (!isAuthError(err)) return;
      onAuthError?.();
    },
    [onAuthError],
  );

  const refreshRun = useCallback(async () => {
    if (refreshInFlightRef.current) {
      refreshPendingRef.current = true;
      return;
    }

    refreshInFlightRef.current = true;
    try {
      do {
        refreshPendingRef.current = false;
        const request = refreshRequestRef.current;
        if (!request.workCenter) {
          setRun(null);
          continue;
        }
        try {
          const next = await fetchActiveProductionRun(
            request.token,
            request.branch,
            request.workCenter,
          );
          const current = refreshRequestRef.current;
          if (
            current.token === request.token &&
            current.branch === request.branch &&
            current.workCenter === request.workCenter
          ) {
            setRun(next);
            setError(null);
          }
        } catch (err) {
          const current = refreshRequestRef.current;
          if (
            current.token === request.token &&
            current.branch === request.branch &&
            current.workCenter === request.workCenter
          ) {
            dropStaleSession(err);
            setError(err instanceof Error ? err.message : "Falha ao ler a contagem.");
          }
        }
      } while (refreshPendingRef.current);
    } finally {
      refreshInFlightRef.current = false;
    }
  }, [dropStaleSession]);

  useEffect(() => {
    void refreshRun();
  }, [refreshRun, runUpdatedSignal]);

  useEffect(() => {
    window.clearInterval(pollRef.current);
    if (!workCenter || realtimeConnected || !run || run.status !== "running") return;
    pollRef.current = window.setInterval(() => {
      void refreshRun();
    }, RUN_POLL_MS);
    return () => window.clearInterval(pollRef.current);
  }, [workCenter, realtimeConnected, run, refreshRun]);

  const play = useCallback(async () => {
    if (!workCenter || !operation || !session) return;
    setBusy(true);
    setError(null);
    try {
      const started = await startProductionRun(token, session.sessionToken, {
        branch,
        workCenter,
        productionOrder: operation.production_order,
        operationCode: operation.operation_code,
      });
      setRun(started);
    } catch (err) {
      dropStaleSession(err);
      setError(err instanceof Error ? err.message : "Falha ao iniciar.");
    } finally {
      setBusy(false);
    }
  }, [token, branch, workCenter, operation, session, dropStaleSession]);

  const pause = useCallback(async () => {
    if (!run || !session) return;
    setBusy(true);
    try {
      setRun(await pauseProductionRun(token, session.sessionToken, run.id));
    } catch (err) {
      dropStaleSession(err);
      setError(err instanceof Error ? err.message : "Falha ao pausar.");
    } finally {
      setBusy(false);
    }
  }, [token, run, session, dropStaleSession]);

  const resume = useCallback(async () => {
    if (!run || !session) return;
    setBusy(true);
    try {
      setRun(await resumeProductionRun(token, session.sessionToken, run.id));
    } catch (err) {
      dropStaleSession(err);
      setError(err instanceof Error ? err.message : "Falha ao retomar.");
    } finally {
      setBusy(false);
    }
  }, [token, run, session, dropStaleSession]);

  const stop = useCallback(async () => {
    if (!run || !session) return;
    setBusy(true);
    try {
      await stopProductionRun(token, session.sessionToken, run.id);
      setRun(null);
    } catch (err) {
      dropStaleSession(err);
      setError(err instanceof Error ? err.message : "Falha ao encerrar.");
    } finally {
      setBusy(false);
    }
  }, [token, run, session, dropStaleSession]);

  const resolvedRun = useMemo(() => {
    const withPieces = applyProductionRunPiecesSnapshot(
      run,
      runRealtimeEvent,
      branch,
      workCenter,
    );
    return applyProductionRunDowntimeEvent(withPieces, runRealtimeEvent, branch, workCenter);
  }, [branch, run, runRealtimeEvent, workCenter]);

  const loadDowntimeReasons = useCallback(async (): Promise<MesDowntimeReason[]> => {
    if (downtimeReasons) return downtimeReasons;
    if (!downtimeReasonsInFlightRef.current) {
      downtimeReasonsInFlightRef.current = true;
      try {
        const items = await fetchMesDowntimeReasons(token);
        setDowntimeReasons(items);
        return items;
      } finally {
        downtimeReasonsInFlightRef.current = false;
      }
    }
    return fetchMesDowntimeReasons(token);
  }, [downtimeReasons, token]);

  /**
   * Classifica uma parada por identidade explícita — funciona também para
   * paradas de runs já encerrados (o backend só exige sessão do mesmo posto).
   */
  const classifyDowntimeById = useCallback(
    async (runId: string, downtimeId: string, reasonCode: string, note: string | null) => {
      if (!session) return;
      setBusy(true);
      try {
        const downtime = await classifyRunDowntime(token, session.sessionToken, runId, {
          reasonCode,
          note,
          downtimeId,
        });
        if (downtime.endedAt || !run || run.id !== runId) {
          // Parada encerrada ou de outro run: reconcilia o snapshot para
          // limpar pendingDowntime/pendingDowntimeCount se aplicável.
          void refreshRun();
        } else {
          setRun((current) =>
            current && current.id === runId ? { ...current, downtime } : current,
          );
        }
      } catch (err) {
        dropStaleSession(err);
        setError(err instanceof Error ? err.message : "Falha ao registrar o motivo.");
        throw err;
      } finally {
        setBusy(false);
      }
    },
    [token, run, session, dropStaleSession, refreshRun],
  );

  const classifyDowntime = useCallback(
    async (reasonCode: string, note: string | null, downtimeId?: string | null) => {
      if (!run) return;
      const target = downtimeId ?? run.downtime?.id ?? null;
      if (target) {
        await classifyDowntimeById(run.id, target, reasonCode, note);
        return;
      }
      // Sem identidade: endpoint legado classifica a parada aberta do run.
      if (!session) return;
      setBusy(true);
      try {
        const downtime = await classifyRunDowntime(token, session.sessionToken, run.id, {
          reasonCode,
          note,
          downtimeId: null,
        });
        setRun((current) =>
          current && current.id === run.id ? { ...current, downtime } : current,
        );
      } catch (err) {
        dropStaleSession(err);
        setError(err instanceof Error ? err.message : "Falha ao registrar o motivo.");
        throw err;
      } finally {
        setBusy(false);
      }
    },
    [token, run, session, dropStaleSession, classifyDowntimeById],
  );

  const runMatchesOperation = useMemo(() => {
    if (!resolvedRun || !operation) return false;
    return (
      resolvedRun.productionOrder === operation.production_order &&
      resolvedRun.operationCode === operation.operation_code
    );
  }, [resolvedRun, operation]);

  return {
    session,
    run: resolvedRun,
    runMatchesOperation,
    busy,
    error,
    play,
    pause,
    resume,
    stop,
    refreshRun,
    downtimeReasons,
    loadDowntimeReasons,
    classifyDowntime,
    classifyDowntimeById,
  };
}
