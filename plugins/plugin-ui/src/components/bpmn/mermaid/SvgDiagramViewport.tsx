import {
  useCallback,
  useLayoutEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
  type WheelEvent as ReactWheelEvent,
} from "react";

import { DiagramViewportControls, type DiagramViewportControlLabels } from "../editor/DiagramViewportControls";
import {
  clampDiagramZoom,
  computeFitTransform,
  computeResetTransform,
  type DiagramContentBounds,
  type DiagramViewportTransform,
  measureSvgWorldSize,
  panViewport,
  zoomViewportAt,
} from "../layout/diagramViewport";

type Props = {
  labels: DiagramViewportControlLabels;
  worldWidth: number;
  worldHeight: number;
  children: ReactNode;
  className?: string;
};

const EMPTY_TRANSFORM: DiagramViewportTransform = { x: 0, y: 0, zoom: 1 };

function boundsFromWorld(width: number, height: number): DiagramContentBounds {
  return {
    minX: 0,
    minY: 0,
    maxX: Math.max(1, width),
    maxY: Math.max(1, height),
  };
}

export function SvgDiagramViewport({
  labels,
  worldWidth,
  worldHeight,
  children,
  className,
}: Props) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const intentRef = useRef<"fit" | "user">("fit");
  const transformRef = useRef<DiagramViewportTransform>(EMPTY_TRANSFORM);
  const dragRef = useRef<{ pointerId: number; lastX: number; lastY: number } | null>(null);
  const worldRef = useRef({ width: Math.max(1, worldWidth), height: Math.max(1, worldHeight) });
  const [transform, setTransform] = useState<DiagramViewportTransform>(EMPTY_TRANSFORM);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });
  const [measuredWorld, setMeasuredWorld] = useState({
    width: Math.max(1, worldWidth),
    height: Math.max(1, worldHeight),
  });

  transformRef.current = transform;
  worldRef.current = measuredWorld;
  const worldBounds = boundsFromWorld(measuredWorld.width, measuredWorld.height);

  const applyTransform = useCallback((next: DiagramViewportTransform, intent: "fit" | "user") => {
    intentRef.current = intent;
    transformRef.current = next;
    setTransform(next);
  }, []);

  const fitToView = useCallback(
    (size = viewportSize) => {
      if (size.width < 8 || size.height < 8) return;
      const bounds = boundsFromWorld(worldRef.current.width, worldRef.current.height);
      if (bounds.maxX <= 1 && bounds.maxY <= 1) return;
      applyTransform(computeFitTransform(bounds, size), "fit");
    },
    [applyTransform, viewportSize]
  );

  const resetView = useCallback(() => {
    if (viewportSize.width < 8 || viewportSize.height < 8) return;
    applyTransform(computeResetTransform(worldBounds, viewportSize), "user");
  }, [applyTransform, viewportSize, worldBounds.maxX, worldBounds.maxY]);

  useLayoutEffect(() => {
    const next = { width: Math.max(1, worldWidth), height: Math.max(1, worldHeight) };
    worldRef.current = next;
    setMeasuredWorld(next);
    intentRef.current = "fit";
  }, [worldWidth, worldHeight]);

  useLayoutEffect(() => {
    const svg = viewportRef.current?.querySelector<SVGSVGElement>(
      ":scope > .delpi-ui-bpmn-svg-viewport__world svg"
    );
    if (!svg) return;
    const measured = measureSvgWorldSize(svg);
    if (measured.width <= 1 || measured.height <= 1) return;
    worldRef.current = measured;
    setMeasuredWorld((current) =>
      current.width === measured.width && current.height === measured.height ? current : measured
    );
    intentRef.current = "fit";
  }, [children, worldWidth, worldHeight]);

  useLayoutEffect(() => {
    const element = viewportRef.current;
    if (!element) return;

    const measureViewport = () => {
      const rect = element.getBoundingClientRect();
      const next = { width: rect.width, height: rect.height };
      setViewportSize(next);
      if (intentRef.current !== "fit" || next.width < 8 || next.height < 8) return;
      const bounds = boundsFromWorld(worldRef.current.width, worldRef.current.height);
      if (bounds.maxX <= 1 && bounds.maxY <= 1) return;
      applyTransform(computeFitTransform(bounds, next), "fit");
    };

    measureViewport();
    if (typeof ResizeObserver === "undefined") {
      return;
    }
    const observer = new ResizeObserver(measureViewport);
    observer.observe(element);
    return () => observer.disconnect();
  }, [applyTransform, measuredWorld.height, measuredWorld.width]);

  const onPointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    const target = event.target as HTMLElement | null;
    if (target?.closest("button, input, textarea, [data-diagram-viewport-chrome]")) {
      return;
    }
    dragRef.current = { pointerId: event.pointerId, lastX: event.clientX, lastY: event.clientY };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const onPointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) return;
    applyTransform(
      panViewport(transformRef.current, event.clientX - drag.lastX, event.clientY - drag.lastY),
      "user"
    );
    drag.lastX = event.clientX;
    drag.lastY = event.clientY;
  };

  const endDrag = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (dragRef.current?.pointerId === event.pointerId) {
      dragRef.current = null;
    }
  };

  const onWheel = (event: ReactWheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
    const nextZoom = transformRef.current.zoom * (event.deltaY > 0 ? 0.9 : 1.1);
    applyTransform(
      zoomViewportAt(transformRef.current, nextZoom, {
        x: event.clientX - rect.left,
        y: event.clientY - rect.top,
      }),
      "user"
    );
  };

  const classes = ["delpi-ui-bpmn-svg-viewport", className].filter(Boolean).join(" ");

  return (
    <div
      ref={viewportRef}
      className={classes}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onWheel={onWheel}
    >
      <div
        className="delpi-ui-bpmn-svg-viewport__world"
        style={{
          width: worldBounds.maxX,
          height: worldBounds.maxY,
          transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.zoom})`,
        }}
      >
        {children}
      </div>
      <div className="delpi-ui-bpmn-svg-viewport__chrome" data-diagram-viewport-chrome>
        <DiagramViewportControls
          labels={labels}
          zoom={transform.zoom}
          onZoomChange={(nextZoom) => {
            const rect = viewportRef.current?.getBoundingClientRect();
            if (!rect) {
              applyTransform(
                { ...transformRef.current, zoom: clampDiagramZoom(nextZoom) },
                "user"
              );
              return;
            }
            applyTransform(
              zoomViewportAt(transformRef.current, nextZoom, {
                x: rect.width / 2,
                y: rect.height / 2,
              }),
              "user"
            );
          }}
          onFit={() => fitToView()}
          onReset={resetView}
        />
      </div>
    </div>
  );
}
