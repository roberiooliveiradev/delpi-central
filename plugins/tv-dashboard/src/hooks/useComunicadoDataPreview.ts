import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  buildDataPreviewFingerprint,
  isDataBlockType,
  resolveDataBlockRefreshSec,
  serializeComunicadoConfig,
  type ComunicadoConfig,
  type ComunicadoDataBlock,
  type ComunicadoDataResolved,
} from "@delpi/tv-dashboard-presentation";

import { previewDataBlockV2 } from "../api/tvDashboardApi";

type Options = {
  playlistId: string;
  config: ComunicadoConfig;
  globalRefreshSec?: number;
  debounceMs?: number;
};

function stripResolved(block: ComunicadoDataBlock): Record<string, unknown> {
  const { resolved: _resolved, ...blockPayload } = block as ComunicadoDataBlock & {
    resolved?: ComunicadoDataResolved;
  };
  return blockPayload as Record<string, unknown>;
}

export function useComunicadoDataPreview({
  playlistId,
  config,
  globalRefreshSec,
  debounceMs = 650,
}: Options) {
  const [resolvedByBlockId, setResolvedByBlockId] = useState<Record<string, ComunicadoDataResolved>>({});
  const [initialLoading, setInitialLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const configRef = useRef(config);
  configRef.current = config;

  const requestIdRef = useRef(0);
  const resolvedRef = useRef(resolvedByBlockId);
  resolvedRef.current = resolvedByBlockId;

  const dataFingerprint = useMemo(() => buildDataPreviewFingerprint(config), [config]);

  const readDataBlocks = useCallback(
    () =>
      (configRef.current.blocks ?? []).filter((block): block is ComunicadoDataBlock =>
        isDataBlockType(block.type),
      ),
    [],
  );

  const fetchBlocks = useCallback(
    async (blocks: ComunicadoDataBlock[], options: { showLoading: boolean; blockIds?: Set<string> }) => {
      if (blocks.length === 0) {
        setResolvedByBlockId({});
        setInitialLoading(false);
        setError(null);
        return;
      }

      const targetIds = options.blockIds ?? new Set(blocks.map((block) => block.id));
      const hasExistingData = blocks.some(
        (block) => targetIds.has(block.id) && resolvedRef.current[block.id] !== undefined,
      );

      if (options.showLoading && !hasExistingData) {
        setInitialLoading(true);
      }

      const requestId = ++requestIdRef.current;
      setError(null);

      const nativeConfig = serializeComunicadoConfig(configRef.current);

      try {
        const pairs = await Promise.all(
          blocks
            .filter((block) => targetIds.has(block.id))
            .map(async (block) => {
              const response = await previewDataBlockV2({
                block: stripResolved(block),
                nativeConfig,
                playlistId,
              });
              const resolved = response.block?.resolved;
              return [block.id, resolved] as const;
            }),
        );

        if (requestIdRef.current !== requestId) return;

        setResolvedByBlockId((previous) => {
          const next = { ...previous };
          for (const [blockId, resolved] of pairs) {
            if (resolved && typeof resolved === "object") {
              next[blockId] = resolved as ComunicadoDataResolved;
            }
          }
          return next;
        });
      } catch (err) {
        if (requestIdRef.current !== requestId) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar dados.");
        if (!hasExistingData) {
          setResolvedByBlockId({});
        }
      } finally {
        if (requestIdRef.current === requestId) {
          setInitialLoading(false);
        }
      }
    },
    [playlistId],
  );

  useEffect(() => {
    const blocks = readDataBlocks();
    if (blocks.length === 0) {
      setResolvedByBlockId({});
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
