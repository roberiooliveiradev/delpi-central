import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchMachineLoad, fetchMachineLoadLiveStatus, refreshMachineLoad } from "../api/ppcApi";
import { copy } from "../content/copy";
import type { MachineLoadLiveStatusPayload, MachineLoadPayload, PpcBranch } from "../types";
import { applyMachineLoadLiveStatus } from "../utils/machineLoadLiveStatus";
import { selectMachineLoadCenter } from "../utils/machineLoadSelection";

type UseMachineLoadParams = {
  branch: PpcBranch;
  workCenter: string | null;
  startDate: string | null;
  endDate: string | null;
};

/**
 * A fila é uma só por filial + janela de leitura. O centro de trabalho **não**
 * entra na chave: ele é recorte de apresentação, resolvido localmente.
 */
function scopeKey(
  branch: PpcBranch,
  startDate: string | null,
  endDate: string | null,
): string {
  return `${branch}|${startDate ?? ""}|${endDate ?? ""}`;
}

/** Frequência do status vivo do chão de fábrica, pausado com a aba oculta. */
const LIVE_STATUS_INTERVAL_MS = 30_000;

/** Filas já carregadas nesta sessão do MFE — voltar de outra aba do PPC não recarrega. */
const MAX_CACHED_SCOPES = 4;
const queueCache = new Map<string, MachineLoadPayload>();

function readQueueCache(key: string): MachineLoadPayload | null {
  return queueCache.get(key) ?? null;
}

function writeQueueCache(key: string, payload: MachineLoadPayload): void {
  queueCache.delete(key);
  queueCache.set(key, payload);
  while (queueCache.size > MAX_CACHED_SCOPES) {
    const oldest = queueCache.keys().next().value;
    if (oldest === undefined) break;
    queueCache.delete(oldest);
  }
}

/**
 * Carrega a fila da filial uma vez por escopo e recorta o centro de trabalho em
 * memória: trocar de aba não custa requisição nem passa por estado vazio.
 */
export function useMachineLoad({ branch, workCenter, startDate, endDate }: UseMachineLoadParams) {
  const scope = scopeKey(branch, startDate, endDate);
  const [snapshot, setSnapshot] = useState<MachineLoadPayload | null>(null);
  const [liveStatus, setLiveStatus] = useState<MachineLoadLiveStatusPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((value) => value + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    const cached = readQueueCache(scope);

    if (cached) {
      // Fila já conhecida: mostra na hora e revalida em silêncio.
      setSnapshot(cached);
      setError(null);
      setLoading(false);
    } else {
      setSnapshot(null);
      setLoading(true);
    }

    // Sem `workCenter`: a leitura traz a filial inteira e o recorte é local.
    fetchMachineLoad({ branch, startDate, endDate, signal: controller.signal })
      .then((payload) => {
        writeQueueCache(scope, payload);
        setSnapshot(payload);
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : copy.machineLoad.loadError);
        if (!readQueueCache(scope)) setSnapshot(null);
      })
      .finally(() => {
        if (controller.signal.aborted) return;
        setLoading(false);
      });

    return () => controller.abort();
  }, [branch, endDate, scope, startDate, reloadToken]);

  const applyPayload = useCallback(
    (payload: MachineLoadPayload) => {
      writeQueueCache(scope, payload);
      setSnapshot(payload);
    },
    [scope],
  );

  const refreshFromTotvs = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const payload = await refreshMachineLoad({ branch, startDate, endDate });
      writeQueueCache(scope, payload);
      setSnapshot(payload);
      return payload;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : copy.machineLoad.loadError;
      setError(message);
      throw err;
    } finally {
      setRefreshing(false);
    }
  }, [branch, endDate, scope, startDate]);

  // Status congelado da filial anterior não vale para a nova.
  useEffect(() => {
    setLiveStatus(null);
  }, [branch]);

  // O chão de fábrica sai do caminho crítico: a fila aparece primeiro e o status
  // chega em seguida, sem recarregar a fila.
  const hasQueue = snapshot != null;
  useEffect(() => {
    if (!hasQueue) return;
    let cancelled = false;
    const pending = new Set<AbortController>();

    const poll = () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;
      const controller = new AbortController();
      pending.add(controller);
      fetchMachineLoadLiveStatus({ branch, signal: controller.signal })
        .then((payload) => {
          if (!cancelled) setLiveStatus(payload);
        })
        .catch(() => {
          // Best-effort: sem status vivo a fila congelada continua válida na tela.
        })
        .finally(() => pending.delete(controller));
    };

    poll();
    const timer = setInterval(poll, LIVE_STATUS_INTERVAL_MS);
    const onVisibilityChange = () => {
      if (document.visibilityState === "visible") poll();
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      cancelled = true;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      for (const controller of pending) controller.abort();
    };
  }, [branch, hasQueue]);

  // Fila congelada → status vivo → recorte do centro ativo. Trocar de centro
  // percorre só a última etapa, em memória.
  const data = useMemo(() => {
    if (!snapshot) return null;
    const withStatus = liveStatus
      ? applyMachineLoadLiveStatus(snapshot, liveStatus)
      : snapshot;
    return selectMachineLoadCenter(withStatus, workCenter);
  }, [snapshot, liveStatus, workCenter]);

  return {
    data,
    loading,
    refreshing,
    error,
    reload,
    refreshFromTotvs,
    applyPayload,
  };
}
