import { useCallback, useRef, useState, type MutableRefObject } from "react";

import {
  applyComplexBlockFrameWithTypography,
  isComplexViewBlock,
  isConnectorShapeBlock,
  isLineShapeKind,
  reconcileConnectorsAfterDrag,
  serializeComunicadoConfig,
  syncLineVerticesFromFrame,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoFrame,
} from "@delpi/tv-dashboard-presentation";

import type { DeckEditorHistoryContextValue } from "../../context/deckEditorHistoryContext";
import { useCanvasBlockInteraction } from "../../components/useCanvasBlockInteraction";
import { expandSelectionWithGroups } from "../../utils/comunicadoGrouping";
import { applyMultiFrameDelta } from "../../utils/multiFrameTransform";
import {
  peerFramesForSmartGuides,
  snapFrameToPeerBlocks,
  type SmartGuideLine,
} from "../../utils/comunicadoSmartGuides";
import { finalizeMultiFramesWithSnap } from "../../utils/finalizeMultiFramesWithSnap";
import { resolveStageTapWithoutDragAction } from "../../utils/stageInteractionPolicy";
import { stageGridSnapPercents } from "../../utils/stageGridSize";
import { snapshotConfig } from "./useComunicadoEditorHistory";

/** Janela para distinguir 2º toque (limpa) de clique duplo (isola / edita). */
export const TAP_DESELECT_DELAY_MS = 320;

type Options = {
  configRef: MutableRefObject<ComunicadoConfig>;
  selectedIds: string[];
  selectedId: string | null;
  applyConfig: (next: ComunicadoConfig) => void;
  pushPast: (snapshot: ComunicadoConfig) => void;
  deckHistory: DeckEditorHistoryContextValue | null;
  snapToGridRef: MutableRefObject<boolean>;
  snapToObjectsRef: MutableRefObject<boolean>;
  stageGridSizePercentRef: MutableRefObject<number>;
  clearSelection: () => void;
};

function resolveDraggedExcludeIds(
  multi: { startFrames: Map<string, ComunicadoFrame> } | null,
  blockId: string,
): Set<string> {
  if (multi && multi.startFrames.size > 0) {
    return new Set(multi.startFrames.keys());
  }
  return new Set([blockId]);
}

