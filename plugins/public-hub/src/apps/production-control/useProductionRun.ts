import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createBenchSession,
  endBenchSession,
  fetchActiveProductionRun,
  pauseProductionRun,
  resumeProductionRun,
  startProductionRun,
  stopProductionRun,
  type BenchSessionSnapshot,
  type MachineLoadOperation,
  type ProductionRunSnapshot,
} from "./api";
import { operationPendingQty } from "./cockpitStatus";

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
  realtimeConnected?: boolean;
};

export function useProductionRun({
  token,
  branch,
  workCenter,
  operation,
  runUpdatedSignal = 0,
  realtimeConnected = false,
}: Options) {
  const [session, setSession] = useState<BenchSessionSnapshot | null>(null);
  const [run, setRun] = useState<ProductionRunSnapshot | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [operatorCode, setOperatorCode] = useState("");
  const [operatorName, setOperatorName] = useState("");
  const pollRef = useRef(0);

  useEffect(() => {
    if (!workCenter) {
      setSession(null);
      setRun(null);
      return;
    }
    setSession(readStoredSession(branch, workCenter));
  }, [branch, workCenter]);

  const refreshRun = useCallback(async () => {
    if (!workCenter) {
      setRun(null);
      return;
    }
    try {
      const next = await fetchActiveProductionRun(token, branch, workCenter);
      setRun(next);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao ler a contagem.");
    }
  }, [token, branch, workCenter]);

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
  }, [workCenter, realtimeConnected, run?.id, run?.status, refreshRun]);

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
        plannedQty: operationPendingQty(operation),
      });
      setRun(started);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao iniciar.");
    } finally {
      setBusy(false);
    }
  }, [token, branch, workCenter, operation, session]);

  const pause = useCallback(async () => {
    if (!run || !session) return;
    setBusy(true);
    try {
      setRun(await pauseProductionRun(token, session.sessionToken, run.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao pausar.");
    } finally {
      setBusy(false);
    }
  }, [token, run, session]);

  const resume = useCallback(async () => {
    if (!run || !session) return;
    setBusy(true);
    try {
      setRun(await resumeProductionRun(token, session.sessionToken, run.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao retomar.");
    } finally {
      setBusy(false);
    }
  }, [token, run, session]);

  const stop = useCallback(async () => {
    if (!run || !session) return;
    setBusy(true);
    try {
      await stopProductionRun(token, session.sessionToken, run.id);
      setRun(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao encerrar.");
    } finally {
      setBusy(false);
    }
  }, [token, run, session]);

  const runMatchesOperation = useMemo(() => {
    if (!run || !operation) return false;
    return (
      run.productionOrder === operation.production_order &&
      run.operationCode === operation.operation_code
    );
  }, [run, operation]);

  return {
    session,
    run,
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
  };
}
