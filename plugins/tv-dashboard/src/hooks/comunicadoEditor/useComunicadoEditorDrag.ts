import { useCallback, useRef, type MutableRefObject } from "react";

import {
  clampFrameForBlock,
  isLineShapeKind,
  serializeComunicadoConfig,
  syncLineVerticesFromFrame,
  type ComunicadoBlock,
  type ComunicadoConfig,
} from "@delpi/tv-dashboard-presentation";

import type { DeckEditorHistoryContextValue } from "../../context/deckEditorHistoryContext";
import { useCanvasBlockInteraction } from "../../components/useCanvasBlockInteraction";
import { expandSelectionWithGroups } from "../../utils/comunicadoGrouping";
import { snapComunicadoFrame } from "../../utils/comunicadoSnap";
import { snapshotConfig } from "./useComunicadoEditorHistory";

type Options = {
  configRef: MutableRefObject<ComunicadoConfig>;
  selectedIds: string[];
  selectedId: string | null;
  applyConfig: (next: ComunicadoConfig) => void;
  pushPast: (snapshot: ComunicadoConfig) => void;
  deckHistory: DeckEditorHistoryContextValue | null;
  snapEnabledRef: MutableRefObject<boolean>;
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

  const handleUpdateFrame = useCallback(
    (blockId: string, frame: ComunicadoBlock["frame"]) => {
      const multi = multiDragRef.current;
      if (multi && multi.startFrames.has(blockId)) {
        const origin = multi.startFrames.get(blockId);
        if (!origin) return;
        const dx = frame.x - origin.x;
        const dy = frame.y - origin.y;
        const isResize = frame.w !== origin.w || frame.h !== origin.h;
        const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
          if (!multi.startFrames.has(block.id)) return block;
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
        updateBlocksSilent(nextBlocks);
        return;
      }
      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId ? { ...block, frame } : block,
      );
      updateBlocksSilent(nextBlocks);
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

      if (mode === "rotate") {
        const beforeBlock = before.blocks?.find((block) => block.id === blockId);
        const afterBlock = configRef.current.blocks?.find((block) => block.id === blockId);
        const unchanged =
          (beforeBlock?.style?.rotation ?? 0) === (afterBlock?.style?.rotation ?? 0);
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
      for (const id of idsToFinalize) {
        const index = nextBlocks.findIndex((block) => block.id === id);
        if (index < 0) continue;
        const current = nextBlocks[index];
        const snapMode = mode === "resize" ? "resize" : "move";
        const snappedFrame = snapEnabledRef.current
          ? snapComunicadoFrame(current, current.frame, snapMode)
          : clampFrameForBlock(current, current.frame);
        let updated: ComunicadoBlock = { ...current, frame: snappedFrame };
        if (
          updated.type === "shape" &&
          isLineShapeKind(updated.shape) &&
          mode === "resize"
        ) {
          updated = {
            ...updated,
            vertices: syncLineVerticesFromFrame(updated, snappedFrame),
          };
        }
        nextBlocks[index] = updated;
      }

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
    [applyConfig, configRef, deckHistory, pushPast, snapEnabledRef],
  );

  const clearDragSnapshot = useCallback(() => {
    dragSnapshotRef.current = null;
  }, []);

  const { canvasRef, startDrag } = useCanvasBlockInteraction({
    onUpdateFrame: handleUpdateFrame,
    onUpdateStyle: handleUpdateStyle,
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
