import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchMachineLoad,
  fetchMachineLoadBalances,
  fetchMachineLoadCockpitStatus,
  publishMachineLoad,
  refreshMachineLoad,
} from "../api/ppcApi";
import { copy } from "../content/copy";
import type {
  MachineLoadBalancesPayload,
  MachineLoadCockpitStatusPayload,
  MachineLoadPayload,
  PpcBranch,
} from "../types";
import {
  applyMachineLoadBalances,
  applyMachineLoadCockpitStatus,
} from "../utils/machineLoadCockpitStatus";
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

/** Frequência do estado de execução e dos saldos, pausados com a aba oculta. */
const EXECUTION_STATUS_INTERVAL_MS = 30_000;

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
 *
 * A execução vem exclusivamente do cockpit (`/machine-load/cockpit-status`) e
 * os saldos de `/machine-load/balances` — duas leituras best-effort a cada
 * 30 s, suspensas com a aba oculta. Nenhuma delas toca a fila congelada:
 * snapshot, ordem e publicação permanecem estáveis entre as consultas.
 */
export function useMachineLoad({ branch, workCenter, startDate, endDate }: UseMachineLoadParams) {
  const scope = scopeKey(branch, startDate, endDate);
  const [snapshot, setSnapshot] = useState<MachineLoadPayload | null>(null);
  const [cockpitStatus, setCockpitStatus] = useState<MachineLoadCockpitStatusPayload | null>(null);
  const [balances, setBalances] = useState<MachineLoadBalancesPayload | null>(null);
  const [executionUnavailable, setExecutionUnavailable] = useState(false);
  const [balancesUnavailable, setBalancesUnavailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [publishing, setPublishing] = useState(false);
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

  /**
   * Libera a programacao atual para os cockpits. O WORKING nao muda — a resposta
   * do publish atualiza so o estado de publicacao, sem rebaixar a fila inteira.
   */
  const publishToMachines = useCallback(async () => {
    setPublishing(true);
    setError(null);
    try {
      const publication = await publishMachineLoad({ branch });
      setSnapshot((current) => {
        if (!current) return current;
        const next = {
          ...current,
          publication: {
            state: publication.state,
            published_at: publication.published_at,
            published_by: publication.published_by,
          },
        };
        writeQueueCache(scope, next);
        return next;
      });
      return publication;
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : copy.machineLoad.publish.error;
      setError(message);
      throw err;
    } finally {
      setPublishing(false);
    }
  }, [branch, scope]);

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

  // Estado de execução e saldos de outra filial não valem para a nova — limpa
  // imediatamente para não contaminar a fila que está chegando.
  useEffect(() => {
    setCockpitStatus(null);
    setBalances(null);
    setExecutionUnavailable(false);
    setBalancesUnavailable(false);
  }, [branch]);

  // Execução do cockpit e saldos saem do caminho crítico: a fila aparece
  // primeiro e as duas leituras chegam em seguida, sem recarregar a fila.
  const hasQueue = snapshot != null;
  useEffect(() => {
    if (!hasQueue) return;
    let cancelled = false;
    const pending = new Set<AbortController>();
    // Sem requisição concorrente redundante: enquanto a última não fecha,
    // o próximo tick pula — resposta atrasada nunca disputa com a mais nova.
    let statusInFlight = false;
    let balancesInFlight = false;

    const poll = () => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") return;

      if (!statusInFlight) {
        statusInFlight = true;
        const statusController = new AbortController();
        pending.add(statusController);
        fetchMachineLoadCockpitStatus({ branch, signal: statusController.signal })
          .then((payload) => {
            if (cancelled) return;
            setCockpitStatus(payload);
            setExecutionUnavailable(false);
          })
          .catch(() => {
            // Best-effort: a fila e a última leitura válida permanecem; a tela
            // sinaliza indisponibilidade em vez de esconder ou inventar execução.
            if (!cancelled) setExecutionUnavailable(true);
          })
          .finally(() => {
            statusInFlight = false;
            pending.delete(statusController);
          });
      }

      if (!balancesInFlight) {
        balancesInFlight = true;
        const balancesController = new AbortController();
        pending.add(balancesController);
        fetchMachineLoadBalances({ branch, signal: balancesController.signal })
          .then((payload) => {
            if (cancelled) return;
            setBalances(payload);
            setBalancesUnavailable(false);
          })
          .catch(() => {
            // Saldo desconhecido não esconde trabalho: último valor conhecido fica.
            if (!cancelled) setBalancesUnavailable(true);
          })
          .finally(() => {
            balancesInFlight = false;
            pending.delete(balancesController);
          });
      }
    };

    poll();
    const timer = setInterval(poll, EXECUTION_STATUS_INTERVAL_MS);
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

  // Fila congelada → execução do cockpit → saldos → recorte do centro ativo.
  // Trocar de centro percorre só a última etapa, em memória.
  const data = useMemo(() => {
    if (!snapshot) return null;
    const withExecution = cockpitStatus
      ? applyMachineLoadCockpitStatus(snapshot, cockpitStatus)
      : snapshot;
    const withBalances = balances
      ? applyMachineLoadBalances(withExecution, balances)
      : withExecution;
    return selectMachineLoadCenter(withBalances, workCenter);
  }, [snapshot, cockpitStatus, balances, workCenter]);

  return {
    data,
    loading,
    refreshing,
    publishing,
    error,
    executionUnavailable,
    /** Primeira leitura de execução recebida — agrupamento exige fonte viva. */
    executionLoaded: cockpitStatus != null,
    balancesUnavailable,
    reload,
    refreshFromTotvs,
    publishToMachines,
    applyPayload,
  };
}
