import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  classifyRunDowntime,
  createBenchSession,
  endBenchSession,
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
} from "./api";
import {
  applyProductionRunDowntimeEvent,
  applyProductionRunPiecesSnapshot,
} from "./productionRunRealtime";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";

const SESSION_STORAGE_PREFIX = "delpi.pcp.cockpit.bench-session";
const RUN_POLL_MS = 1_000;

function sessionStorageKey(branch: string, workCenter: string): string {
  return `${SESSION_STORAGE_PREFIX}.${branch}.${workCenter}`;
}

function readStoredSession(branch: string, workCenter: string): BenchSessionSnapshot | null {
  try {
    const raw = window.sessionStorage.getItem(sessionStorageKey(branch, workCenter));
    if (!raw) return null;
    return JSON.parse(raw) as BenchSessionSnapshot;
  } catch {
    return null;
  }
}

function storeSession(branch: string, workCenter: string, session: BenchSessionSnapshot | null): void {
  try {
    const key = sessionStorageKey(branch, workCenter);
    if (session) window.sessionStorage.setItem(key, JSON.stringify(session));
    else window.sessionStorage.removeItem(key);
  } catch {
    /* private mode */
  }
}

type Options = {
  token: string;
  branch: string;
  workCenter: string | null;
  operation: MachineLoadOperation | null;
  runUpdatedSignal?: number;
  runRealtimeEvent?: MachineLoadRealtimeEvent | null;
  realtimeConnected?: boolean;
};

export function useProductionRun({
  token,
  branch,
  workCenter,
  operation,
  runUpdatedSignal = 0,
  runRealtimeEvent = null,
  realtimeConnected = false,
}: Options) {
  const [session, setSession] = useState<BenchSessionSnapshot | null>(null);
  const [run, setRun] = useState<ProductionRunSnapshot | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [operatorCode, setOperatorCode] = useState("");
  const [operatorName, setOperatorName] = useState("");
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
    let active = true;
    const nextSession = workCenter ? readStoredSession(branch, workCenter) : null;
    queueMicrotask(() => {
      if (!active) return;
      setSession(nextSession);
      if (!workCenter) setRun(null);
    });
    return () => {
      active = false;
    };
  }, [branch, workCenter]);

  const dropStaleSession = useCallback(
    (err: unknown) => {
      // 401 = sessão expirada/inválida no backend: descarta a sessão local
      // para o formulário de identificação reaparecer.
      if (!isAuthError(err)) return;
      if (workCenter) storeSession(branch, workCenter, null);
      setSession(null);
    },
    [branch, workCenter],
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

  const identify = useCallback(async () => {
    if (!workCenter) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createBenchSession(token, {
        branch,
        workCenter,
        operatorCode: operatorCode.trim(),
        operatorName: operatorName.trim() || null,
      });
      storeSession(branch, workCenter, created);
      setSession(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao identificar operador.");
    } finally {
      setBusy(false);
    }
  }, [token, branch, workCenter, operatorCode, operatorName]);

  const clearSession = useCallback(async () => {
    if (!workCenter || !session) return;
    setBusy(true);
    try {
      await endBenchSession(token, session.sessionToken);
    } catch {
      /* still clear local */
    } finally {
      storeSession(branch, workCenter, null);
      setSession(null);
      setBusy(false);
    }
  }, [token, branch, workCenter, session]);

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

  const classifyDowntime = useCallback(
    async (reasonCode: string, note: string | null, downtimeId?: string | null) => {
      if (!run || !session) return;
      setBusy(true);
      try {
        const downtime = await classifyRunDowntime(token, session.sessionToken, run.id, {
          reasonCode,
          note,
          downtimeId: downtimeId ?? null,
        });
        if (downtime.endedAt) {
          // Parada já encerrada: não é mais a parada aberta — reconcilia o
          // snapshot para limpar pendingDowntime/pendingDowntimeCount.
          void refreshRun();
        } else {
          setRun((current) =>
            current && current.id === run.id ? { ...current, downtime } : current,
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
    operatorCode,
    operatorName,
    setOperatorCode,
    setOperatorName,
    identify,
    clearSession,
    play,
    pause,
    resume,
    stop,
    refreshRun,
    downtimeReasons,
    loadDowntimeReasons,
    classifyDowntime,
  };
}
