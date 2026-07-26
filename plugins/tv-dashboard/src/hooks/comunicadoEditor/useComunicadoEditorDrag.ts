import { useCallback, useRef, useState, type MutableRefObject } from "react";

import {
  applyComplexBlockFrameWithTypography,
  clampFrameForBlock,
  isComplexViewBlock,
  isLineShapeKind,
  reconcileConnectorsAfterDrag,
  serializeComunicadoConfig,
  translateLineEndpoints,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoFrame,
  type ComunicadoShapeBlock,
} from "@delpi/tv-dashboard-presentation";

import type { DeckEditorHistoryContextValue } from "../../context/deckEditorHistoryContext";
import {
  useCanvasBlockInteraction,
  type ConnectionSitesPreview,
} from "../../components/useCanvasBlockInteraction";
import { normalizeResizeHandle } from "../../utils/resizeFrameAspect";
import {
  peerFramesForSmartGuides,
  snapFrameToPeerBlocks,
  type SmartGuideLine,
} from "../../utils/comunicadoSmartGuides";
import { finalizeMultiFramesWithSnap } from "../../utils/finalizeMultiFramesWithSnap";
import { snapComunicadoFrame } from "../../utils/comunicadoSnap";
import {
  applyGroupMove,
  applyGroupRotate,
  applyGroupScale,
  beginGroupGesture,
  resolveWorldFrames,
  type StageGroupGesture,
} from "../../utils/stageGroupGesture";
import { resolveMultiDragBlockIds } from "../../utils/stageGroupedSelection";
import { resolveStageTapWithoutDragAction } from "../../utils/stageInteractionPolicy";
import { stageGridSnapPercents } from "../../utils/stageGridSize";
import { snapshotConfig } from "./useComunicadoEditorHistory";

/** Janela para distinguir 2º toque (limpa) de clique duplo (isola / edita). */
export const TAP_DESELECT_DELAY_MS = 320;

type Options = {
  configRef: MutableRefObject<ComunicadoConfig>;
  selectedIds: string[];
  selectedId: string | null;
  applyConfig: (next: ComunicadoConfig, options?: { persist?: boolean }) => void;
  pushPast: (snapshot: ComunicadoConfig) => void;
  deckHistory: DeckEditorHistoryContextValue | null;
  snapToGridRef: MutableRefObject<boolean>;
  snapToObjectsRef: MutableRefObject<boolean>;
  stageGridSizePercentRef: MutableRefObject<number>;
  clearSelection: () => void;
  /** Largura/altura do palco (design) — órbita de rotação em grupo. */
  getSlideAspectRatio: () => number;
};

