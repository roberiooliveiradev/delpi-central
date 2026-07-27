import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildDataPreviewFingerprint,
  isComunicadoInputBlock,
  isFetchableDataBlockType,
  mergeComunicadoDataPages,
  resolveComunicadoDataPageState,
  resolveDataBlockErrorText,
  resolveInputRefreshSourceIds,
  resolvePreviewRefreshSourceIds,
  serializeComunicadoConfig,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataBinding,
  type ComunicadoDataResolved,
} from "@delpi/tv-dashboard-presentation";

import { previewDataBlockV2 } from "../api/tvDashboardApi";
import {
  createLinkedTimeoutSignal,
  DATA_PREVIEW_BLOCK_TIMEOUT_MS,
  formatDataPreviewLoadingLabel,
  resolveDataSourceProgressLabel,
  resolvePreviewAbortMessage,
} from "../utils/dataPreviewFetchGuard";
import { readDataPreviewCache, writeDataPreviewCache } from "../utils/editorSessionCache";

export type RefreshDataPreviewOptions = {
  /** Bypass cache no servidor (clique em Atualizar visual). */
  force?: boolean;
  blockIds?: string[];
};

type Options = {
  playlistId: string;
  config: ComunicadoConfig;
};

type FetchableBlock = Extract<ComunicadoBlock, { dataBinding: ComunicadoDataBinding }>;

const DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS = 400;

function stripResolved(block: FetchableBlock): Record<string, unknown> {
  const { resolved: _resolved, ...blockPayload } = block;
  return blockPayload as Record<string, unknown>;
}

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
): Record<string, ComunicadoDataResolved> {
  const fingerprint = buildDataPreviewFingerprint(config);
  const fromSession = readDataPreviewCache(playlistId, fingerprint);
  const fromBlocks = seedFromConfigBlocks(config);
  return { ...fromSession, ...fromBlocks };
}

