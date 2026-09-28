import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildDataPreviewFingerprint,
  DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS,
  DATA_REFRESH_SEC_DEFAULT,
  isFetchableDataBlockType,
  mergeComunicadoDataPages,
  planDataModelPreviewRefresh,
  planDataPreviewRefresh,
  resolveComunicadoDataPageState,
  resolveDataBlockErrorText,
  resolveDataBlockRefreshSec,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataBinding,
  type ComunicadoDataResolved,
  type TvDataModel,
} from "@delpi/tv-dashboard-presentation";

import {
  createLinkedTimeoutSignal,
  DATA_PREVIEW_BLOCK_TIMEOUT_MS,
  formatDataPreviewLoadingLabel,
  resolveDataSourceProgressLabel,
  resolvePreviewAbortMessage,
} from "../utils/dataPreviewFetchGuard";
import {
  requestDataPreviewBlock,
  requestDataPreviewModel,
  serializeNativeConfigForPreview,
  stripBlockResolvedForPreview,
} from "../utils/dataPreviewRequest";
import { readDataPreviewCache, writeDataPreviewCache } from "../utils/editorSessionCache";

export type RefreshDataPreviewOptions = {
  /** Bypass cache no servidor (clique em Atualizar visual). */
  force?: boolean;
  blockIds?: string[];
};

type Options = {
  playlistId: string;
  config: ComunicadoConfig;
  /** dataDefaults live da programação — entra no fingerprint e no preview. */
  playlistDefaults?: Record<string, unknown> | null;
  /** Intervalo padrão da programação (segundos) — refresh periódico no editor. */
  globalRefreshSec?: number | null;
};

type FetchableBlock = Extract<ComunicadoBlock, { dataBinding: ComunicadoDataBinding }>;

/**
 * Unidade de preview: bloco `data_source`/data_* (kind `source`) ou
 * DataModel persistido (kind `model`, `/data/preview-model`).
 */
type PreviewTarget =
  | { kind: "source"; id: string; block: FetchableBlock }
  | { kind: "model"; id: string; model: TvDataModel };

function seedFromConfigBlocks(config: ComunicadoConfig): Record<string, ComunicadoDataResolved> {
  const seeded: Record<string, ComunicadoDataResolved> = {};
  for (const block of config.blocks ?? []) {
    if (!isFetchableDataBlockType(block.type)) continue;
    if (!("resolved" in block) || !block.resolved || typeof block.resolved !== "object") continue;
    seeded[block.id] = block.resolved as ComunicadoDataResolved;
  }
  return seeded;
}

function initialResolvedMap(
  playlistId: string,
  config: ComunicadoConfig,
  playlistDefaults?: Record<string, unknown> | null,
): Record<string, ComunicadoDataResolved> {
  const fingerprint = buildDataPreviewFingerprint(config, { playlistDefaults });
  const fromSession = readDataPreviewCache(playlistId, fingerprint);
  const fromBlocks = seedFromConfigBlocks(config);
  return { ...fromSession, ...fromBlocks };
}

function hasAnyResolved(
  map: Record<string, ComunicadoDataResolved>,
  targets: ReadonlyArray<{ id: string }>,
): boolean {
  return targets.some((target) => map[target.id] !== undefined);
}

/** Agrega mensagens de erro soft/hard dos resolved para a barra do palco. */
export function collectPreviewErrorMessages(
  pairs: ReadonlyArray<readonly [string, unknown]>,
): string | null {
  const messages: string[] = [];
  const seen = new Set<string>();
  for (const [, resolved] of pairs) {
    if (!resolved || typeof resolved !== "object") continue;
    const text = resolveDataBlockErrorText(resolved as ComunicadoDataResolved);
    if (!text || seen.has(text)) continue;
    seen.add(text);
    messages.push(text);
  }
  if (messages.length === 0) return null;
  if (messages.length === 1) return messages[0]!;
  return `${messages[0]} (+${messages.length - 1})`;
}

/**
 * Orquestrador único do preview de dados no editor.
 * Decisão de *quais* fontes: `planDataPreviewRefresh` (presentation).
 * Body HTTP: `requestDataPreviewBlock` (sempre com playlistDefaults live).
 */
