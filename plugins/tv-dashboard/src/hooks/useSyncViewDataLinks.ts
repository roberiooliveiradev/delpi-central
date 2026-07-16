import { useEffect, useMemo, useRef, type MutableRefObject } from "react";

import {
  isDataViewBlockType,
  syncDataViewBlocksWithResolved,
  viewHasProjectionConfigured,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataResolved,
} from "@delpi/tv-dashboard-presentation";

/**
 * Quando o preview da fonte chega (ou o visual é ligado sem projection),
 * materializa *Projection e dimensiona o frame — mesmo fluxo do link manual.
 */
export function useSyncViewDataLinks({
  configRef,
  blocks,
  resolvedByBlockId,
  commitBlocks,
}: {
  configRef: MutableRefObject<ComunicadoConfig>;
  /** Blocos persistidos do config (sem overlay de resolved). */
  blocks: ComunicadoBlock[];
  resolvedByBlockId: Record<string, ComunicadoDataResolved | undefined>;
  commitBlocks: (next: ComunicadoBlock[]) => void;
}) {
  const lastSyncKeyRef = useRef("");

  const pendingKey = useMemo(() => {
    return blocks
      .filter((block) => isDataViewBlockType(block.type))
      .map((block) => {
        const sourceId =
          "dataSourceId" in block && typeof block.dataSourceId === "string"
            ? block.dataSourceId.trim()
            : "";
        const hasResolved = Boolean(sourceId && resolvedByBlockId[sourceId]);
        const hasProj = viewHasProjectionConfigured(block);
        return `${block.id}:${sourceId}:${hasProj ? 1 : 0}:${hasResolved ? 1 : 0}:${block.frame.w}x${block.frame.h}`;
      })
      .sort()
      .join("|");
  }, [blocks, resolvedByBlockId]);

  useEffect(() => {
    const current = configRef.current.blocks ?? [];
    const { next, changedIds } = syncDataViewBlocksWithResolved(current, resolvedByBlockId);
    if (changedIds.length === 0) return;

    const syncKey = changedIds
      .map((id) => {
        const block = next.find((item) => item.id === id);
        if (!block || !("dataSourceId" in block)) return id;
        const frame = block.frame;
        const proj =
          block.type === "kpi_view"
            ? block.kpiProjection?.metrics?.map((m) => m.field).join(",")
            : block.type === "chart_view"
              ? block.chartProjection?.series?.map((s) => s.field).join(",")
              : block.type === "table_view"
                ? block.tableProjection?.columns?.map((c) => c.key).join(",")
                : "";
        return `${id}:${block.dataSourceId}:${proj}:${frame.w}x${frame.h}`;
      })
      .sort()
      .join("|");

    if (syncKey === lastSyncKeyRef.current) return;
    lastSyncKeyRef.current = syncKey;
    commitBlocks(next);
  }, [commitBlocks, configRef, pendingKey, resolvedByBlockId]);
}
