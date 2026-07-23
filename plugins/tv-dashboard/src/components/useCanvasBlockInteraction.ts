import { useCallback, useEffect, useRef, type PointerEvent as ReactPointerEvent } from "react";

import {
  applyBlockShapeChromeAdjustment,
  applyConnectorGeometry,
  applyLineEndpointAt,
  attachConnectorEndpoint,
  blockShapeChromeAdjustmentSpecs,
  blockSupportsShapeChromeHandles,
  clampFrame,
  clampFrameForBlock,
  detachConnectorEndpoint,
  findNearestConnectionSite,
  isLineShapeKind,
  isPointShapeKind,
  resolveBlockConnectionSites,
  resolveBlockShapeChromeAdjustmentValues,
  resolveShapeGeometry,
  type ComunicadoBlock,
  type ComunicadoBlockStyle,
  type ComunicadoFrame,
  type ConnectionSite,
} from "@delpi/tv-dashboard-presentation";

import { resizeFrameWithOptionalAspect } from "../utils/resizeFrameAspect";

export type BlockDragMode =
  | "move"
  | "rotate"
  | "resize-nw"
  | "resize-n"
  | "resize-ne"
  | "resize-e"
  | "resize-se"
  | "resize-s"
  | "resize-sw"
  | "resize-w"
  | `adjust-${number}`
  | "endpoint-0"
  | "endpoint-1";

export type ConnectionSitesPreview = {
  blockId: string;
  endpointIndex: 0 | 1;
  point: { x: number; y: number };
  sites: ConnectionSite[];
  activeSite: ConnectionSite | null;
};

type DragState = {
  mode: BlockDragMode;
  blockId: string;
  startX: number;
  startY: number;
  startFrame: ComunicadoFrame;
  aspectRatio: number;
  startRotation?: number;
  startPointerAngle?: number;
  centerX?: number;
  centerY?: number;
  /** Ajuste de geometria / chrome herdado (handle laranja). */
  adjIndex?: number;
  startAdjustments?: number[];
  shortSidePx?: number;
  /** Posição local (0–100) no quadro no pointerdown — evita salto ao clicar. */
  startLocalX?: number;
  startLocalY?: number;
  endpointIndex?: 0 | 1;
};

type PendingDragState = DragState & {
  pointerId: number;
};

type Options = {
  onUpdateFrame: (blockId: string, frame: ComunicadoFrame) => void;
  onUpdateStyle?: (blockId: string, patch: Partial<ComunicadoBlockStyle>) => void;
  /** Patch arbitrário de bloco (KPI/chart chrome via `applyBlockShapeChromeAdjustment`). */
  onUpdateBlock?: (blockId: string, patch: Partial<ComunicadoBlock>) => void;
  onInteractionStart?: () => void;
  onInteractionEnd?: (
    blockId: string,
    frame: ComunicadoFrame,
    mode: "move" | "resize" | "rotate" | "adjust" | "endpoint",
  ) => void;
  /** Move cancelado antes do limiar (toque sem arrastar). */
  onTapWithoutDrag?: (blockId: string) => void;
  resolveBlock?: (blockId: string) => ComunicadoBlock | undefined;
  resolveBlocks?: () => ComunicadoBlock[];
  onConnectionSitesPreview?: (preview: ConnectionSitesPreview | null) => void;
};

const DRAG_THRESHOLD_PX = 5;

function isAdjustMode(mode: BlockDragMode): mode is `adjust-${number}` {
  return mode.startsWith("adjust-");
}

function isEndpointMode(mode: BlockDragMode): mode is "endpoint-0" | "endpoint-1" {
  return mode === "endpoint-0" || mode === "endpoint-1";
}

function parseAdjustIndex(mode: BlockDragMode): number | null {
  if (!isAdjustMode(mode)) return null;
  const index = Number(mode.slice("adjust-".length));
  return Number.isFinite(index) ? index : null;
}

function parseEndpointIndex(mode: BlockDragMode): 0 | 1 | null {
  if (mode === "endpoint-0") return 0;
  if (mode === "endpoint-1") return 1;
  return null;
}

function normalizeRotation(value: number): number {
  let next = value % 360;
  if (next > 180) next -= 360;
  if (next <= -180) next += 360;
  return Math.round(next);
}

