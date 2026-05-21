import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from "react";

export type PanZoomTransform = {
  x: number;
  y: number;
  scale: number;
};

type UsePanZoomOptions = {
  minScale?: number;
  maxScale?: number;
  zoomStep?: number;
  fitPadding?: number;
  fitToken?: string | number;
};

const DEFAULT_TRANSFORM: PanZoomTransform = { x: 0, y: 0, scale: 1 };

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function isInteractivePanTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }

  return Boolean(
    target.closest(
      'button, a, input, select, textarea, label, [data-pan-zoom-lock="true"]',
    ),
  );
}

export function usePanZoom({
  minScale = 0.25,
  maxScale = 2.5,
  zoomStep = 0.15,
  fitPadding = 48,
  fitToken,
}: UsePanZoomOptions = {}) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [transform, setTransform] = useState<PanZoomTransform>(DEFAULT_TRANSFORM);
  const [isDragging, setIsDragging] = useState(false);
  const spacePressedRef = useRef(false);
  const dragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);
  const pinchRef = useRef<{
    distance: number;
    scale: number;
    midpointX: number;
    midpointY: number;
    originX: number;
    originY: number;
  } | null>(null);

  const applyZoomAtPoint = useCallback(
    (clientX: number, clientY: number, nextScale: number) => {
      const viewport = viewportRef.current;
      if (!viewport) return;

      const rect = viewport.getBoundingClientRect();
      const pointerX = clientX - rect.left;
      const pointerY = clientY - rect.top;

      setTransform((current) => {
        const scale = clamp(nextScale, minScale, maxScale);
        const ratio = scale / current.scale;

        return {
          scale,
          x: pointerX - (pointerX - current.x) * ratio,
          y: pointerY - (pointerY - current.y) * ratio,
        };
      });
    },
    [maxScale, minScale],
  );

  const zoomIn = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const rect = viewport.getBoundingClientRect();
    applyZoomAtPoint(
      rect.left + rect.width / 2,
      rect.top + rect.height / 2,
      transform.scale * (1 + zoomStep),
    );
  }, [applyZoomAtPoint, transform.scale, zoomStep]);

  const zoomOut = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const rect = viewport.getBoundingClientRect();
    applyZoomAtPoint(
      rect.left + rect.width / 2,
      rect.top + rect.height / 2,
      transform.scale * (1 - zoomStep),
    );
  }, [applyZoomAtPoint, transform.scale, zoomStep]);

  const resetView = useCallback(() => {
    setTransform(DEFAULT_TRANSFORM);
  }, []);

  const fitToView = useCallback(() => {
    const viewport = viewportRef.current;
    const content = contentRef.current;
    if (!viewport || !content) return;

    const viewportWidth = viewport.clientWidth;
    const viewportHeight = viewport.clientHeight;
    const contentWidth = content.offsetWidth;
    const contentHeight = content.offsetHeight;

    if (!contentWidth || !contentHeight) {
      resetView();
      return;
    }

    const scale = clamp(
      Math.min(
        (viewportWidth - fitPadding) / contentWidth,
        (viewportHeight - fitPadding) / contentHeight,
      ),
      minScale,
      maxScale,
    );

    const x = (viewportWidth - contentWidth * scale) / 2;
    const y = Math.max(fitPadding / 4, (viewportHeight - contentHeight * scale) / 2);

    setTransform({ x, y, scale });
  }, [fitPadding, maxScale, minScale, resetView]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.code === "Space" && !event.repeat) {
        spacePressedRef.current = true;
      }
    };

    const onKeyUp = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        spacePressedRef.current = false;
        setIsDragging(false);
        dragRef.current = null;
      }
    };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);

    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, []);

  useEffect(() => {
    if (fitToken === undefined) return;

    const frame = window.requestAnimationFrame(() => {
      fitToView();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [fitToken, fitToView]);

  const canStartPan = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
    if (isInteractivePanTarget(event.target)) {
      return false;
    }

    return event.button === 1 || event.button === 0;
  }, []);

  const handlePointerDown = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      if (!canStartPan(event)) {
        return;
      }

      event.preventDefault();
      dragRef.current = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        originX: transform.x,
        originY: transform.y,
      };
      setIsDragging(true);
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    [canStartPan, transform.x, transform.y],
  );

  const handlePointerMove = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
    const drag = dragRef.current;
    if (!drag || drag.pointerId !== event.pointerId) {
      return;
    }

    setTransform((current) => ({
      ...current,
      x: drag.originX + (event.clientX - drag.startX),
      y: drag.originY + (event.clientY - drag.startY),
    }));
  }, []);

  const endDrag = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
    if (dragRef.current?.pointerId === event.pointerId) {
      dragRef.current = null;
      setIsDragging(false);
      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
    }
  }, []);

  const handleWheel = useCallback(
    (event: ReactWheelEvent<HTMLDivElement>) => {
      event.preventDefault();
      const factor = event.deltaY < 0 ? 1 + zoomStep : 1 - zoomStep;
      applyZoomAtPoint(
        event.clientX,
        event.clientY,
        transform.scale * factor,
      );
    },
    [applyZoomAtPoint, transform.scale, zoomStep],
  );

  const getTouchDistance = (touches: React.TouchList) => {
    if (touches.length < 2) return 0;
    const first = touches[0];
    const second = touches[1];
    const dx = first.clientX - second.clientX;
    const dy = first.clientY - second.clientY;
    return Math.hypot(dx, dy);
  };

  const handleTouchStart = useCallback(
    (event: React.TouchEvent<HTMLDivElement>) => {
      if (event.touches.length !== 2 || !viewportRef.current) return;

      const viewport = viewportRef.current;
      const rect = viewport.getBoundingClientRect();
      const distance = getTouchDistance(event.touches);
      const midpointX =
        (event.touches[0].clientX + event.touches[1].clientX) / 2 - rect.left;
      const midpointY =
        (event.touches[0].clientY + event.touches[1].clientY) / 2 - rect.top;

      pinchRef.current = {
        distance,
        scale: transform.scale,
        midpointX,
        midpointY,
        originX: transform.x,
        originY: transform.y,
      };
    },
    [transform.scale, transform.x, transform.y],
  );

  const handleTouchMove = useCallback((event: React.TouchEvent<HTMLDivElement>) => {
    const pinch = pinchRef.current;
    if (!pinch || event.touches.length !== 2) return;

    event.preventDefault();
    const distance = getTouchDistance(event.touches);
    if (!distance || !pinch.distance) return;

    const nextScale = clamp(
      pinch.scale * (distance / pinch.distance),
      minScale,
      maxScale,
    );
    const ratio = nextScale / pinch.scale;

    setTransform({
      scale: nextScale,
      x: pinch.midpointX - (pinch.midpointX - pinch.originX) * ratio,
      y: pinch.midpointY - (pinch.midpointY - pinch.originY) * ratio,
    });
  }, [maxScale, minScale]);

  const handleTouchEnd = useCallback(() => {
    pinchRef.current = null;
  }, []);

  const surfaceStyle = {
    transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
  };

  const zoomPercent = Math.round(transform.scale * 100);

  return {
    viewportRef,
    contentRef,
    transform,
    surfaceStyle,
    zoomPercent,
    isDragging,
    zoomIn,
    zoomOut,
    resetView,
    fitToView,
    viewportProps: {
      onWheel: handleWheel,
      onPointerDown: handlePointerDown,
      onPointerMove: handlePointerMove,
      onPointerUp: endDrag,
      onPointerCancel: endDrag,
      onTouchStart: handleTouchStart,
      onTouchMove: handleTouchMove,
      onTouchEnd: handleTouchEnd,
      onTouchCancel: handleTouchEnd,
    },
  };
}
