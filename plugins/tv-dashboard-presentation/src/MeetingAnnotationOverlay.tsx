import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  type PointerEvent as ReactPointerEvent,
} from "react";

import {
  MEETING_INK_COLOR,
  MEETING_INK_WIDTH_PX,
  type MeetingAnnotationTool,
  type MeetingInkStroke,
  type MeetingNormPoint,
} from "./meetingAnnotationTypes";
import {
  createMeetingStrokeId,
  meetingPointsToSvgPath,
  normalizeMeetingPoint,
  strokesForSlide,
} from "./meetingInkModel";
import "./meeting-annotation.css";

export type MeetingRemoteLaserEvent = {
  clientId: string;
  slideId: string;
  x: number;
  y: number;
  visible: boolean;
};

export type MeetingAnnotationOverlayHandle = {
  paintRemoteLaser: (event: MeetingRemoteLaserEvent) => void;
  clearLasersForSlide: (slideId: string) => void;
};

export type MeetingAnnotationOverlayProps = {
  enabled: boolean;
  slideId: string;
  clientId: string;
  tool: MeetingAnnotationTool;
  strokes: MeetingInkStroke[];
  onLocalStroke: (event: {
    strokeId: string;
    phase: "start" | "move" | "end";
    points: MeetingNormPoint[];
  }) => void;
  /** Throttled network publish only — local paint is DOM/rAF, no parent setState. */
  onLocalLaserNetwork: (event: { x: number; y: number; visible: boolean }) => void;
};

/** Idle sem movimento some o laser (estilo PowerPoint). */
const LASER_IDLE_HIDE_MS = 1800;
const LASER_NETWORK_THROTTLE_MS = 90;

function pointerToNorm(
  event: ReactPointerEvent<HTMLDivElement>,
  el: HTMLDivElement,
): MeetingNormPoint {
  const rect = el.getBoundingClientRect();
  const w = rect.width || 1;
  const h = rect.height || 1;
  return normalizeMeetingPoint((event.clientX - rect.left) / w, (event.clientY - rect.top) / h);
}

type RemoteLaserEntry = {
  slideId: string;
  x: number;
  y: number;
  visible: boolean;
};

/**
 * Overlay efêmero de caneta/laser (modo reunião).
 * Laser: paint local/remoto via DOM + rAF — sem re-render do deck por movimento.
 */
export const MeetingAnnotationOverlay = forwardRef<
  MeetingAnnotationOverlayHandle,
  MeetingAnnotationOverlayProps