export function useCanvasBlockInteraction({
  onUpdateFrame,
  onUpdateStyle,
  onUpdateBlock,
  onInteractionStart,
  onInteractionEnd,
  onTapWithoutDrag,
  resolveBlock,
  resolveBlocks,
  onConnectionSitesPreview,
}: Options) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const pendingRef = useRef<PendingDragState | null>(null);
  const onUpdateFrameRef = useRef(onUpdateFrame);
  const onUpdateStyleRef = useRef(onUpdateStyle);
  const onUpdateBlockRef = useRef(onUpdateBlock);
  const onInteractionStartRef = useRef(onInteractionStart);
  const onInteractionEndRef = useRef(onInteractionEnd);
  const onTapWithoutDragRef = useRef(onTapWithoutDrag);
  const resolveBlocksRef = useRef(resolveBlocks);
  const onConnectionSitesPreviewRef = useRef(onConnectionSitesPreview);
  onUpdateFrameRef.current = onUpdateFrame;
  onUpdateStyleRef.current = onUpdateStyle;
  onUpdateBlockRef.current = onUpdateBlock;
  onInteractionStartRef.current = onInteractionStart;
  onInteractionEndRef.current = onInteractionEnd;
  onTapWithoutDragRef.current = onTapWithoutDrag;
  resolveBlocksRef.current = resolveBlocks;
  onConnectionSitesPreviewRef.current = onConnectionSitesPreview;

  const pointerToPercent = useCallback((clientX: number, clientY: number) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return {
      x: ((clientX - rect.left) / rect.width) * 100,
      y: ((clientY - rect.top) / rect.height) * 100,
    };
  }, []);

  const applyDragMoveRef = useRef<(event: PointerEvent) => void>(() => {});
  const resolveBlockRef = useRef(resolveBlock);
  resolveBlockRef.current = resolveBlock;

  const clampDragFrame = (blockId: string, frame: ComunicadoFrame) => {
    const block = resolveBlockRef.current?.(blockId);
    if (block) return clampFrameForBlock(block, frame);
    return clampFrame(frame);
  };

  applyDragMoveRef.current = (event: PointerEvent) => {
    const drag = dragRef.current;
    if (!drag) return;
    const current = pointerToPercent(event.clientX, event.clientY);
    const start = pointerToPercent(drag.startX, drag.startY);
    const dx = current.x - start.x;
    const dy = current.y - start.y;
    const frame = drag.startFrame;
    const lockAspect = event.shiftKey && drag.mode !== "move" && !isAdjustMode(drag.mode);

    if (drag.mode === "rotate") {
      if (drag.centerX == null || drag.centerY == null || drag.startPointerAngle == null) return;
      const angle = Math.atan2(current.y - drag.centerY, current.x - drag.centerX);
      const deltaDeg = ((angle - drag.startPointerAngle) * 180) / Math.PI;
      onUpdateStyleRef.current?.(drag.blockId, {
        rotation: normalizeRotation((drag.startRotation ?? 0) + deltaDeg),
      });
      return;
    }

    if (isAdjustMode(drag.mode) && drag.adjIndex != null) {
      const block = resolveBlockRef.current?.(drag.blockId);
      if (!block || !blockSupportsShapeChromeHandles(block)) return;
      const localX = frame.w > 0 ? ((current.x - frame.x) / frame.w) * 100 : 50;
      const localY = frame.h > 0 ? ((current.y - frame.y) / frame.h) * 100 : 50;
      const specs = blockShapeChromeAdjustmentSpecs(block);
      const spec = specs.find((item) => item.index === drag.adjIndex) ?? specs[drag.adjIndex];
      if (!spec) return;
      const startValues =
        drag.startAdjustments ??
        resolveBlockShapeChromeAdjustmentValues(block, drag.shortSidePx ?? 64);
      const startValue = startValues[spec.index] ?? spec.defaultValue;
      const startLocalX = drag.startLocalX ?? localX;
      const startLocalY = drag.startLocalY ?? localY;
      const rawNow = spec.valueFromPointer(localX, localY, startValues);
      const rawAtStart = spec.valueFromPointer(startLocalX, startLocalY, startValues);
      const value = Math.min(
        spec.max,
        Math.max(spec.min, startValue + (rawNow - rawAtStart)),
      );
      const patch = applyBlockShapeChromeAdjustment(block, spec.index, value, drag.shortSidePx ?? 64);
      if (!patch) return;
      if (onUpdateBlockRef.current) {
        onUpdateBlockRef.current(drag.blockId, patch);
      } else if (patch.style) {
        onUpdateStyleRef.current?.(drag.blockId, patch.style);
      }
      return;
    }

    if (isEndpointMode(drag.mode) && drag.endpointIndex != null) {
      const block = resolveBlockRef.current?.(drag.blockId);
      if (!block || block.type !== "shape" || !isLineShapeKind(block.shape)) return;
      const allBlocks = resolveBlocksRef.current?.() ?? [];
      const activeSite = findNearestConnectionSite(current, allBlocks, {
        excludeBlockIds: new Set([drag.blockId]),
      });
      const point = activeSite
        ? { x: activeSite.x, y: activeSite.y }
        : { x: current.x, y: current.y };
      let next = applyLineEndpointAt(block, drag.endpointIndex, point);
      next = detachConnectorEndpoint(next, drag.endpointIndex);
      if (activeSite) {
        next = attachConnectorEndpoint(
          next,
          drag.endpointIndex,
          activeSite.blockId,
          activeSite.id,
        );
        next = applyConnectorGeometry(next, allBlocks);
      }
      onUpdateBlockRef.current?.(drag.blockId, {
        vertices: next.vertices,
        frame: next.frame,
        connector: next.connector,
      });
      onConnectionSitesPreviewRef.current?.({
        blockId: drag.blockId,
        endpointIndex: drag.endpointIndex,
        point,
        sites: allBlocks.flatMap((item) =>
          item.id === drag.blockId ? [] : resolveBlockConnectionSites(item),
        ),
        activeSite,
      });
      return;
    }

    if (drag.mode === "move") {
      onUpdateFrameRef.current(
        drag.blockId,
        clampDragFrame(drag.blockId, {
          ...frame,
          x: frame.x + dx,
          y: frame.y + dy,
        }),
      );
      return;
    }

    onUpdateFrameRef.current(
      drag.blockId,
      clampDragFrame(
        drag.blockId,
        resizeFrameWithOptionalAspect(frame, dx, dy, drag.mode, drag.aspectRatio, lockAspect),
      ),
    );
  };

  const pointerListenersRef = useRef({
    onPointerMove: (_event: PointerEvent) => {},
    onPointerUp: () => {},
    onPendingMove: (_event: PointerEvent) => {},
    onPendingUp: (_event: PointerEvent) => {},
  });

  const removePointerListeners = useCallback(() => {
    const listeners = pointerListenersRef.current;
    window.removeEventListener("pointermove", listeners.onPointerMove);
    window.removeEventListener("pointerup", listeners.onPointerUp);
    window.removeEventListener("pointermove", listeners.onPendingMove);
    window.removeEventListener("pointerup", listeners.onPendingUp);
  }, []);

  const finishInteraction = useCallback(() => {
    const drag = dragRef.current;
    if (drag && onInteractionEndRef.current) {
      const mode: "move" | "resize" | "rotate" | "adjust" | "endpoint" =
        drag.mode === "move"
          ? "move"
          : drag.mode === "rotate"
            ? "rotate"
            : isAdjustMode(drag.mode)
              ? "adjust"
              : isEndpointMode(drag.mode)
                ? "endpoint"
                : "resize";
      onInteractionEndRef.current(drag.blockId, drag.startFrame, mode);
    }
    onConnectionSitesPreviewRef.current?.(null);
    pendingRef.current = null;
    dragRef.current = null;
    removePointerListeners();
  }, [removePointerListeners]);

  pointerListenersRef.current.onPointerMove = (event: PointerEvent) => {
    applyDragMoveRef.current(event);
  };

  pointerListenersRef.current.onPointerUp = () => {
    finishInteraction();
  };

  pointerListenersRef.current.onPendingMove = (event: PointerEvent) => {
    const pending = pendingRef.current;
    if (!pending || event.pointerId !== pending.pointerId) return;
    const dx = event.clientX - pending.startX;
    const dy = event.clientY - pending.startY;
    if (dx * dx + dy * dy < DRAG_THRESHOLD_PX * DRAG_THRESHOLD_PX) return;

    onInteractionStartRef.current?.();

    const { pointerId: _pointerId, ...dragState } = pending;
    pendingRef.current = null;
    removePointerListeners();
    dragRef.current = dragState;
    const listeners = pointerListenersRef.current;
    window.addEventListener("pointermove", listeners.onPointerMove);
    window.addEventListener("pointerup", listeners.onPointerUp);
    applyDragMoveRef.current(event);
  };

  pointerListenersRef.current.onPendingUp = (event: PointerEvent) => {
    if (pendingRef.current && event.pointerId !== pendingRef.current.pointerId) return;
    const pending = pendingRef.current;
    pendingRef.current = null;
    removePointerListeners();
    if (pending) {
      onTapWithoutDragRef.current?.(pending.blockId);
    }
  };

  useEffect(() => {
    return () => {
      removePointerListeners();
    };
  }, [removePointerListeners]);

  const startDrag = useCallback(
    (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => {
      // Só botão esquerdo: direito abre menu; meio/outros não movem nem redimensionam.
      if (Number.isFinite(event.button) && event.button !== 0) return;
      // Ctrl+arraste = pan do palco; não iniciar move/resize do bloco.
      if (event.ctrlKey) return;
      event.preventDefault();
      event.stopPropagation();

      const aspectRatio = block.frame.w / Math.max(block.frame.h, 0.1);
      const dragState: DragState = {
        mode,
        blockId: block.id,
        startX: event.clientX,
        startY: event.clientY,
        startFrame: { ...block.frame },
        aspectRatio,
      };

      const listeners = pointerListenersRef.current;
      const adjIndex = parseAdjustIndex(mode);

      if (adjIndex != null && blockSupportsShapeChromeHandles(block)) {
        const wrap = (event.currentTarget as HTMLElement).closest(".td-composer__block-wrap");
        // offsetWidth/Height = espaço de layout (design), não getBoundingClientRect (já com zoom).
        const shortSidePx = wrap
          ? Math.min(
              (wrap as HTMLElement).offsetWidth || 64,
              (wrap as HTMLElement).offsetHeight || 64,
            )
          : 64;
        const startPt = pointerToPercent(event.clientX, event.clientY);
        const frame = dragState.startFrame;
        const startLocalX = frame.w > 0 ? ((startPt.x - frame.x) / frame.w) * 100 : 50;
        const startLocalY = frame.h > 0 ? ((startPt.y - frame.y) / frame.h) * 100 : 50;
        onInteractionStartRef.current?.();
        dragRef.current = {
          ...dragState,
          adjIndex,
          startAdjustments: resolveBlockShapeChromeAdjustmentValues(block, shortSidePx),
          shortSidePx,
          startLocalX,
          startLocalY,
        };
        window.addEventListener("pointermove", listeners.onPointerMove);
        window.addEventListener("pointerup", listeners.onPointerUp);
        return;
      }

      const endpointIndex = parseEndpointIndex(mode);
      if (endpointIndex != null && block.type === "shape" && isLineShapeKind(block.shape)) {
        onInteractionStartRef.current?.();
        dragRef.current = {
          ...dragState,
          endpointIndex,
        };
        window.addEventListener("pointermove", listeners.onPointerMove);
        window.addEventListener("pointerup", listeners.onPointerUp);
        return;
      }

      if (mode === "rotate") {
        let centerX = block.frame.x + block.frame.w / 2;
        let centerY = block.frame.y + block.frame.h / 2;
        if (block.type === "shape" && isPointShapeKind(block.shape)) {
          const geometry = resolveShapeGeometry(block);
          if (geometry.primitive === "point") {
            centerX = geometry.position.x;
            centerY = geometry.position.y;
          }
        }
        const startPt = pointerToPercent(event.clientX, event.clientY);
        onInteractionStartRef.current?.();
        dragRef.current = {
          ...dragState,
          centerX,
          centerY,
          startRotation: block.style?.rotation ?? 0,
          startPointerAngle: Math.atan2(startPt.y - centerY, startPt.x - centerX),
        };
        window.addEventListener("pointermove", listeners.onPointerMove);
        window.addEventListener("pointerup", listeners.onPointerUp);
        return;
      }

      if (mode !== "move") {
        onInteractionStartRef.current?.();
        pendingRef.current = null;
        removePointerListeners();
        dragRef.current = dragState;
        window.addEventListener("pointermove", listeners.onPointerMove);
        window.addEventListener("pointerup", listeners.onPointerUp);
        return;
      }

      pendingRef.current = { ...dragState, pointerId: event.pointerId };
      window.addEventListener("pointermove", listeners.onPendingMove);
      window.addEventListener("pointerup", listeners.onPendingUp);
    },
    [pointerToPercent, removePointerListeners],
  );

  return { canvasRef, startDrag };
};