function resolveDraggedExcludeIds(
  gesture: StageGroupGesture | null,
  blockId: string,
): Set<string> {
  if (gesture && gesture.memberIds.length > 0) {
    return new Set(gesture.memberIds);
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

function applyWorldUpdatesToBlocks(input: {
  blocks: ComunicadoBlock[];
  updates: Map<string, { frame: ComunicadoFrame; rotation: number }>;
  resolveBaseline: (id: string) => ComunicadoBlock | undefined;
  childExtent: ComunicadoFrame;
  groupFrame: ComunicadoFrame;
}): ComunicadoBlock[] {
  const { blocks, updates, resolveBaseline, childExtent, groupFrame } = input;
  const scaleX = childExtent.w > 0 ? groupFrame.w / childExtent.w : 1;
  const scaleY = childExtent.h > 0 ? groupFrame.h / childExtent.h : 1;
  const scaled =
    Math.abs(scaleX - 1) > 1e-6 || Math.abs(scaleY - 1) > 1e-6;

  return blocks.map((block) => {
    const update = updates.get(block.id);
    if (!update) return block;
    const base = resolveBaseline(block.id) ?? block;
    let next: ComunicadoBlock = {
      ...block,
      frame: update.frame,
      style: { ...block.style, rotation: update.rotation },
    } as ComunicadoBlock;
    if (scaled && isComplexViewBlock(base)) {
      next = applyComplexBlockFrameWithTypography(base, update.frame);
      next = {
        ...next,
        style: { ...next.style, rotation: update.rotation },
      } as ComunicadoBlock;
    }
    return next;
  });
}

/**
 * Drag / resize / rotate no palco — handlers + `useCanvasBlockInteraction`.
 * Multi/grupo N>1: único pipeline `stageGroupGesture` (live ≡ release).
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
  getSlideAspectRatio,
}: Options) {
  const getSlideAspectRatioRef = useRef(getSlideAspectRatio);
  getSlideAspectRatioRef.current = getSlideAspectRatio;
  const dragSnapshotRef = useRef<ComunicadoConfig | null>(null);
  const groupGestureRef = useRef<StageGroupGesture | null>(null);
  /** Preview DOM rígido: um container transformado; bake nos blocos só no pointerup. */
  const [activeGroupGesture, setActiveGroupGesture] =
    useState<StageGroupGesture | null>(null);
  /** Seleção efetiva no pointerdown (evita race do React antes do threshold do drag). */
  const multiDragSelectionOverrideRef = useRef<string[] | null>(null);
  /** Segundo toque: limpa seleção se soltar sem cruzar o limiar de arraste. */
  const tapDeselectBlockIdRef = useRef<string | null>(null);
  const tapDeselectTimerRef = useRef<number | null>(null);
  const selectedIdsRef = useRef(selectedIds);
  selectedIdsRef.current = selectedIds;
  const [activeSmartGuides, setActiveSmartGuides] = useState<SmartGuideLine[]>([]);
  const [connectionSitesPreview, setConnectionSitesPreview] =
    useState<ConnectionSitesPreview | null>(null);

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
      /* Preview local do gesto — autosave só no pointerup (handleInteractionEnd). */
      applyConfig({ ...configRef.current, blocks: nextBlocks }, { persist: false });
    },
    [applyConfig, configRef],
  );

  const previewGroupGesture = useCallback((gesture: StageGroupGesture) => {
    /*
     * Não materializar world frames no live. Fazer isso aplicava `rotate()` em
     * cada membro, cada um no próprio centro. O DOM recebe um GroupTransform
     * único e os frames world são materializados somente no pointerup.
     */
    setActiveGroupGesture(gesture);
  }, []);

  const handleUpdateStyle = useCallback(
    (blockId: string, patch: NonNullable<ComunicadoBlock["style"]>) => {
      const gesture = groupGestureRef.current;
      if (gesture && typeof patch.rotation === "number" && gesture.localFrames.has(blockId)) {
        /*
         * patch = interactionStartRotation + delta do pointer.
         * group.rotation = startGroupRotation + mesmo delta (chrome ou membro).
         */
        const pointerDelta = patch.rotation - gesture.interactionStartRotation;
        const next = applyGroupRotate(
          gesture,
          gesture.startGroupRotation + pointerDelta,
        );
        groupGestureRef.current = next;
        previewGroupGesture(next);
        return;
      }

      const nextBlocks = (configRef.current.blocks ?? []).map((block) =>
        block.id === blockId
          ? ({ ...block, style: { ...block.style, ...patch } } as ComunicadoBlock)
          : block,
      );
      updateBlocksSilent(nextBlocks);
    },
    [configRef, previewGroupGesture, updateBlocksSilent],
  );

  const handleUpdateBlock = useCallback(
    (blockId: string, patch: Partial<ComunicadoBlock>) => {
      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        if (block.id !== blockId) return block;
        const next = { ...block, ...patch } as ComunicadoBlock;
        if (patch.style) {
          next.style = { ...block.style, ...patch.style };
        }
        if ("connector" in patch && patch.connector === undefined && next.type === "shape") {
          delete (next as ComunicadoShapeBlock).connector;
        }
        return next;
      });
      /* Endpoint drag: não detach via reconcile — attach/detach parcial já veio no patch. */
      updateBlocksSilent(nextBlocks);
    },
    [configRef, updateBlocksSilent],
  );

  const resolveBaseline = useCallback((blockId: string): ComunicadoBlock | undefined => {
    return dragSnapshotRef.current?.blocks?.find((block) => block.id === blockId);
  }, []);

  const handleUpdateFrame = useCallback(
    (blockId: string, frame: ComunicadoBlock["frame"]) => {
      const gesture = groupGestureRef.current;
      const baseline = resolveBaseline(blockId);
      const excludeIds = resolveDraggedExcludeIds(gesture, blockId);
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

      if (gesture && gesture.localFrames.has(blockId)) {
        const startRef = gesture.interactionStartFrame;
        const isResize =
          workingFrame.w !== startRef.w || workingFrame.h !== startRef.h;
        const next = isResize
          ? applyGroupScale(gesture, workingFrame, { lockAspect: true })
          : applyGroupMove(gesture, workingFrame);
        groupGestureRef.current = next;
        previewGroupGesture(next);
        return;
      }

      const draggedIds = new Set<string>([blockId]);
      const nextBlocks = (configRef.current.blocks ?? []).map((block) => {
        if (block.id !== blockId) return block;
        const base = baseline ?? block;
        const isResize =
          workingFrame.w !== base.frame.w || workingFrame.h !== base.frame.h;
        if (isResize && isComplexViewBlock(base)) {
          return applyComplexBlockFrameWithTypography(base, workingFrame);
        }
        if (
          base.type === "shape" &&
          isLineShapeKind(base.shape) &&
          !isResize
        ) {
          const dx = workingFrame.x - base.frame.x;
          const dy = workingFrame.y - base.frame.y;
          return translateLineEndpoints(base, dx, dy);
        }
        return { ...block, frame: workingFrame };
      });
      updateBlocksSilent(reconcileConnectorsAfterDrag(nextBlocks, draggedIds));
    },
    [configRef, previewGroupGesture, resolveBaseline, snapToObjectsRef, updateBlocksSilent],
  );

  const handleInteractionStart = useCallback(
    (meta?: {
      blockId: string;
      mode: string;
      startFrame: ComunicadoBlock["frame"];
    }) => {
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
      /* Filhos isolados: não reexpandir o grupo (senão resize/move afeta todos). */
      const activeIds = resolveMultiDragBlockIds(configRef.current.blocks ?? [], baseIds);
      if (activeIds.length > 1) {
        const members: Array<{ id: string; frame: ComunicadoFrame; rotation: number }> = [];
        const groupIds = new Set<string>();
        for (const id of activeIds) {
          const block = configRef.current.blocks?.find((item) => item.id === id);
          if (!block) continue;
          if (block.groupId) groupIds.add(block.groupId);
          members.push({
            id: block.id,
            frame: { ...block.frame },
            rotation: block.style?.rotation ?? 0,
          });
        }
        const slideAspect = getSlideAspectRatioRef.current();
        const groupId = groupIds.size === 1 ? [...groupIds][0] : undefined;
        const provisional = beginGroupGesture({
          members,
          slideAspect,
          groupRotation: groupId
            ? configRef.current.groupTransforms?.[groupId]?.rotation
            : undefined,
          interactionStartFrame: meta?.startFrame,
          resizeHandle: meta?.mode ? normalizeResizeHandle(meta.mode) : null,
        });
        if (provisional && meta?.blockId) {
          const interactionStartRotation = provisional.dragFromChrome
            ? provisional.group.rotation
            : (members.find((member) => member.id === meta.blockId)?.rotation ??
              provisional.group.rotation);
          groupGestureRef.current = {
            ...provisional,
            interactionStartRotation,
          };
        } else {
          groupGestureRef.current = provisional;
        }
        setActiveGroupGesture(groupGestureRef.current);
      } else {
        groupGestureRef.current = null;
        setActiveGroupGesture(null);
      }
    },
    [cancelPendingTapDeselect, configRef, selectedId, selectedIds],
  );

  const handleInteractionEnd = useCallback(
    (
      blockId: string,
      _frame: ComunicadoBlock["frame"],
      mode: "move" | "resize" | "rotate" | "adjust" | "endpoint",
    ) => {
      setActiveSmartGuides([]);
      const before = dragSnapshotRef.current;
      dragSnapshotRef.current = null;
      const gesture = groupGestureRef.current;
      groupGestureRef.current = null;
      setActiveGroupGesture(null);
      if (!before) return;

      const recordGestureHistory = () => {
        pushPast(before);
        deckHistory?.recordBeforeChange(serializeComunicadoConfig(before));
      };

      /*
       * Grupo/multi: snap opcional no GroupTransform e um único bake world.
       * Este ramo também finaliza rotate — antes rotate saía cedo e dependia
       * do bake live por membro, reintroduzindo a distorção.
       */
      if (gesture && gesture.memberIds.length > 1) {
        let finalGesture = gesture;
        if (mode !== "rotate" && snapToGridRef.current) {
          const snapPercents = stageGridSnapPercents(stageGridSizePercentRef.current);
          const anchor =
            before.blocks?.find((block) => block.id === blockId) ??
            before.blocks?.find((block) => block.id === gesture.memberIds[0]);
          if (anchor) {
            const snappedGroup = snapComunicadoFrame(
              { ...anchor, frame: gesture.group.frame } as ComunicadoBlock,
              gesture.group.frame,
              mode === "resize" ? "resize" : "move",
              snapPercents,
            );
            if (mode === "move") {
              finalGesture = {
                ...gesture,
                group: { ...gesture.group, frame: snappedGroup },
              };
            } else if (mode === "resize") {
              finalGesture = applyGroupScale(
                {
                  ...gesture,
                  dragFromChrome: true,
                  interactionStartFrame: { ...gesture.childExtent },
                },
                snappedGroup,
                { lockAspect: true },
              );
            }
          }
        } else if (mode === "move") {
          const clamped = clampFrameForBlock(
            {
              type: "shape",
              shape: "rect",
              id: "group-chrome",
              frame: gesture.group.frame,
            } as unknown as ComunicadoBlock,
            gesture.group.frame,
          );
          finalGesture = {
            ...gesture,
            group: { ...gesture.group, frame: clamped },
          };
        }

        const updates = resolveWorldFrames(finalGesture);
        const draggedIds = new Set(updates.keys());
        let nextBlocks = applyWorldUpdatesToBlocks({
          /* Baseline, não config live: preview não altera os membros. */
          blocks: before.blocks ?? [],
          updates,
          resolveBaseline: (id) => before.blocks?.find((block) => block.id === id),
          childExtent: finalGesture.childExtent,
          groupFrame: finalGesture.group.frame,
        });
        nextBlocks = reconcileConnectorsAfterDrag(nextBlocks, draggedIds);

        const nextConfig: ComunicadoConfig = { ...configRef.current, blocks: nextBlocks };
        const groupIds = new Set(
          gesture.memberIds
            .map((id) => before.blocks?.find((block) => block.id === id)?.groupId)
            .filter((id): id is string => Boolean(id)),
        );
        if (groupIds.size === 1) {
          const groupId = [...groupIds][0]!;
          nextConfig.groupTransforms = {
            ...(configRef.current.groupTransforms ?? {}),
            [groupId]: { rotation: finalGesture.group.rotation },
          };
        }
        const unchanged = gesture.memberIds.every((id) => {
          const beforeBlock = before.blocks?.find((block) => block.id === id);
          const afterBlock = nextBlocks.find((block) => block.id === id);
          if (!beforeBlock || !afterBlock) return true;
          return (
            beforeBlock.frame.x === afterBlock.frame.x &&
            beforeBlock.frame.y === afterBlock.frame.y &&
            beforeBlock.frame.w === afterBlock.frame.w &&
            beforeBlock.frame.h === afterBlock.frame.h &&
            (beforeBlock.style?.rotation ?? 0) === (afterBlock.style?.rotation ?? 0)
          );
        });

        if (unchanged) {
          applyConfig(nextConfig);
          return;
        }
        recordGestureHistory();
        applyConfig(nextConfig);
        return;
      }

      if (mode === "rotate" || mode === "adjust" || mode === "endpoint") {
        const beforeBlock = before.blocks?.find((block) => block.id === blockId);
        const afterBlock = configRef.current.blocks?.find((block) => block.id === blockId);
        const unchanged =
          mode === "rotate"
            ? (beforeBlock?.style?.rotation ?? 0) === (afterBlock?.style?.rotation ?? 0)
            : mode === "endpoint"
              ? JSON.stringify(beforeBlock && "vertices" in beforeBlock ? beforeBlock.vertices : null) ===
                  JSON.stringify(afterBlock && "vertices" in afterBlock ? afterBlock.vertices : null) &&
                JSON.stringify(
                  beforeBlock && "connector" in beforeBlock ? beforeBlock.connector : null,
                ) ===
                  JSON.stringify(
                    afterBlock && "connector" in afterBlock ? afterBlock.connector : null,
                  )
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

      const idsToFinalize = [blockId];

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
          updated = applyComplexBlockFrameWithTypography(beforeBlock, snappedFrame);
        } else {
          updated = { ...current, frame: snappedFrame };
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
    groupGestureRef.current = null;
    setActiveGroupGesture(null);
    multiDragSelectionOverrideRef.current = null;
    cancelPendingTapDeselect();
    setActiveSmartGuides([]);
    setConnectionSitesPreview(null);
  }, [cancelPendingTapDeselect]);

  const { canvasRef, startDrag } = useCanvasBlockInteraction({
    onUpdateFrame: handleUpdateFrame,
    onUpdateStyle: handleUpdateStyle,
    onUpdateBlock: handleUpdateBlock,
    onInteractionStart: handleInteractionStart,
    onInteractionEnd: handleInteractionEnd,
    onTapWithoutDrag: handleTapWithoutDrag,
    resolveBlock: (blockId) => configRef.current.blocks?.find((block) => block.id === blockId),
    resolveBlocks: () => configRef.current.blocks ?? [],
    onConnectionSitesPreview: setConnectionSitesPreview,
  });

  return {
    canvasRef,
    startDrag,
    clearDragSnapshot,
    armMultiDragSelection,
    armTapDeselect,
    cancelPendingTapDeselect,
    activeSmartGuides,
    connectionSitesPreview,
    activeGroupGesture,
  };
}
