import { useEffect, useRef, useState } from "react";
import {
  isDataBlockType,
  serializeComunicadoConfig,
  type ComunicadoConfig,
  type ComunicadoDataResolved,
} from "@delpi/tv-dashboard-presentation";

import { previewDataBlockV2 } from "../api/tvDashboardApi";

type Options = {
  playlistId: string;
  config: ComunicadoConfig;
  debounceMs?: number;
};

export function useComunicadoDataPreview({
  playlistId,
  config,
  debounceMs = 650,
}: Options) {
  const [resolvedByBlockId, setResolvedByBlockId] = useState<Record<string, ComunicadoDataResolved>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    const dataBlocks = (config.blocks ?? []).filter((block) => isDataBlockType(block.type));
    if (dataBlocks.length === 0) {
      setResolvedByBlockId({});
      setLoading(false);
      setError(null);
      return;
    }

    const timer = window.setTimeout(() => {
      const requestId = ++requestIdRef.current;
      setLoading(true);
      setError(null);
      const nativeConfig = serializeComunicadoConfig(config);

      void (async () => {
        try {
          const pairs = await Promise.all(
            dataBlocks.map(async (block) => {
              const { resolved: _resolved, ...blockPayload } = block as typeof block & {
                resolved?: ComunicadoDataResolved;
              };
              const response = await previewDataBlockV2({
                block: blockPayload as Record<string, unknown>,
                nativeConfig,
                playlistId,
              });
              const resolved = response.block?.resolved;
              return [block.id, resolved] as const;
            }),
          );
          if (requestIdRef.current !== requestId) return;
          const next: Record<string, ComunicadoDataResolved> = {};
          for (const [blockId, resolved] of pairs) {
            if (resolved && typeof resolved === "object") {
              next[blockId] = resolved as ComunicadoDataResolved;
            }
          }
          setResolvedByBlockId(next);
        } catch (err) {
          if (requestIdRef.current !== requestId) return;
          setError(err instanceof Error ? err.message : "Falha ao carregar dados.");
          setResolvedByBlockId({});
        } finally {
          if (requestIdRef.current === requestId) {
            setLoading(false);
          }
        }
      })();
    }, debounceMs);

    return () => window.clearTimeout(timer);
  }, [playlistId, config, debounceMs]);

  return { resolvedByBlockId, loading, error };
}
