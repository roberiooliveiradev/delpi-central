import { useCallback, useRef, type PointerEvent as ReactPointerEvent } from "react";

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

type Options = {
  onUpdateFrame: (blockId: string, frame: ComunicadoFrame) => void;
};

export function useCanvasBlockInteraction({ onUpdateFrame }: Options) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);
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

  const endDrag = useCallback(() => {
    dragRef.current = null;
    window.removeEventListener("pointermove", handlePointerMove);
    window.removeEventListener("pointerup", handlePointerUp);
  }, []);

  const handlePointerMove = useCallback(
    (event: PointerEvent) => {
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
    },
    [pointerToPercent],
  );

  const handlePointerUp = useCallback(() => {
    endDrag();
  }, [endDrag]);

  const startDrag = useCallback(
    (event: ReactPointerEvent, block: ComunicadoBlock, mode: DragMode) => {
      event.preventDefault();
      event.stopPropagation();
      dragRef.current = {
        mode,
        blockId: block.id,
        startX: event.clientX,
        startY: event.clientY,
        startFrame: { ...block.frame },
      };
      window.addEventListener("pointermove", handlePointerMove);
      window.addEventListener("pointerup", handlePointerUp);
    },
    [handlePointerMove, handlePointerUp],
  );

  return { canvasRef, startDrag };
}
