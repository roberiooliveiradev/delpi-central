import { useCallback, useEffect, useRef, useState } from "react";
import {
  createDrawnLineBlock,
  createFreeformPathBlock,
  isClickPathDrawTool,
  isLineDrawToolId,
  previewDrawnLinePoints,
  smoothCurveThroughPoints,
  snapPointToConnectionSite,
  type ComunicadoBlock,
  type ComunicadoGeometryVertex,
  type ComunicadoLineToolId,
  type ComunicadoShapeBlock,
  type DrawnLineAttach,
  type LineDrawToolKind,
} from "@delpi/tv-dashboard-presentation";

const MIN_DRAW_DISTANCE_PCT = 0.4;
const MIN_SCRIBBLE_SAMPLE_PCT = 0.25;
const DOUBLE_CLICK_MS = 350;
const DOUBLE_CLICK_PCT = 1.2;

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

type ClickDraft = {
  tool: "polyline" | "curve";
  anchors: ComunicadoGeometryVertex[];
  cursor: ComunicadoGeometryVertex;
  lastClickAt: number;
  lastClickPoint: ComunicadoGeometryVertex;
};

type Params = {
  stageDrawTool: ComunicadoLineToolId | null;
  blocks: ComunicadoBlock[];
  clientToCanvasPercent: (clientX: number, clientY: number) => ComunicadoGeometryVertex;
  addPreparedShapeBlock: (block: ComunicadoShapeBlock) => void;
};

/**
 * Gesto de desenho Linha / Seta / Conector / Curva / Polilinha / Rabisco no palco.
 */
export function useStageLineDraw({
  stageDrawTool,
  blocks,
  clientToCanvasPercent,
  addPreparedShapeBlock,
}: Params) {
  const [drawPreview, setDrawPreview] = useState<StageLineDrawPreview | null>(null);
  const clickDraftRef = useRef<ClickDraft | null>(null);
  const blocksRef = useRef(blocks);
  blocksRef.current = blocks;

  const clearClickDraft = useCallback(() => {
    clickDraftRef.current = null;
    setDrawPreview(null);
  }, []);

  useEffect(() => {
    clearClickDraft();
  }, [stageDrawTool, clearClickDraft]);

  const previewClickDraft = useCallback((draft: ClickDraft) => {
    const live = [...draft.anchors, draft.cursor];
    const points =
      draft.tool === "curve" && live.length >= 2 ? smoothCurveThroughPoints(live) : live;
    setDrawPreview({ tool: draft.tool, points });
  }, []);

  const commitClickDraft = useCallback(() => {
    const draft = clickDraftRef.current;
    if (!draft || draft.anchors.length < 2) {
      clearClickDraft();
      return false;
    }
    const block = createFreeformPathBlock({
      tool: draft.tool,
      vertices: draft.anchors,
    });
    clearClickDraft();
    if (block) addPreparedShapeBlock(block);
    return Boolean(block);
  }, [addPreparedShapeBlock, clearClickDraft]);

  const beginDragTool = useCallback(
    (event: React.PointerEvent<HTMLDivElement>, tool: LineDrawToolKind) => {
      event.preventDefault();
      event.stopPropagation();

      const currentBlocks = blocksRef.current;
      const rawStart = clientToCanvasPercent(event.clientX, event.clientY);
      const startSnap = snapPointToConnectionSite(rawStart, currentBlocks);
      const start = startSnap.point;
      const fromAttach: DrawnLineAttach | undefined = startSnap.attach;
      let end = start;
      let toAttach: DrawnLineAttach | undefined;
      const scribblePoints: ComunicadoGeometryVertex[] = [{ ...start }];

      if (tool === "scribble") {
        setDrawPreview({ tool, points: [...scribblePoints] });
      } else {
        setDrawPreview({
          tool,
          points: previewDrawnLinePoints(start, end, tool),
        });
      }

      const onMove = (moveEvent: PointerEvent) => {
        moveEvent.preventDefault();
        let nextEnd = clientToCanvasPercent(moveEvent.clientX, moveEvent.clientY);
        if (tool === "scribble") {
          const last = scribblePoints[scribblePoints.length - 1]!;
          if (Math.hypot(nextEnd.x - last.x, nextEnd.y - last.y) >= MIN_SCRIBBLE_SAMPLE_PCT) {
            scribblePoints.push(nextEnd);
            setDrawPreview({ tool, points: [...scribblePoints] });
          }
          return;
        }
        if (moveEvent.shiftKey && (tool === "line" || tool === "line-arrow")) {
          nextEnd = snapAngle45(start, nextEnd);
        }
        const endSnap = snapPointToConnectionSite(nextEnd, currentBlocks);
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

        if (tool === "scribble") {
          if (scribblePoints.length < 2) return;
          const block = createFreeformPathBlock({
            tool: "scribble",
            vertices: scribblePoints,
          });
          if (block) addPreparedShapeBlock(block);
          return;
        }

        const dist = Math.hypot(end.x - start.x, end.y - start.y);
        if (dist < MIN_DRAW_DISTANCE_PCT) return;

        const block = createDrawnLineBlock({
          tool,
          start,
          end,
          blocks: currentBlocks,
          fromAttach,
          toAttach,
        });
        addPreparedShapeBlock(block);
      };

      window.addEventListener("pointermove", onMove, { passive: false });
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    },
    [addPreparedShapeBlock, clientToCanvasPercent],
  );

  const beginClickPathTool = useCallback(
    (event: React.PointerEvent<HTMLDivElement>, tool: "polyline" | "curve") => {
      event.preventDefault();
      event.stopPropagation();

      const point = clientToCanvasPercent(event.clientX, event.clientY);
      const existing = clickDraftRef.current;
      const now = Date.now();

      if (
        existing &&
        existing.tool === tool &&
        now - existing.lastClickAt <= DOUBLE_CLICK_MS &&
        Math.hypot(point.x - existing.lastClickPoint.x, point.y - existing.lastClickPoint.y) <=
          DOUBLE_CLICK_PCT
      ) {
        commitClickDraft();
        return;
      }

      if (!existing || existing.tool !== tool) {
        const draft: ClickDraft = {
          tool,
          anchors: [point],
          cursor: point,
          lastClickAt: now,
          lastClickPoint: point,
        };
        clickDraftRef.current = draft;
        previewClickDraft(draft);
      } else {
        existing.anchors.push(point);
        existing.cursor = point;
        existing.lastClickAt = now;
        existing.lastClickPoint = point;
        previewClickDraft(existing);
      }

      const onMove = (moveEvent: PointerEvent) => {
        const draft = clickDraftRef.current;
        if (!draft) return;
        draft.cursor = clientToCanvasPercent(moveEvent.clientX, moveEvent.clientY);
        previewClickDraft(draft);
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
      };

      window.addEventListener("pointermove", onMove, { passive: true });
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    },
    [clientToCanvasPercent, commitClickDraft, previewClickDraft],
  );

  const beginDraw = useCallback(
    (event: React.PointerEvent<HTMLDivElement>) => {
      if (!isLineDrawToolId(stageDrawTool)) return false;
      if (isClickPathDrawTool(stageDrawTool)) {
        beginClickPathTool(event, stageDrawTool);
        return true;
      }
      beginDragTool(event, stageDrawTool);
      return true;
    },
    [beginClickPathTool, beginDragTool, stageDrawTool],
  );

  return {
    drawPreview,
    beginDraw,
    isDrawToolActive: isLineDrawToolId(stageDrawTool),
    hasPathDraft: Boolean(clickDraftRef.current),
    finishPathDraft: commitClickDraft,
    cancelPathDraft: clearClickDraft,
  };
}
