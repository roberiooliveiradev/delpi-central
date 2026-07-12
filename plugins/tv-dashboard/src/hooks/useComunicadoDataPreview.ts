import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildDataPreviewFingerprint,
  isFetchableDataBlockType,
  resolveDataBlockRefreshSec,
  serializeComunicadoConfig,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataBinding,
  type ComunicadoDataResolved,
} from "@delpi/tv-dashboard-presentation";

import { previewDataBlockV2 } from "../api/tvDashboardApi";
import { readDataPreviewCache, writeDataPreviewCache } from "../utils/editorSessionCache";

type Options = {
  playlistId: string;
  config: ComunicadoConfig;
  globalRefreshSec?: number;
  debounceMs?: number;
};

type FetchableBlock = Extract<ComunicadoBlock, { dataBinding: ComunicadoDataBinding }>;

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

/**
 * Preview de dados do editor — cache por blockId sobrevive à troca de slide e ao F5
 * (sessionStorage + equality no merge). Não zerar o mapa ao abrir um slide sem fontes.
 */
export function useComunicadoDataPreview({
  playlistId,
  config,
  globalRefreshSec,
  debounceMs = 650,
}: Options) {
  const [resolvedByBlockId, setResolvedByBlockId] = useState<Record<string, ComunicadoDataResolved>>(
    () => initialResolvedMap(playlistId, config),
  );
  const [initialLoading, setInitialLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const configRef = useRef(config);
  configRef.current = config;

  const requestIdRef = useRef(0);
  const resolvedRef = useRef(resolvedByBlockId);
  resolvedRef.current = resolvedByBlockId;
  const playlistIdRef = useRef(playlistId);
  const fingerprintRef = useRef(buildDataPreviewFingerprint(config));

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

  // Troca de playlist: recarrega seed da sessão; cache da playlist anterior não se aplica.
  useEffect(() => {
    if (playlistIdRef.current === playlistId) return;
    playlistIdRef.current = playlistId;
    const seeded = initialResolvedMap(playlistId, configRef.current);
    setResolvedByBlockId(seeded);
    setInitialLoading(false);
    setError(null);
    requestIdRef.current += 1;
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
    async (blocks: FetchableBlock[], options: { showLoading: boolean; blockIds?: Set<string> }) => {
      if (blocks.length === 0) {
        setInitialLoading(false);
        setError(null);
        return;
      }

      const targetIds = options.blockIds ?? new Set(blocks.map((block) => block.id));
      const targets = blocks.filter((block) => targetIds.has(block.id));
      const hasExistingData = targets.some(
        (block) => resolvedRef.current[block.id] !== undefined,
      );

      // Só banner/placeholder quando o palco ainda não tem nada para mostrar.
      if (options.showLoading && !hasExistingData) {
        setInitialLoading(true);
      }

      const requestId = ++requestIdRef.current;
      setError(null);

      const nativeConfig = serializeComunicadoConfig(configRef.current);

      try {
        const pairs = await Promise.all(
          targets.map(async (block) => {
            const response = await previewDataBlockV2({
              block: stripResolved(block),
              nativeConfig,
              playlistId: playlistIdRef.current,
            });
            const resolved = response.block?.resolved;
            return [block.id, resolved] as const;
          }),
        );

        if (requestIdRef.current !== requestId) return;

        mergeResolved(pairs);
      } catch (err) {
        if (requestIdRef.current !== requestId) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar dados.");
        // Mantém cache anterior nos blocos afetados — evita apagar o gráfico na tela.
      } finally {
        if (requestIdRef.current === requestId) {
          setInitialLoading(false);
        }
      }
    },
    [mergeResolved],
  );

  useEffect(() => {
    const blocks = readDataBlocks();
    if (blocks.length === 0) {
      // Slide sem fontes: não limpar resolved de outros slides (volta ao gráfico sem piscar).
      setInitialLoading(false);
      setError(null);
      return;
    }

    const timer = window.setTimeout(() => {
      void fetchBlocks(blocks, { showLoading: true });
    }, debounceMs);

    return () => window.clearTimeout(timer);
  }, [playlistId, dataFingerprint, debounceMs, fetchBlocks, readDataBlocks]);

  useEffect(() => {
    const blocks = readDataBlocks();
    if (blocks.length === 0) return;

    const timers = blocks.map((block) => {
      const refreshSec = resolveDataBlockRefreshSec(block.dataBinding, globalRefreshSec);
      return window.setInterval(() => {
        if (typeof document !== "undefined" && document.visibilityState === "hidden") return;
        const latest = readDataBlocks().find((item) => item.id === block.id);
        if (!latest) return;
        void fetchBlocks([latest], {
          showLoading: false,
          blockIds: new Set([block.id]),
        });
      }, refreshSec * 1000);
    });

    return () => {
      for (const timer of timers) {
        window.clearInterval(timer);
      }
    };
  }, [playlistId, dataFingerprint, globalRefreshSec, fetchBlocks, readDataBlocks]);

  return { resolvedByBlockId, loading: initialLoading, error };
}
