import {
  useCallback,
  useEffect,
  useRef,
  type PointerEvent as ReactPointerEvent,
} from "react";

import {
  MEETING_INK_COLOR,
  MEETING_INK_WIDTH_PX,
  type MeetingAnnotationTool,
  type MeetingInkStroke,
  type MeetingLaserState,
  type MeetingNormPoint,
} from "./meetingAnnotationTypes";
import {
  createMeetingStrokeId,
  meetingPointsToSvgPath,
  normalizeMeetingPoint,
  strokesForSlide,
} from "./meetingInkModel";
import "./meeting-annotation.css";

export type MeetingAnnotationOverlayProps = {
  enabled: boolean;
  slideId: string;
  clientId: string;
  tool: MeetingAnnotationTool;
  strokes: MeetingInkStroke[];
  lasers: MeetingLaserState[];
  onLocalStroke: (event: {
    strokeId: string;
    phase: "start" | "move" | "end";
    points: MeetingNormPoint[];
  }) => void;
  onLocalLaser: (event: { x: number; y: number; visible: boolean }) => void;
};

function pointerToNorm(
  event: ReactPointerEvent<HTMLDivElement>,
  el: HTMLDivElement,
): MeetingNormPoint {
  const rect = el.getBoundingClientRect();
  const w = rect.width || 1;
  const h = rect.height || 1;
  return normalizeMeetingPoint((event.clientX - rect.left) / w, (event.clientY - rect.top) / h);
}

/**
 * Overlay efêmero de caneta/laser (modo reunião).
 * Estado só em memória React — F5 limpa.
 */
export function MeetingAnnotationOverlay({
  enabled,
  slideId,
  clientId,
  tool,
  strokes,
  lasers,
  onLocalStroke,
  onLocalLaser,
}: MeetingAnnotationOverlayProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const drawingRef = useRef<{ strokeId: string; pointerId: number } | null>(null);
  const lastMoveAtRef = useRef(0);

  useEffect(() => {
    drawingRef.current = null;
  }, [slideId]);

  const visibleStrokes = strokesForSlide(strokes, slideId);
  const visibleLasers = lasers.filter(
    (laser) => laser.visible && laser.slideId === slideId,
  );

  const endLaser = useCallback(() => {
    onLocalLaser({ x: 0.5, y: 0.5, visible: false });
  }, [onLocalLaser]);

  if (!enabled) return null;

  const interactive = tool === "pen" || tool === "laser";

  return (
    <div
      ref={rootRef}
      className={[
        "tdp-meeting-annotation",
        interactive ? "tdp-meeting-annotation--interactive" : null,
        tool === "pen" ? "tdp-meeting-annotation--pen" : null,
        tool === "laser" ? "tdp-meeting-annotation--laser" : null,
      ]
        .filter(Boolean)
        .join(" ")}
      aria-hidden={!interactive}
      onPointerDown={(event) => {
        if (!interactive || !rootRef.current) return;
        event.preventDefault();
        rootRef.current.setPointerCapture(event.pointerId);
        const point = pointerToNorm(event, rootRef.current);
        if (tool === "pen") {
          const strokeId = createMeetingStrokeId(clientId);
          drawingRef.current = { strokeId, pointerId: event.pointerId };
          onLocalStroke({ strokeId, phase: "start", points: [point] });
          return;
        }
        onLocalLaser({ ...point, visible: true });
      }}
      onPointerMove={(event) => {
        if (!interactive || !rootRef.current) return;
        const now = performance.now();
        if (tool === "laser" && now - lastMoveAtRef.current < 32) return;
        lastMoveAtRef.current = now;
        const point = pointerToNorm(event, rootRef.current);
        if (tool === "laser") {
          if ((event.buttons & 1) === 0 && event.pointerType === "mouse") return;
          onLocalLaser({ ...point, visible: true });
          return;
        }
        const drawing = drawingRef.current;
        if (!drawing || drawing.pointerId !== event.pointerId) return;
        onLocalStroke({ strokeId: drawing.strokeId, phase: "move", points: [point] });
      }}
      onPointerUp={(event) => {
        if (!rootRef.current) return;
        try {
          rootRef.current.releasePointerCapture(event.pointerId);
        } catch {
          // ignore
        }
        if (tool === "laser") {
          endLaser();
          return;
        }
        const drawing = drawingRef.current;
        if (!drawing || drawing.pointerId !== event.pointerId) return;
        const point = pointerToNorm(event, rootRef.current);
        onLocalStroke({ strokeId: drawing.strokeId, phase: "end", points: [point] });
        drawingRef.current = null;
      }}
      onPointerCancel={() => {
        const drawing = drawingRef.current;
        if (drawing) {
          onLocalStroke({ strokeId: drawing.strokeId, phase: "end", points: [] });
          drawingRef.current = null;
        }
        if (tool === "laser") endLaser();
      }}
      onPointerLeave={() => {
        if (tool === "laser") endLaser();
      }}
    >
      <svg
        className="tdp-meeting-annotation__ink"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        {visibleStrokes.map((stroke) => (
          <path
            key={stroke.strokeId}
            className="tdp-meeting-annotation__stroke"
            d={meetingPointsToSvgPath(stroke.points)}
            fill="none"
            stroke={MEETING_INK_COLOR}
            strokeWidth={MEETING_INK_WIDTH_PX}
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      {visibleLasers.map((laser) => (
        <span
          key={laser.clientId}
          className="tdp-meeting-annotation__laser"
          style={{ left: `${laser.x * 100}%`, top: `${laser.y * 100}%` }}
        />
      ))}
    </div>
  );
}