export function useComunicadoDataPreview({
  playlistId,
  config,
  playlistDefaults = null,
  globalRefreshSec = DATA_REFRESH_SEC_DEFAULT,
}: Options) {
  const [resolvedByBlockId, setResolvedByBlockId] = useState<Record<string, ComunicadoDataResolved>>(
    () => initialResolvedMap(playlistId, config, playlistDefaults),
  );
  const [staleSourceIds, setStaleSourceIds] = useState<string[]>([]);
  const [refreshingSourceIds, setRefreshingSourceIds] = useState<string[]>([]);
  const [loadingMoreSourceIds, setLoadingMoreSourceIds] = useState<string[]>([]);
  const [initialLoading, setInitialLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  /** Progresso determinado do fetch em curso (blocos concluídos / total). */
  const [loadingProgress, setLoadingProgress] = useState<{
    completed: number;
    total: number;
    pendingLabels: string[];
  } | null>(null);

  const configRef = useRef(config);
  configRef.current = config;
  const playlistDefaultsRef = useRef(playlistDefaults);
  playlistDefaultsRef.current = playlistDefaults;
  const globalRefreshSecRef = useRef(globalRefreshSec);
  globalRefreshSecRef.current = globalRefreshSec;

  const requestIdRef = useRef(0);
  const batchAbortRef = useRef<AbortController | null>(null);
  const resolvedRef = useRef(resolvedByBlockId);
  resolvedRef.current = resolvedByBlockId;
  const playlistIdRef = useRef(playlistId);
  const fingerprintRef = useRef(
    buildDataPreviewFingerprint(config, { playlistDefaults }),
  );
  /** Fingerprint da última carga bem-sucedida (ou hidratada do session). */
  const syncedFingerprintRef = useRef(
    buildDataPreviewFingerprint(config, { playlistDefaults }),
  );
  const didInitialFetchRef = useRef(false);
  const autoRefreshTimerRef = useRef<number | null>(null);
  const loadingMoreRef = useRef(new Set<string>());

  const dataFingerprint = useMemo(
    () => buildDataPreviewFingerprint(config, { playlistDefaults }),
    [config, playlistDefaults],
  );
  fingerprintRef.current = dataFingerprint;

  const readDataBlocks = useCallback(
    () =>
      (configRef.current.blocks ?? []).filter(
        (block): block is FetchableBlock =>
          isFetchableDataBlockType(block.type) && "dataBinding" in block,
      ),
    [],
  );

  const readDataTargets = useCallback((): PreviewTarget[] => {
    const cfg = configRef.current;
    const sources: PreviewTarget[] = (cfg.blocks ?? [])
      .filter(
        (block): block is FetchableBlock =>
          isFetchableDataBlockType(block.type) && "dataBinding" in block,
      )
      .map((block) => ({ kind: "source", id: block.id, block }));
    const models: PreviewTarget[] = (cfg.dataModels ?? []).map((model) => ({
      kind: "model",
      id: model.id,
      model,
    }));
    return [...sources, ...models];
  }, []);

  useEffect(() => {
    return () => {
      if (autoRefreshTimerRef.current != null) window.clearTimeout(autoRefreshTimerRef.current);
      batchAbortRef.current?.abort();
      batchAbortRef.current = null;
    };
  }, []);

  // Troca de playlist: recarrega seed da sessão.
  useEffect(() => {
    if (playlistIdRef.current === playlistId) return;
    playlistIdRef.current = playlistId;
    const seeded = initialResolvedMap(playlistId, configRef.current, playlistDefaultsRef.current);
    const fp = buildDataPreviewFingerprint(configRef.current, {
      playlistDefaults: playlistDefaultsRef.current,
    });
    setResolvedByBlockId(seeded);
    setStaleSourceIds([]);
    setInitialLoading(false);
    setError(null);
    setLoadingProgress(null);
    batchAbortRef.current?.abort();
    batchAbortRef.current = null;
    requestIdRef.current += 1;
    fingerprintRef.current = fp;
    syncedFingerprintRef.current = fp;
    didInitialFetchRef.current = false;
    if (autoRefreshTimerRef.current != null) {
      window.clearTimeout(autoRefreshTimerRef.current);
      autoRefreshTimerRef.current = null;
    }
  }, [playlistId]);

  const mergeResolved = useCallback(
    (pairs: ReadonlyArray<readonly [string, unknown]>) => {
      setResolvedByBlockId((previous) => {
        const next = { ...previous };
        let changed = false;
        const absorb = (blockId: string, resolved: ComunicadoDataResolved) => {
          if (JSON.stringify(next[blockId]) === JSON.stringify(resolved)) return;
          next[blockId] = resolved;
          changed = true;
        };
        for (const [blockId, resolved] of pairs) {
          if (!resolved || typeof resolved !== "object") continue;
          const value = resolved as ComunicadoDataResolved;
          absorb(blockId, value);
          // Flatten linked enrich stamps so views can resolve by their own id.
          const linked = value.linkedResolvedByBlockId;
          if (linked && typeof linked === "object") {
            for (const [viewId, viewResolved] of Object.entries(linked)) {
              if (!viewResolved || typeof viewResolved !== "object") continue;
              absorb(viewId, viewResolved as ComunicadoDataResolved);
            }
          }
        }
        if (!changed) return previous;
        writeDataPreviewCache(playlistIdRef.current, fingerprintRef.current, next);
        return next;
      });
    },
    [],
  );

  const fetchTargets = useCallback(
    async (
      targets: PreviewTarget[],
      options: { showLoading: boolean; targetIds?: Set<string>; force?: boolean },
    ) => {
      if (targets.length === 0) {
        setInitialLoading(false);
        setError(null);
        setLoadingProgress(null);
        return;
      }

      const targetIds = options.targetIds ?? new Set(targets.map((target) => target.id));
      const active = targets.filter((target) => targetIds.has(target.id));
      const hasExistingData = active.some(
        (target) => resolvedRef.current[target.id] !== undefined,
      );

      if (options.showLoading && !hasExistingData) {
        setInitialLoading(true);
      }

      batchAbortRef.current?.abort();
      const batchAbort = new AbortController();
      batchAbortRef.current = batchAbort;

      const requestId = ++requestIdRef.current;
      setError(null);
      setRefreshingSourceIds([...targetIds]);
      setStaleSourceIds((prev) => prev.filter((id) => !targetIds.has(id)));

      const progressLabel = (target: PreviewTarget) =>
        target.kind === "model"
          ? target.model.label?.trim() || target.model.id
          : resolveDataSourceProgressLabel(target.block);

      const pendingIds = new Set(active.map((target) => target.id));
      setLoadingProgress({
        completed: 0,
        total: active.length,
        pendingLabels: active.map(progressLabel),
      });

      const nativeConfig = serializeNativeConfigForPreview(configRef.current);
      const fetchFingerprint = fingerprintRef.current;

      const bumpProgressById = (finishedId: string) => {
        if (requestIdRef.current !== requestId) return;
        pendingIds.delete(finishedId);
        setLoadingProgress({
          completed: active.length - pendingIds.size,
          total: active.length,
          pendingLabels: active
            .filter((target) => pendingIds.has(target.id))
            .map(progressLabel),
        });
      };

      try {
        const pairs = await Promise.all(
          active.map(async (target) => {
            const { signal, cleanup } = createLinkedTimeoutSignal(
              DATA_PREVIEW_BLOCK_TIMEOUT_MS,
              batchAbort.signal,
            );
            try {
              if (target.kind === "model") {
                const response = await requestDataPreviewModel({
                  model: target.model,
                  nativeConfig,
                  playlistId: playlistIdRef.current,
                  playlistDefaults: playlistDefaultsRef.current,
                  forceRefresh: Boolean(options.force),
                  signal,
                });
                const resolved = response.model?.resolved;
                if (resolved && typeof resolved === "object") {
                  return [target.id, resolved] as const;
                }
                return [
                  target.id,
                  { error: "Resposta de preview sem dados resolvidos." },
                ] as const;
              }
              const response = await requestDataPreviewBlock({
                block: stripBlockResolvedForPreview(target.block),
                nativeConfig,
                playlistId: playlistIdRef.current,
                playlistDefaults: playlistDefaultsRef.current,
                forceRefresh: Boolean(options.force),
                signal,
              });
              const resolved = response.block?.resolved;
              if (resolved && typeof resolved === "object") {
                return [target.id, resolved] as const;
              }
              return [
                target.id,
                { error: "Resposta de preview sem dados resolvidos." },
              ] as const;
            } catch (err) {
              const superseded = requestIdRef.current !== requestId;
              const message = resolvePreviewAbortMessage(err, superseded);
              if (!message) {
                const previous = resolvedRef.current[target.id];
                return [
                  target.id,
                  previous ?? { error: "Carregamento cancelado." },
                ] as const;
              }
              return [target.id, { error: message }] as const;
            } finally {
              cleanup();
              bumpProgressById(target.id);
            }
          }),
        );

        if (requestIdRef.current !== requestId) return;

        mergeResolved(pairs);
        syncedFingerprintRef.current = fetchFingerprint;
        setStaleSourceIds((prev) => prev.filter((id) => !targetIds.has(id)));
        setError(collectPreviewErrorMessages(pairs));
      } catch (err) {
        if (requestIdRef.current !== requestId) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar dados.");
        setStaleSourceIds((prev) => [...new Set([...prev, ...targetIds])]);
      } finally {
        if (requestIdRef.current === requestId) {
          setInitialLoading(false);
          setRefreshingSourceIds([]);
          setLoadingProgress(null);
          if (batchAbortRef.current === batchAbort) {
            batchAbortRef.current = null;
          }
        }
      }
    },
    [mergeResolved],
  );

  const refreshDataPreview = useCallback(
    async (options?: RefreshDataPreviewOptions) => {
      const targets = readDataTargets();
      if (targets.length === 0) {
        setStaleSourceIds([]);
        setError(null);
        return;
      }
      const targetIds = options?.blockIds?.length
        ? new Set(options.blockIds)
        : new Set(targets.map((target) => target.id));
      await fetchTargets(targets, {
        showLoading: true,
        targetIds,
        force: options?.force !== false,
      });
    },
    [fetchTargets, readDataTargets],
  );

  const loadMoreDataPreview = useCallback(
    async (blockId: string) => {
      if (loadingMoreRef.current.has(blockId)) return;
      const block = readDataBlocks().find((item) => item.id === blockId);
      const previous = resolvedRef.current[blockId];
      const pageState = resolveComunicadoDataPageState(previous);
      if (!block || !previous || !pageState?.hasMore) return;
      const requestBlock = {
        ...block,
        dataBinding: {
          ...block.dataBinding,
          params: {
            ...(block.dataBinding.params ?? {}),
            page: pageState.page + 1,
            page_size:
              pageState.pageSize ??
              (Number(block.dataBinding.params?.page_size) || 30),
          },
        },
      };
      loadingMoreRef.current.add(blockId);
      setLoadingMoreSourceIds((current) => [...new Set([...current, blockId])]);
      setLoadingProgress({
        completed: 0,
        total: 1,
        pendingLabels: [resolveDataSourceProgressLabel(block)],
      });
      const { signal, cleanup } = createLinkedTimeoutSignal(DATA_PREVIEW_BLOCK_TIMEOUT_MS);
      try {
        const response = await requestDataPreviewBlock({
          block: stripBlockResolvedForPreview(requestBlock),
          nativeConfig: serializeNativeConfigForPreview(configRef.current),
          playlistId: playlistIdRef.current,
          playlistDefaults: playlistDefaultsRef.current,
          forceRefresh: false,
          signal,
        });
        const nextPage = response.block?.resolved;
        if (!nextPage || typeof nextPage !== "object") {
          setError("Resposta de preview sem dados resolvidos.");
          return;
        }
        const pageError = resolveDataBlockErrorText(nextPage as ComunicadoDataResolved);
        if (pageError) {
          setError(pageError);
          return;
        }
        setResolvedByBlockId((current) => {
          const merged = mergeComunicadoDataPages(
            current[blockId] ?? previous,
            nextPage as ComunicadoDataResolved,
          );
          const next = { ...current, [blockId]: merged };
          resolvedRef.current = next;
          writeDataPreviewCache(playlistIdRef.current, fingerprintRef.current, next);
          return next;
        });
        setLoadingProgress({
          completed: 1,
          total: 1,
          pendingLabels: [],
        });
      } catch (err) {
        const message = resolvePreviewAbortMessage(err, false);
        setError(message ?? "Falha ao carregar mais dados.");
      } finally {
        cleanup();
        loadingMoreRef.current.delete(blockId);
        setLoadingMoreSourceIds((current) => current.filter((id) => id !== blockId));
        setLoadingProgress(null);
      }
    },
    [readDataBlocks],
  );

  const scheduleAutoRefresh = useCallback(
    (changedTargetIds: string[], targets: PreviewTarget[]) => {
      if (changedTargetIds.length === 0) return;
      // G5/G21: mark stale immediately — never present prior semantic payload as current.
      setStaleSourceIds((prev) => [...new Set([...prev, ...changedTargetIds])]);
      setResolvedByBlockId((previous) => {
        let changed = false;
        const next = { ...previous };
        for (const id of changedTargetIds) {
          const resolved = previous[id];
          if (!resolved || resolved.presentationStale === true) continue;
          const linked = resolved.linkedResolvedByBlockId;
          let nextLinked = linked;
          if (linked && typeof linked === "object") {
            nextLinked = {};
            for (const [blockId, entry] of Object.entries(linked)) {
              if (!entry || typeof entry !== "object") continue;
              nextLinked[blockId] = {
                ...entry,
                presentationStale: true,
                serverDisplayApplied: false,
                serverProjectionApplied: false,
              };
            }
          }
          next[id] = {
            ...resolved,
            presentationStale: true,
            serverDisplayApplied: false,
            serverProjectionApplied: false,
            ...(nextLinked ? { linkedResolvedByBlockId: nextLinked } : {}),
          };
          changed = true;
        }
        if (!changed) return previous;
        // Do not write stale-stripped map to session cache as authoritative.
        return next;
      });
      if (autoRefreshTimerRef.current != null) window.clearTimeout(autoRefreshTimerRef.current);
      autoRefreshTimerRef.current = window.setTimeout(() => {
        autoRefreshTimerRef.current = null;
        void fetchTargets(targets, {
          showLoading: false,
          targetIds: new Set(changedTargetIds),
          force: true,
        });
      }, DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS);
    },
    [fetchTargets],
  );

  // Fingerprint: auto-refresh das fontes/modelos afetados; carga inicial se ainda não há dados.
  useEffect(() => {
    const targets = readDataTargets();
    if (targets.length === 0) {
      setStaleSourceIds([]);
      setError(null);
      return;
    }

    const hasData = hasAnyResolved(resolvedRef.current, targets);
    const synced = syncedFingerprintRef.current;

    if (dataFingerprint !== synced) {
      if (hasData || didInitialFetchRef.current) {
        const sourceIds = planDataPreviewRefresh({
          previousFingerprint: synced,
          nextFingerprint: dataFingerprint,
          blocks: configRef.current.blocks,
        });
        const modelIds = planDataModelPreviewRefresh({
          previousFingerprint: synced,
          nextFingerprint: dataFingerprint,
          dataModels: configRef.current.dataModels,
        });
        const changedIds = [...new Set([...sourceIds, ...modelIds])];
        // Exclusão de visual / mudança sem impacto em dados: avança fingerprint sem fetch.
        if (changedIds.length === 0) {
          syncedFingerprintRef.current = dataFingerprint;
          setStaleSourceIds([]);
          return;
        }
        scheduleAutoRefresh(changedIds, targets);
        return;
      }
      didInitialFetchRef.current = true;
      void fetchTargets(targets, { showLoading: true, force: false });
      return;
    }

    setStaleSourceIds([]);
    if (hasData) {
      didInitialFetchRef.current = true;
      return;
    }
    if (!didInitialFetchRef.current) {
      didInitialFetchRef.current = true;
      void fetchTargets(targets, { showLoading: true, force: false });
    }
  }, [playlistId, dataFingerprint, fetchTargets, readDataTargets, scheduleAutoRefresh]);

  // Refresh periódico no editor: intervalo da programação (globalRefreshSec).
  // Add/delete e layout NÃO refetcham; encoding/filtros/Atualizar continuam no fingerprint.
  useEffect(() => {
    const targets = readDataTargets();
    if (targets.length === 0) return;
    const intervalSec = resolveDataBlockRefreshSec(undefined, globalRefreshSecRef.current);
    if (!Number.isFinite(intervalSec) || intervalSec <= 0) return;
    const timer = window.setInterval(() => {
      const current = readDataTargets();
      if (current.length === 0) return;
      // Não empilhar se já há lote em andamento.
      if (batchAbortRef.current) return;
      void fetchTargets(current, {
        showLoading: false,
        force: true,
      });
    }, intervalSec * 1000);
    return () => window.clearInterval(timer);
  }, [playlistId, fetchTargets, readDataTargets, globalRefreshSec]);

  const isDataPreviewStale = staleSourceIds.length > 0;

  const loadingProgressPercent = useMemo(() => {
    if (!loadingProgress || loadingProgress.total <= 0) return null;
    return Math.min(
      100,
      Math.round((loadingProgress.completed / loadingProgress.total) * 100),
    );
  }, [loadingProgress]);

  const loadingProgressLabel = useMemo(() => {
    if (!loadingProgress || loadingProgress.total <= 0) return null;
    return formatDataPreviewLoadingLabel(loadingProgress);
  }, [loadingProgress]);

  const clearStaleForSourceIds = useCallback((blockIds: string[]) => {
    if (blockIds.length === 0) return;
    const idSet = new Set(blockIds);
    setStaleSourceIds((prev) => prev.filter((id) => !idSet.has(id)));
  }, []);

  return {
    resolvedByBlockId,
    loading: initialLoading,
    error,
    isDataPreviewStale,
    staleSourceIds,
    refreshingSourceIds,
    loadingMoreSourceIds,
    /** Percentual real 0–100 enquanto há fetch; `null` quando ocioso. */
    loadingProgressPercent,
    /** Rótulo com fonte pendente / contagem (barra do palco). */
    loadingProgressLabel,
    refreshDataPreview,
    loadMoreDataPreview,
    clearStaleForSourceIds,
  };
}