function hasAnyResolved(
  map: Record<string, ComunicadoDataResolved>,
  blocks: FetchableBlock[],
): boolean {
  return blocks.some((block) => map[block.id] !== undefined);
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
 * Preview de dados do editor — refetch automático quando filtros ou fontes mudam.
 * Botão «Atualizar visual» permanece para refresh manual com bypass de cache.
 * Cada fonte tem timeout; lote anterior é abortado ao iniciar um novo fetch.
 */
export function useComunicadoDataPreview({ playlistId, config }: Options) {
  const [resolvedByBlockId, setResolvedByBlockId] = useState<Record<string, ComunicadoDataResolved>>(
    () => initialResolvedMap(playlistId, config),
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

  const requestIdRef = useRef(0);
  const batchAbortRef = useRef<AbortController | null>(null);
  const resolvedRef = useRef(resolvedByBlockId);
  resolvedRef.current = resolvedByBlockId;
  const playlistIdRef = useRef(playlistId);
  const fingerprintRef = useRef(buildDataPreviewFingerprint(config));
  /** Fingerprint da última carga bem-sucedida (ou hidratada do session). */
  const syncedFingerprintRef = useRef(buildDataPreviewFingerprint(config));
  const didInitialFetchRef = useRef(false);
  const autoRefreshTimerRef = useRef<number | null>(null);
  const loadingMoreRef = useRef(new Set<string>());

  const dataFingerprint = useMemo(() => buildDataPreviewFingerprint(config), [config]);
  fingerprintRef.current = dataFingerprint;

  const readDataBlocks = useCallback(
    () =>
      (configRef.current.blocks ?? []).filter(
        (block): block is FetchableBlock =>
          isFetchableDataBlockType(block.type) && "dataBinding" in block,
      ),
    [],
  );

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
    const seeded = initialResolvedMap(playlistId, configRef.current);
    const fp = buildDataPreviewFingerprint(configRef.current);
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
        for (const [blockId, resolved] of pairs) {
          if (!resolved || typeof resolved !== "object") continue;
          const value = resolved as ComunicadoDataResolved;
          if (JSON.stringify(previous[blockId]) === JSON.stringify(value)) continue;
          next[blockId] = value;
          changed = true;
        }
        if (!changed) return previous;
        writeDataPreviewCache(playlistIdRef.current, fingerprintRef.current, next);
        return next;
      });
    },
    [],
  );

  const fetchBlocks = useCallback(
    async (
      blocks: FetchableBlock[],
      options: { showLoading: boolean; blockIds?: Set<string>; force?: boolean },
    ) => {
      if (blocks.length === 0) {
        setInitialLoading(false);
        setError(null);
        setLoadingProgress(null);
        return;
      }

      const targetIds = options.blockIds ?? new Set(blocks.map((block) => block.id));
      const targets = blocks.filter((block) => targetIds.has(block.id));
      const hasExistingData = targets.some(
        (block) => resolvedRef.current[block.id] !== undefined,
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

      const pendingIds = new Set(targets.map((block) => block.id));
      setLoadingProgress({
        completed: 0,
        total: targets.length,
        pendingLabels: targets.map(resolveDataSourceProgressLabel),
      });

      const nativeConfig = serializeComunicadoConfig(configRef.current);
      const fetchFingerprint = fingerprintRef.current;

      const bumpProgressById = (finishedId: string) => {
        if (requestIdRef.current !== requestId) return;
        pendingIds.delete(finishedId);
        setLoadingProgress({
          completed: targets.length - pendingIds.size,
          total: targets.length,
          pendingLabels: targets
            .filter((block) => pendingIds.has(block.id))
            .map(resolveDataSourceProgressLabel),
        });
      };

      try {
        const pairs = await Promise.all(
          targets.map(async (block) => {
            const { signal, cleanup } = createLinkedTimeoutSignal(
              DATA_PREVIEW_BLOCK_TIMEOUT_MS,
              batchAbort.signal,
            );
            try {
              const response = await previewDataBlockV2({
                block: stripResolved(block),
                nativeConfig,
                playlistId: playlistIdRef.current,
                forceRefresh: Boolean(options.force),
                signal,
              });
              const resolved = response.block?.resolved;
              if (resolved && typeof resolved === "object") {
                return [block.id, resolved] as const;
              }
              return [
                block.id,
                { error: "Resposta de preview sem dados resolvidos." },
              ] as const;
            } catch (err) {
              const superseded = requestIdRef.current !== requestId;
              const message = resolvePreviewAbortMessage(err, superseded);
              if (!message) {
                const previous = resolvedRef.current[block.id];
                return [
                  block.id,
                  previous ?? { error: "Carregamento cancelado." },
                ] as const;
              }
              return [block.id, { error: message }] as const;
            } finally {
              cleanup();
              bumpProgressById(block.id);
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
      const blocks = readDataBlocks();
      if (blocks.length === 0) {
        setStaleSourceIds([]);
        setError(null);
        return;
      }
      const blockIds = options?.blockIds?.length
        ? new Set(options.blockIds)
        : new Set(blocks.map((block) => block.id));
      await fetchBlocks(blocks, {
        showLoading: true,
        blockIds,
        force: options?.force !== false,
      });
    },
    [fetchBlocks, readDataBlocks],
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
        const response = await previewDataBlockV2({
          block: stripResolved(requestBlock),
          nativeConfig: serializeComunicadoConfig(configRef.current),
          playlistId: playlistIdRef.current,
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
    (sourceIds: string[], blocks: FetchableBlock[]) => {
      if (sourceIds.length === 0) return;
      if (autoRefreshTimerRef.current != null) window.clearTimeout(autoRefreshTimerRef.current);
      autoRefreshTimerRef.current = window.setTimeout(() => {
        autoRefreshTimerRef.current = null;
        void fetchBlocks(blocks, {
          showLoading: false,
          blockIds: new Set(sourceIds),
          force: true,
        });
      }, DATA_PREVIEW_AUTO_REFRESH_DEBOUNCE_MS);
    },
    [fetchBlocks],
  );

  // Fingerprint: auto-refresh das fontes afetadas; carga inicial se ainda não há dados.
  useEffect(() => {
    const blocks = readDataBlocks();
    if (blocks.length === 0) {
      setStaleSourceIds([]);
      setError(null);
      return;
    }

    const hasData = hasAnyResolved(resolvedRef.current, blocks);
    const synced = syncedFingerprintRef.current;

    if (dataFingerprint !== synced) {
      if (hasData || didInitialFetchRef.current) {
        const allFetchableIds = blocks.map((block) => block.id);
        const inputAffected = new Set<string>();
        for (const block of configRef.current.blocks ?? []) {
          if (!isComunicadoInputBlock(block)) continue;
          for (const id of resolveInputRefreshSourceIds(block, configRef.current.blocks)) {
            inputAffected.add(id);
          }
        }
        const sourceIds = resolvePreviewRefreshSourceIds({
          previousFingerprint: synced,
          nextFingerprint: dataFingerprint,
          allFetchableIds,
          inputAffectedSourceIds: [...inputAffected],
        });
        scheduleAutoRefresh(sourceIds, blocks);
        return;
      }
      didInitialFetchRef.current = true;
      void fetchBlocks(blocks, { showLoading: true, force: false });
      return;
    }

    setStaleSourceIds([]);
    if (hasData) {
      didInitialFetchRef.current = true;
      return;
    }
    if (!didInitialFetchRef.current) {
      didInitialFetchRef.current = true;
      void fetchBlocks(blocks, { showLoading: true, force: false });
    }
  }, [playlistId, dataFingerprint, fetchBlocks, readDataBlocks, scheduleAutoRefresh]);

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
