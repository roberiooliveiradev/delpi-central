import { useCallback, useRef, type MutableRefObject } from "react";

import {
  clampFrameForBlock,
  isConnectorShapeBlock,
  isLineShapeKind,
  reconcileConnectorsAfterDrag,
  serializeComunicadoConfig,
  syncLineVerticesFromFrame,
  type ComunicadoBlock,
  type ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import type { DeckEditorHistoryContextValue } from "../../context/deckEditorHistoryContext";
import { useCanvasBlockInteraction } from "../../components/useCanvasBlockInteraction";
import { expandSelectionWithGroups } from "../../utils/comunicadoGrouping";
import { snapComunicadoFrame } from "../../utils/comunicadoSnap";
import { stageGridSnapPercents } from "../../utils/stageGridSize";
import { snapshotConfig } from "./useComunicadoEditorHistory";

type Options = {
  configRef: MutableRefObject<ComunicadoConfig>;
  selectedIds: string[];
  selectedId: string | null;
  applyConfig: (next: ComunicadoConfig) => void;
  pushPast: (snapshot: ComunicadoConfig) => void;
  deckHistory: DeckEditorHistoryContextValue | null;
  snapEnabledRef: MutableRefObject<boolean>;
  stageGridSizePercentRef: MutableRefObject<number>;
};

/**
 * Drag / resize / rotate no palco — handlers + `useCanvasBlockInteraction`.
 */
export function useComunicadoEditorDrag({
  configRef,
  selectedIds,
  selectedId,
  applyConfig,
  pushPast,
  deckHistory,
  snapEnabledRef,
  stageGridSizePercentRef,
}: Options) {
  const dragSnapshotRef = useRef<ComunicadoConfig | null>(null);
  const multiDragRef = useRef<{ startFrames: Map<string, ComunicadoBlock["frame"]> } | null>(null);

  const updateBlocksSilent = useCallback(
    (nextBlocks: ComunicadoBlock[]) => {
      applyConfig({ ...configRef.current, blocks: nextBlocks });
    },
    [applyConfig, configRef],
  );

  const handleUpdateStyle = useCallback(
    (blockId: string, patch: NonNullable<ComunicadoBlock["style"]>) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId
          ? ({ ...block, style: { ...block.style, ...patch } } as ComunicadoBlock)
          : block,
      );
      updateBlocksSilent(nextBlocks);
    },
    [configRef, updateBlocksSilent],
  );

  const handleUpdateBlock = useCallback(
    (blockId: string, patch: Partial<ComunicadoBlock>) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        if (block.id !== blockId) return block;
        const next = { ...block, ...patch } as ComunicadoBlock;
        if (patch.style) {
          next.style = { ...block.style, ...patch.style };
        }
        return next;
      });
      updateBlocksSilent(nextBlocks);
    },
    [configRef, updateBlocksSilent],
  );

  const handleUpdateFrame = useCallback(
    (blockId: string, frame: ComunicadoBlock["frame"]) => {
      const multi = multiDragRef.current;
      let nextBlocks: ComunicadoBlock[];
      const draggedIds = new Set<string>();
      if (multi && multi.startFrames.has(blockId)) {
        const origin = multi.startFrames.get(blockId);
        if (!origin) return;
        const dx = frame.x - origin.x;
        const dy = frame.y - origin.y;
        const isResize = frame.w !== origin.w || frame.h !== origin.h;
        nextBlocks = (configRef.current.blocks ?? []).map((block) => {
          if (!multi.startFrames.has(block.id)) return block;
          draggedIds.add(block.id);
          const start = multi.startFrames.get(block.id)!;
          if (block.id === blockId && isResize) {
            return { ...block, frame };
          }
          return {
            ...block,
            frame: {
              ...start,
              x: start.x + dx,
              y: start.y + dy,
              w: start.w,
              h: start.h,
            },
          };
        });
      } else {
        draggedIds.add(blockId);
        nextBlocks = (configRef.current.blocks ?? []).map((block) =>
          block.id === blockId ? { ...block, frame } : block,
        );
      }
      updateBlocksSilent(reconcileConnectorsAfterDrag(nextBlocks, draggedIds));
    },
    [configRef, updateBlocksSilent],
  );

  const handleInteractionStart = useCallback(() => {
    dragSnapshotRef.current = snapshotConfig(configRef.current);
    const baseIds = selectedIds.length > 0 ? selectedIds : selectedId ? [selectedId] : [];
    const activeIds = expandSelectionWithGroups(configRef.current.blocks ?? [], baseIds);
    if (activeIds.length > 1) {
      const startFrames = new Map<string, ComunicadoBlock["frame"]>();
      for (const id of activeIds) {
        const block = configRef.current.blocks?.find((item) => item.id === id);
        if (block) startFrames.set(id, { ...block.frame });
      }
      multiDragRef.current = { startFrames };
    } else {
      multiDragRef.current = null;
    }
  }, [configRef, selectedId, selectedIds]);

  const handleInteractionEnd = useCallback(
    (blockId: string, _frame: ComunicadoBlock["frame"], mode: "move" | "resize" | "rotate" | "adjust") => {
      const before = dragSnapshotRef.current;
      dragSnapshotRef.current = null;
      const multi = multiDragRef.current;
      multiDragRef.current = null;
      if (!before) return;

      if (mode === "rotate" || mode === "adjust") {
        const beforeBlock = before.blocks?.find((block) => block.id === blockId);
        const afterBlock = configRef.current.blocks?.find((block) => block.id === blockId);
        const unchanged =
          mode === "rotate"
            ? (beforeBlock?.style?.rotation ?? 0) === (afterBlock?.style?.rotation ?? 0)
            : JSON.stringify({
                style: beforeBlock?.style,
                kpiParts: beforeBlock && "kpiParts" in beforeBlock ? beforeBlock.kpiParts : null,
                chartParts:
                  beforeBlock && "chartParts" in beforeBlock ? beforeBlock.chartParts : null,
              }) ===
              JSON.stringify({
                style: afterBlock?.style,
                kpiParts: afterBlock && "kpiParts" in afterBlock ? afterBlock.kpiParts : null,
                chartParts: afterBlock && "chartParts" in afterBlock ? afterBlock.chartParts : null,
              });
        if (unchanged) {
          applyConfig(configRef.current);
          return;
        }
        if (deckHistory) {
          deckHistory.recordBeforeChange(serializeComunicadoConfig(before));
        } else {
          pushPast(before);
        }
        applyConfig(configRef.current);
        return;
      }

      const idsToFinalize =
        multi && multi.startFrames.size > 1
          ? [...multi.startFrames.keys()]
          : [blockId];

      let nextBlocks = [...(configRef.current.blocks ?? [])];
      const draggedIds = new Set(idsToFinalize);
      for (const id of idsToFinalize) {
        const index = nextBlocks.findIndex((block) => block.id === id);
        if (index < 0) continue;
        const current = nextBlocks[index];
        const snapMode = mode === "resize" ? "resize" : "move";
        const snapPercents = stageGridSnapPercents(stageGridSizePercentRef.current);
        const snappedFrame = snapEnabledRef.current
          ? snapComunicadoFrame(current, current.frame, snapMode, snapPercents)
          : clampFrameForBlock(current, current.frame);
        let updated: ComunicadoBlock = { ...current, frame: snappedFrame };
        if (
          updated.type === "shape" &&
          isLineShapeKind(updated.shape) &&
          !isConnectorShapeBlock(updated) &&
          mode === "resize"
        ) {
          updated = {
            ...updated,
            vertices: syncLineVerticesFromFrame(updated, snappedFrame),
          };
        }
        nextBlocks[index] = updated;
      }
      nextBlocks = reconcileConnectorsAfterDrag(nextBlocks, draggedIds);

      const nextConfig = { ...configRef.current, blocks: nextBlocks };
      const unchanged = idsToFinalize.every((id) => {
        const beforeBlock = before.blocks?.find((block) => block.id === id);
        const afterBlock = nextBlocks.find((block) => block.id === id);
        if (!beforeBlock || !afterBlock) return true;
        return (
          beforeBlock.frame.x === afterBlock.frame.x &&
          beforeBlock.frame.y === afterBlock.frame.y &&
          beforeBlock.frame.w === afterBlock.frame.w &&
          beforeBlock.frame.h === afterBlock.frame.h
        );
      });

      if (unchanged) {
        applyConfig(nextConfig);
        return;
      }

      if (deckHistory) {
        deckHistory.recordBeforeChange(serializeComunicadoConfig(before));
      } else {
        pushPast(before);
      }
      applyConfig(nextConfig);
    },
    [applyConfig, configRef, deckHistory, pushPast, snapEnabledRef, stageGridSizePercentRef],
  );

  const clearDragSnapshot = useCallback(() => {
    dragSnapshotRef.current = null;
  }, []);

  const { canvasRef, startDrag } = useCanvasBlockInteraction({
    onUpdateFrame: handleUpdateFrame,
    onUpdateStyle: handleUpdateStyle,
    onUpdateBlock: handleUpdateBlock,
    onInteractionStart: handleInteractionStart,
    onInteractionEnd: handleInteractionEnd,
    resolveBlock: (blockId) => configRef.current.blocks?.find((block) => block.id === blockId),
  });

  return {
    canvasRef,
    startDrag,
    clearDragSnapshot,
  };
}