>(function MeetingAnnotationOverlay(
  {
    enabled,
    slideId,
    clientId,
    tool,
    strokes,
    onLocalStroke,
    onLocalLaserNetwork,
  },
  ref,
) {
  const rootRef = useRef<HTMLDivElement>(null);
  const localLaserRef = useRef<HTMLSpanElement>(null);
  const remoteLayerRef = useRef<HTMLDivElement>(null);
  const remoteLaserElsRef = useRef<Map<string, HTMLSpanElement>>(new Map());
  const remoteLaserStateRef = useRef<Map<string, RemoteLaserEntry>>(new Map());
  const drawingRef = useRef<{ strokeId: string; pointerId: number } | null>(null);
  const laserIdleTimerRef = useRef<number | null>(null);
  const paintRafRef = useRef<number | null>(null);
  const localLaserVisibleRef = useRef(false);
  const localLaserPointRef = useRef<MeetingNormPoint>({ x: 0.5, y: 0.5 });
  const lastNetworkAtRef = useRef(0);
  const pendingNetworkRef = useRef<{ x: number; y: number; visible: boolean } | null>(null);
  const networkTimerRef = useRef<number | null>(null);
  const onLocalLaserNetworkRef = useRef(onLocalLaserNetwork);
  onLocalLaserNetworkRef.current = onLocalLaserNetwork;

  useEffect(() => {
    drawingRef.current = null;
  }, [slideId]);

  const applyLaserTransform = useCallback(
    (el: HTMLSpanElement, point: MeetingNormPoint, root: HTMLDivElement) => {
      const w = root.clientWidth || 1;
      const h = root.clientHeight || 1;
      el.style.transform = `translate3d(${point.x * w}px, ${point.y * h}px, 0) translate(-50%, -50%)`;
    },
    [],
  );

  const paintLasers = useCallback(() => {
    paintRafRef.current = null;
    const root = rootRef.current;
    const localEl = localLaserRef.current;
    if (!root) return;

    if (localEl) {
      localEl.style.opacity = localLaserVisibleRef.current ? "1" : "0";
      if (localLaserVisibleRef.current) {
        applyLaserTransform(localEl, localLaserPointRef.current, root);
      }
    }

    const layer = remoteLayerRef.current;
    if (!layer) return;

    for (const [remoteClientId, state] of remoteLaserStateRef.current) {
      let el = remoteLaserElsRef.current.get(remoteClientId);
      if (!el) {
        el = document.createElement("span");
        el.className = "tdp-meeting-annotation__laser";
        el.dataset.clientId = remoteClientId;
        layer.appendChild(el);
        remoteLaserElsRef.current.set(remoteClientId, el);
      }
      const show = state.visible && state.slideId === slideId;
      el.style.opacity = show ? "1" : "0";
      if (show) {
        applyLaserTransform(el, { x: state.x, y: state.y }, root);
      }
    }
  }, [applyLaserTransform, slideId]);

  const scheduleLaserPaint = useCallback(() => {
    if (paintRafRef.current != null) return;
    paintRafRef.current = window.requestAnimationFrame(paintLasers);
  }, [paintLasers]);

  useEffect(() => {
    scheduleLaserPaint();
  }, [slideId, scheduleLaserPaint]);

  const flushLaserNetwork = useCallback(() => {
    networkTimerRef.current = null;
    const pending = pendingNetworkRef.current;
    if (!pending) return;
    pendingNetworkRef.current = null;
    lastNetworkAtRef.current = performance.now();
    onLocalLaserNetworkRef.current(pending);
  }, []);

  const emitLaserNetwork = useCallback(
    (event: { x: number; y: number; visible: boolean }) => {
      pendingNetworkRef.current = event;
      const now = performance.now();
      const elapsed = now - lastNetworkAtRef.current;
      if (elapsed >= LASER_NETWORK_THROTTLE_MS) {
        flushLaserNetwork();
        return;
      }
      if (networkTimerRef.current == null) {
        networkTimerRef.current = window.setTimeout(
          flushLaserNetwork,
          LASER_NETWORK_THROTTLE_MS - elapsed,
        );
      }
    },
    [flushLaserNetwork],
  );

  const clearLaserIdleTimer = useCallback(() => {
    if (laserIdleTimerRef.current != null) {
      window.clearTimeout(laserIdleTimerRef.current);
      laserIdleTimerRef.current = null;
    }
  }, []);

  const hideLocalLaser = useCallback(() => {
    clearLaserIdleTimer();
    localLaserVisibleRef.current = false;
    scheduleLaserPaint();
    emitLaserNetwork({ x: localLaserPointRef.current.x, y: localLaserPointRef.current.y, visible: false });
  }, [clearLaserIdleTimer, emitLaserNetwork, scheduleLaserPaint]);

  const showLocalLaserAt = useCallback(
    (point: MeetingNormPoint) => {
      localLaserPointRef.current = point;
      localLaserVisibleRef.current = true;
      scheduleLaserPaint();
      emitLaserNetwork({ ...point, visible: true });
      clearLaserIdleTimer();
      laserIdleTimerRef.current = window.setTimeout(() => {
        laserIdleTimerRef.current = null;
        localLaserVisibleRef.current = false;
        scheduleLaserPaint();
        emitLaserNetwork({ ...point, visible: false });
      }, LASER_IDLE_HIDE_MS);
    },
    [clearLaserIdleTimer, emitLaserNetwork, scheduleLaserPaint],
  );

  useImperativeHandle(
    ref,
    () => ({
      paintRemoteLaser: (event: MeetingRemoteLaserEvent) => {
        if (event.clientId === clientId) return;
        if (!event.visible) {
          remoteLaserStateRef.current.delete(event.clientId);
          const el = remoteLaserElsRef.current.get(event.clientId);
          if (el) el.style.opacity = "0";
          return;
        }
        remoteLaserStateRef.current.set(event.clientId, {
          slideId: event.slideId,
          x: event.x,
          y: event.y,
          visible: true,
        });
        scheduleLaserPaint();
      },
      clearLasersForSlide: (targetSlideId: string) => {
        for (const [remoteClientId, state] of remoteLaserStateRef.current) {
          if (state.slideId !== targetSlideId) continue;
          state.visible = false;
          const el = remoteLaserElsRef.current.get(remoteClientId);
          if (el) el.style.opacity = "0";
        }
        scheduleLaserPaint();
      },
    }),
    [clientId, scheduleLaserPaint],
  );

  useEffect(() => {
    if (tool !== "laser") {
      hideLocalLaser();
    }
    return () => {
      clearLaserIdleTimer();
      if (networkTimerRef.current != null) {
        window.clearTimeout(networkTimerRef.current);
        networkTimerRef.current = null;
      }
      if (paintRafRef.current != null) {
        window.cancelAnimationFrame(paintRafRef.current);
        paintRafRef.current = null;
      }
    };
  }, [tool, hideLocalLaser, clearLaserIdleTimer]);

  const visibleStrokes = strokesForSlide(strokes, slideId);

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
        if (tool === "laser") {
          showLocalLaserAt(pointerToNorm(event, rootRef.current));
          return;
        }
        event.preventDefault();
        rootRef.current.setPointerCapture(event.pointerId);
        const point = pointerToNorm(event, rootRef.current);
        const strokeId = createMeetingStrokeId(clientId);
        drawingRef.current = { strokeId, pointerId: event.pointerId };
        onLocalStroke({ strokeId, phase: "start", points: [point] });
      }}
      onPointerMove={(event) => {
        if (!interactive || !rootRef.current) return;
        if (tool === "laser") {
          showLocalLaserAt(pointerToNorm(event, rootRef.current));
          return;
        }
        const drawing = drawingRef.current;
        if (!drawing || drawing.pointerId !== event.pointerId) return;
        const point = pointerToNorm(event, rootRef.current);
        onLocalStroke({ strokeId: drawing.strokeId, phase: "move", points: [point] });
      }}
      onPointerEnter={(event) => {
        if (tool !== "laser" || !rootRef.current) return;
        showLocalLaserAt(pointerToNorm(event, rootRef.current));
      }}
      onPointerUp={(event) => {
        if (tool === "laser") return;
        if (!rootRef.current) return;
        try {
          rootRef.current.releasePointerCapture(event.pointerId);
        } catch {
          // ignore
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
        if (tool === "laser") hideLocalLaser();
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
      <div
        ref={remoteLayerRef}
        className="tdp-meeting-annotation__remote-lasers"
        aria-hidden="true"
      />
      <span
        ref={localLaserRef}
        className="tdp-meeting-annotation__laser tdp-meeting-annotation__laser--local"
        aria-hidden="true"
        style={{ opacity: 0 }}
      />
    </div>
  );
});

MeetingAnnotationOverlay.displayName = "MeetingAnnotationOverlay";
