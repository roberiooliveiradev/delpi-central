import { useCallback, useState } from "react";
import {
  createDrawnLineBlock,
  isLineDrawToolId,
  previewDrawnLinePoints,
  snapPointToConnectionSite,
  type ComunicadoBlock,
  type ComunicadoGeometryVertex,
  type ComunicadoLineToolId,
  type ComunicadoShapeBlock,
  type DrawnLineAttach,
  type LineDrawToolKind,
} from "@delpi/tv-dashboard-presentation";

const MIN_DRAW_DISTANCE_PCT = 0.4;

export type StageLineDrawPreview = {
  tool: LineDrawToolKind;
  points: ComunicadoGeometryVertex[];
};

function snapAngle45(
  start: ComunicadoGeometryVertex,
  end: ComunicadoGeometryVertex,
): ComunicadoGeometryVertex {
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const len = Math.hypot(dx, dy) || 1;
  const angle = Math.atan2(dy, dx);
  const snapped = Math.round(angle / (Math.PI / 4)) * (Math.PI / 4);
  return {
    x: start.x + Math.cos(snapped) * len,
    y: start.y + Math.sin(snapped) * len,
  };
}

type Params = {
  stageDrawTool: ComunicadoLineToolId | null;
  blocks: ComunicadoBlock[];
  clientToCanvasPercent: (clientX: number, clientY: number) => ComunicadoGeometryVertex;
  addPreparedShapeBlock: (block: ComunicadoShapeBlock) => void;
};

/**
 * Gesto de desenho Linha/Seta/Conector no palco (Inserir → Linha).
 */
export function useStageLineDraw({
  stageDrawTool,
  blocks,
  clientToCanvasPercent,
  addPreparedShapeBlock,
}: Params) {
  const [drawPreview, setDrawPreview] = useState<StageLineDrawPreview | null>(null);

  const beginDraw = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (!isLineDrawToolId(stageDrawTool)) return false;

      event.preventDefault();
      event.stopPropagation();

      const tool = stageDrawTool;
      const rawStart = clientToCanvasPercent(event.clientX, event.clientY);
      const startSnap = snapPointToConnectionSite(rawStart, blocks);
      const start = startSnap.point;
      const fromAttach: DrawnLineAttach | undefined = startSnap.attach;
      let end = start;
      let toAttach: DrawnLineAttach | undefined;

      setDrawPreview({
        tool,
        points: previewDrawnLinePoints(start, end, tool),
      });

      const onMove = (moveEvent: PointerEvent) => {
        moveEvent.preventDefault();
        let nextEnd = clientToCanvasPercent(moveEvent.clientX, moveEvent.clientY);
        if (moveEvent.shiftKey && (tool === "line" || tool === "line-arrow")) {
          nextEnd = snapAngle45(start, nextEnd);
        }
        const endSnap = snapPointToConnectionSite(nextEnd, blocks);
        end = endSnap.point;
        toAttach = endSnap.attach;
        setDrawPreview({
          tool,
          points: previewDrawnLinePoints(
            start,
            end,
            tool,
            fromAttach?.anchor ?? "center",
            toAttach?.anchor ?? "center",
          ),
        });
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
        setDrawPreview(null);

        const dist = Math.hypot(end.x - start.x, end.y - start.y);
        if (dist < MIN_DRAW_DISTANCE_PCT) return;

        const block = createDrawnLineBlock({
          tool,
          start,
          end,
          blocks,
          fromAttach,
          toAttach,
        });
        addPreparedShapeBlock(block);
      };

      window.addEventListener("pointermove", onMove, { passive: false });
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
      return true;
    },
    [addPreparedShapeBlock, blocks, clientToCanvasPercent, stageDrawTool],
  );

  return { drawPreview, beginDraw, isDrawToolActive: isLineDrawToolId(stageDrawTool) };
}