function resolveLiveSnapMode(
  baseline: ComunicadoBlock | undefined,
  frame: ComunicadoFrame,
): "move" | "resize" {
  if (!baseline) return "move";
  if (frame.w !== baseline.frame.w || frame.h !== baseline.frame.h) return "resize";
  return "move";
}

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
  snapToGridRef,
  snapToObjectsRef,
  stageGridSizePercentRef,
  clearSelection,
}: Options) {
  const dragSnapshotRef = useRef<ComunicadoConfig | null>(null);
  const multiDragRef = useRef<{ startFrames: Map<string, ComunicadoBlock["frame"]> } | null>(null);
  /** Seleção efetiva no pointerdown (evita race do React antes do threshold do drag). */
  const multiDragSelectionOverrideRef = useRef<string[] | null>(null);
  /** Segundo toque: limpa seleção se soltar sem cruzar o limiar de arraste. */
  const tapDeselectBlockIdRef = useRef<string | null>(null);
  const tapDeselectTimerRef = useRef<number | null>(null);
  const selectedIdsRef = useRef(selectedIds);
  selectedIdsRef.current = selectedIds;
  const [activeSmartGuides, setActiveSmartGuides] = useState<SmartGuideLine[]>([]);

  const armMultiDragSelection = useCallback((ids: string[]) => {
    multiDragSelectionOverrideRef.current = [...new Set(ids.filter(Boolean))];
  }, []);

  const armTapDeselect = useCallback((blockId: string | null) => {
    tapDeselectBlockIdRef.current = blockId;
  }, []);

  const cancelPendingTapDeselect = useCallback(() => {
    tapDeselectBlockIdRef.current = null;
    if (tapDeselectTimerRef.current != null) {
      window.clearTimeout(tapDeselectTimerRef.current);
      tapDeselectTimerRef.current = null;
    }
  }, []);

  const handleTapWithoutDrag = useCallback(
    (blockId: string) => {
      const candidate = tapDeselectBlockIdRef.current;
      tapDeselectBlockIdRef.current = null;
      if (!candidate || candidate !== blockId) return;
      const action = resolveStageTapWithoutDragAction({
        blocks: configRef.current.blocks ?? [],
        selectedIds: selectedIdsRef.current,
        targetBlockId: blockId,
        wasAlreadySelected: true,
      });
      /* isolate-child: o pointerdown já isolou; não limpar. */
      if (action.type !== "clear-selection") return;
      /*
       * Atrasa a limpeza para não roubar o 1º clique de um clique duplo
       * (isolar subitem / editar texto).
       */
      if (tapDeselectTimerRef.current != null) {
        window.clearTimeout(tapDeselectTimerRef.current);
      }
      tapDeselectTimerRef.current = window.setTimeout(() => {
        tapDeselectTimerRef.current = null;
        clearSelection();
      }, TAP_DESELECT_DELAY_MS);
    },
    [clearSelection, configRef],
  );
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

  const resolveBaseline = useCallback((blockId: string): ComunicadoBlock | undefined => {
    return dragSnapshotRef.current?.blocks?.find((block) => block.id === blockId);
  }, []);

  const handleUpdateFrame = useCallback(
    (blockId: string, frame: ComunicadoBlock["frame"]) => {
      const multi = multiDragRef.current;
      const baseline = resolveBaseline(blockId);
      const excludeIds = resolveDraggedExcludeIds(multi, blockId);
      let workingFrame = frame;
      let guides: SmartGuideLine[] = [];

      if (snapToObjectsRef.current) {
        const peers = peerFramesForSmartGuides(configRef.current.blocks ?? [], excludeIds);
        const mode = resolveLiveSnapMode(baseline, frame);
        const snapped = snapFrameToPeerBlocks(workingFrame, peers, mode);
        workingFrame = snapped.frame;
        guides = snapped.guides;
      }
      setActiveSmartGuides(guides);

      let nextBlocks: ComunicadoBlock[];
      const draggedIds = new Set<string>();

      if (multi && multi.startFrames.has(blockId)) {
        const nextFrames = applyMultiFrameDelta(multi.startFrames, blockId, workingFrame);
        nextBlocks = (configRef.current.blocks ?? []).map((block) => {
          const nextFrame = nextFrames.get(block.id);
          if (!nextFrame) return block;
          draggedIds.add(block.id);
          const base = resolveBaseline(block.id) ?? block;
          const start = multi.startFrames.get(block.id)!;
          const isResize = nextFrame.w !== start.w || nextFrame.h !== start.h;
          if (isResize && isComplexViewBlock(base)) {
            return applyComplexBlockFrameWithTypography(base, nextFrame);
          }
          return { ...block, frame: nextFrame };
        });
      } else {
        draggedIds.add(blockId);
        nextBlocks = (configRef.current.blocks ?? []).map((block) => {
          if (block.id !== blockId) return block;
          const base = baseline ?? block;
          const isResize =
            workingFrame.w !== base.frame.w || workingFrame.h !== base.frame.h;
          if (isResize && isComplexViewBlock(base)) {
            return applyComplexBlockFrameWithTypography(base, workingFrame);
          }
          return { ...block, frame: workingFrame };
        });
      }
      updateBlocksSilent(reconcileConnectorsAfterDrag(nextBlocks, draggedIds));
    },
    [configRef, resolveBaseline, snapToObjectsRef, updateBlocksSilent],
  );

  const handleInteractionStart = useCallback(() => {
    cancelPendingTapDeselect();
    setActiveSmartGuides([]);
    dragSnapshotRef.current = snapshotConfig(configRef.current);
    const override = multiDragSelectionOverrideRef.current;
    multiDragSelectionOverrideRef.current = null;
    const baseIds =
      override && override.length > 0
        ? override
        : selectedIds.length > 0
          ? selectedIds
          : selectedId
            ? [selectedId]
            : [];
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
  }, [cancelPendingTapDeselect, configRef, selectedId, selectedIds]);

  const handleInteractionEnd = useCallback(
    (blockId: string, _frame: ComunicadoBlock["frame"], mode: "move" | "resize" | "rotate" | "adjust") => {
      setActiveSmartGuides([]);
      const before = dragSnapshotRef.current;
      dragSnapshotRef.current = null;
      const multi = multiDragRef.current;
      multiDragRef.current = null;
      if (!before) return;

      const recordGestureHistory = () => {
        pushPast(before);
        deckHistory?.recordBeforeChange(serializeComunicadoConfig(before));
      };

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
        recordGestureHistory();
        applyConfig(configRef.current);
        return;
      }

      const idsToFinalize =
        multi && multi.startFrames.size > 1
          ? [...multi.startFrames.keys()]
          : [blockId];

      let nextBlocks = [...(configRef.current.blocks ?? [])];
      const draggedIds = new Set(idsToFinalize);
      const snapMode = mode === "resize" ? "resize" : "move";
      const snapPercents = stageGridSnapPercents(stageGridSizePercentRef.current);
      const startFrames = new Map<string, ComunicadoBlock["frame"]>();
      const currentById = new Map<string, ComunicadoBlock["frame"]>();
      for (const id of idsToFinalize) {
        const beforeBlock = before.blocks?.find((block) => block.id === id);
        const current = nextBlocks.find((block) => block.id === id);
        if (beforeBlock) startFrames.set(id, { ...beforeBlock.frame });
        if (current) currentById.set(id, { ...current.frame });
      }
      /*
       * Snap a objetos já roda no live. No fim: grade/clamp no primário e
       * delta aos irmãos — evita encaixar cada membro e desalinhhar o grupo.
       */
      const snappedById = finalizeMultiFramesWithSnap({
        blocks: nextBlocks,
        ids: idsToFinalize,
        primaryId: blockId,
        startFrames,
        currentById,
        mode: snapMode,
        snapToGrid: snapToGridRef.current,
        snapPercents,
      });

      for (const id of idsToFinalize) {
        const index = nextBlocks.findIndex((block) => block.id === id);
        if (index < 0) continue;
        const current = nextBlocks[index];
        const beforeBlock = before.blocks?.find((block) => block.id === id);
        const snappedFrame = snappedById.get(id) ?? current.frame;

        let updated: ComunicadoBlock;
        if (mode === "resize" && beforeBlock && isComplexViewBlock(beforeBlock)) {
          /* Sempre baseline do início — tipografia live já tipificada; snap reescala do zero. */
          updated = applyComplexBlockFrameWithTypography(beforeBlock, snappedFrame);
        } else {
          updated = { ...current, frame: snappedFrame };
        }

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

      recordGestureHistory();
      applyConfig(nextConfig);
    },
    [
      applyConfig,
      configRef,
      deckHistory,
      pushPast,
      snapToGridRef,
      stageGridSizePercentRef,
    ],
  );

  const clearDragSnapshot = useCallback(() => {
    dragSnapshotRef.current = null;
    multiDragSelectionOverrideRef.current = null;
    cancelPendingTapDeselect();
    setActiveSmartGuides([]);
  }, [cancelPendingTapDeselect]);

  const { canvasRef, startDrag } = useCanvasBlockInteraction({
    onUpdateFrame: handleUpdateFrame,
    onUpdateStyle: handleUpdateStyle,
    onUpdateBlock: handleUpdateBlock,
    onInteractionStart: handleInteractionStart,
    onInteractionEnd: handleInteractionEnd,
    onTapWithoutDrag: handleTapWithoutDrag,
    resolveBlock: (blockId) => configRef.current.blocks?.find((block) => block.id === blockId),
  });

  return {
    canvasRef,
    startDrag,
    clearDragSnapshot,
    armMultiDragSelection,
    armTapDeselect,
    cancelPendingTapDeselect,
    activeSmartGuides,
  };
}
