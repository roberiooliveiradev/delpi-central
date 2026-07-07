import { useCallback, useEffect, useRef, type PointerEvent as ReactPointerEvent } from "react";

import type { ComunicadoBlock, ComunicadoBlockStyle, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";
import { clampFrame } from "@delpi/tv-dashboard-presentation";

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
  | "resize-w";

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
};

type PendingDragState = DragState & {
  pointerId: number;
};

type Options = {
  onUpdateFrame: (blockId: string, frame: ComunicadoFrame) => void;
  onUpdateStyle?: (blockId: string, patch: Partial<ComunicadoBlockStyle>) => void;
  onInteractionStart?: () => void;
  onInteractionEnd?: (blockId: string, frame: ComunicadoFrame, mode: "move" | "resize" | "rotate") => void;
};

const DRAG_THRESHOLD_PX = 5;

function resizeFrame(
  frame: ComunicadoFrame,
  dx: number,
  dy: number,
  mode: BlockDragMode,
  aspectRatio: number,
  lockAspect: boolean,
): ComunicadoFrame {
  let next: ComunicadoFrame;
  switch (mode) {
    case "resize-se":
      next = { ...frame, w: frame.w + dx, h: frame.h + dy };
      break;
    case "resize-e":
      next = { ...frame, w: frame.w + dx };
      break;
    case "resize-s":
      next = { ...frame, h: frame.h + dy };
      break;
    case "resize-n":
      next = { ...frame, y: frame.y + dy, h: frame.h - dy };
      break;
    case "resize-w":
      next = { ...frame, x: frame.x + dx, w: frame.w - dx };
      break;
    case "resize-ne":
      next = { ...frame, y: frame.y + dy, w: frame.w + dx, h: frame.h - dy };
      break;
    case "resize-nw":
      next = { ...frame, x: frame.x + dx, y: frame.y + dy, w: frame.w - dx, h: frame.h - dy };
      break;
    case "resize-sw":
      next = { ...frame, x: frame.x + dx, w: frame.w - dx, h: frame.h + dy };
      break;
    default:
      return frame;
  }

  if (!lockAspect || aspectRatio <= 0) {
    return next;
  }

  const dominant = Math.abs(dx) >= Math.abs(dy) ? "w" : "h";
  if (dominant === "w") {
    next.h = next.w / aspectRatio;
  } else {
    next.w = next.h * aspectRatio;
  }
  return next;
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
  onInteractionStart,
  onInteractionEnd,
}: Options) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const pendingRef = useRef<PendingDragState | null>(null);
  const onUpdateFrameRef = useRef(onUpdateFrame);
  const onUpdateStyleRef = useRef(onUpdateStyle);
  const onInteractionStartRef = useRef(onInteractionStart);
  const onInteractionEndRef = useRef(onInteractionEnd);
  onUpdateFrameRef.current = onUpdateFrame;
  onUpdateStyleRef.current = onUpdateStyle;
  onInteractionStartRef.current = onInteractionStart;
  onInteractionEndRef.current = onInteractionEnd;

  const pointerToPercent = useCallback((clientX: number, clientY: number) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return {
      x: ((clientX - rect.left) / rect.width) * 100,
      y: ((clientY - rect.top) / rect.height) * 100,
    };
  }, []);

  const applyDragMoveRef = useRef<(event: PointerEvent) => void>(() => {});
  applyDragMoveRef.current = (event: PointerEvent) => {
    const drag = dragRef.current;
    if (!drag) return;
    const current = pointerToPercent(event.clientX, event.clientY);
    const start = pointerToPercent(drag.startX, drag.startY);
    const dx = current.x - start.x;
    const dy = current.y - start.y;
    const frame = drag.startFrame;
    const lockAspect = event.shiftKey && drag.mode !== "move";

    if (drag.mode === "rotate") {
      if (drag.centerX == null || drag.centerY == null || drag.startPointerAngle == null) return;
      const angle = Math.atan2(current.y - drag.centerY, current.x - drag.centerX);
      const deltaDeg = ((angle - drag.startPointerAngle) * 180) / Math.PI;
      onUpdateStyleRef.current?.(drag.blockId, {
        rotation: normalizeRotation((drag.startRotation ?? 0) + deltaDeg),
      });
      return;
    }

    if (drag.mode === "move") {
      onUpdateFrameRef.current(
        drag.blockId,
        clampFrame({
          ...frame,
          x: frame.x + dx,
          y: frame.y + dy,
        }),
      );
      return;
    }

    onUpdateFrameRef.current(
      drag.blockId,
      clampFrame(resizeFrame(frame, dx, dy, drag.mode, drag.aspectRatio, lockAspect)),
    );
  };

  /** Refs evitam TDZ entre finishInteraction ↔ onPointerUp ↔ onPendingMove. */
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
      const mode: "move" | "resize" | "rotate" =
        drag.mode === "move" ? "move" : drag.mode === "rotate" ? "rotate" : "resize";
      onInteractionEndRef.current(drag.blockId, drag.startFrame, mode);
    }
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
    pendingRef.current = null;
    removePointerListeners();
  };

  useEffect(() => {
    return () => {
      removePointerListeners();
    };
  }, [removePointerListeners]);

  const startDrag = useCallback(
    (event: ReactPointerEvent, block: ComunicadoBlock, mode: BlockDragMode) => {
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

      if (mode === "rotate") {
        const centerX = block.frame.x + block.frame.w / 2;
        const centerY = block.frame.y + block.frame.h / 2;
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
