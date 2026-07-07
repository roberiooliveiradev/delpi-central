import { useCallback, useEffect, useRef, type PointerEvent as ReactPointerEvent } from "react";

import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";
import { clampFrame } from "@delpi/tv-dashboard-presentation";

type DragMode = "move" | "resize-se" | "resize-e" | "resize-s";

type DragState = {
  mode: DragMode;
  blockId: string;
  startX: number;
  startY: number;
  startFrame: ComunicadoFrame;
};

type PendingDragState = DragState & {
  pointerId: number;
};

type Options = {
  onUpdateFrame: (blockId: string, frame: ComunicadoFrame) => void;
};

const DRAG_THRESHOLD_PX = 5;

export function useCanvasBlockInteraction({ onUpdateFrame }: Options) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
  const pendingRef = useRef<PendingDragState | null>(null);
  const onUpdateFrameRef = useRef(onUpdateFrame);
  onUpdateFrameRef.current = onUpdateFrame;

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

    if (drag.mode === "resize-se") {
      onUpdateFrameRef.current(
        drag.blockId,
        clampFrame({
          ...frame,
          w: frame.w + dx,
          h: frame.h + dy,
        }),
      );
      return;
    }

    if (drag.mode === "resize-e") {
      onUpdateFrameRef.current(
        drag.blockId,
        clampFrame({
          ...frame,
          w: frame.w + dx,
        }),
      );
      return;
    }

    onUpdateFrameRef.current(
      drag.blockId,
      clampFrame({
        ...frame,
        h: frame.h + dy,
      }),
    );
  };

  const onPointerMove = useCallback((event: PointerEvent) => {
    applyDragMoveRef.current(event);
  }, []);

  const onPointerUp = useCallback(() => {
    pendingRef.current = null;
    dragRef.current = null;
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
    window.removeEventListener("pointermove", onPendingMove);
    window.removeEventListener("pointerup", onPendingUp);
  }, []);

  const onPendingMove = useCallback((event: PointerEvent) => {
    const pending = pendingRef.current;
    if (!pending || event.pointerId !== pending.pointerId) return;
    const dx = event.clientX - pending.startX;
    const dy = event.clientY - pending.startY;
    if (dx * dx + dy * dy < DRAG_THRESHOLD_PX * DRAG_THRESHOLD_PX) return;

    const { pointerId: _pointerId, ...dragState } = pending;
    pendingRef.current = null;
    window.removeEventListener("pointermove", onPendingMove);
    window.removeEventListener("pointerup", onPendingUp);
    dragRef.current = dragState;
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    applyDragMoveRef.current(event);
  }, [onPointerMove]);

  const onPendingUp = useCallback(
    (event: PointerEvent) => {
      if (pendingRef.current && event.pointerId !== pendingRef.current.pointerId) return;
      pendingRef.current = null;
      window.removeEventListener("pointermove", onPendingMove);
      window.removeEventListener("pointerup", onPendingUp);
    },
    [onPendingMove],
  );

  useEffect(() => {
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointermove", onPendingMove);
      window.removeEventListener("pointerup", onPendingUp);
    };
  }, [onPointerMove, onPointerUp, onPendingMove, onPendingUp]);

  const startDrag = useCallback(
    (event: ReactPointerEvent, block: ComunicadoBlock, mode: DragMode) => {
      event.preventDefault();
      event.stopPropagation();

      const dragState: DragState = {
        mode,
        blockId: block.id,
        startX: event.clientX,
        startY: event.clientY,
        startFrame: { ...block.frame },
      };

      if (mode !== "move") {
        pendingRef.current = null;
        window.removeEventListener("pointermove", onPendingMove);
        window.removeEventListener("pointerup", onPendingUp);
        dragRef.current = dragState;
        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
        return;
      }

      pendingRef.current = { ...dragState, pointerId: event.pointerId };
      window.addEventListener("pointermove", onPendingMove);
      window.addEventListener("pointerup", onPendingUp);
    },
    [onPointerMove, onPendingMove, onPendingUp],
  );

  return { canvasRef, startDrag };
}
