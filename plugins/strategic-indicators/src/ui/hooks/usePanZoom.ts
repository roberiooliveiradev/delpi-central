import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type WheelEvent as ReactWheelEvent,
} from "react";
import {
  loadPersistedPanZoomTransform,
  savePersistedPanZoomTransform,
} from "./panZoomViewPersistence";

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
  /** Quando true, refaz fit ao mudar o token (ex.: layout novo). */
  autoFitOnTokenChange?: boolean;
  fitToken?: string | number;
  /** Restaura zoom/posição entre recargas de dados e mudanças de filtro. */
  persistKey?: string;
  /** Ajusta à tela na primeira visita se não houver vista salva. */
  fitOnMount?: boolean;
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

function isMobileFitViewport() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.matchMedia("(max-width: 1024px)").matches;
}

function getTouchDistance(touches: TouchList) {
  if (touches.length < 2) {
    return 0;
  }

  const first = touches[0];
  const second = touches[1];
  return Math.hypot(
    first.clientX - second.clientX,
    first.clientY - second.clientY,
  );
}

export function usePanZoom({
  minScale = 0.25,
  maxScale = 2.5,
  zoomStep = 0.15,
  fitPadding = 48,
  autoFitOnTokenChange = false,
  fitToken,
  persistKey,
  fitOnMount = true,
}: UsePanZoomOptions = {}) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [transform, setTransform] = useState<PanZoomTransform>(() => {
    if (!persistKey) {
      return DEFAULT_TRANSFORM;
    }

    return loadPersistedPanZoomTransform(persistKey) ?? DEFAULT_TRANSFORM;
  });
  const didInitialFitRef = useRef(false);
  const [isDragging, setIsDragging] = useState(false);
  const transformRef = useRef(transform);
  const spacePressedRef = useRef(false);
  const dragRef = useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);
  const touchPanRef = useRef<{
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

  useEffect(() => {
    transformRef.current = transform;
  }, [transform]);

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
      transformRef.current.scale * (1 + zoomStep),
    );
  }, [applyZoomAtPoint, zoomStep]);

  const zoomOut = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const rect = viewport.getBoundingClientRect();
    applyZoomAtPoint(
      rect.left + rect.width / 2,
      rect.top + rect.height / 2,
      transformRef.current.scale * (1 - zoomStep),
    );
  }, [applyZoomAtPoint, zoomStep]);

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

    const mobile = isMobileFitViewport();
    const mobileMinScale = Math.max(minScale, 0.55);

    if (mobile) {
      const scale = clamp(
        (viewportWidth - fitPadding) / contentWidth,
        mobileMinScale,
        1,
      );
      const x = (viewportWidth - contentWidth * scale) / 2;
      const y = Math.max(12, fitPadding / 4);

      setTransform({ x, y, scale });
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
    if (!persistKey) {
      return;
    }

    const handle = window.setTimeout(() => {
      savePersistedPanZoomTransform(persistKey, transformRef.current);
    }, 120);

    return () => window.clearTimeout(handle);
  }, [persistKey, transform]);

  useEffect(() => {
    if (!fitOnMount || didInitialFitRef.current) {
      return;
    }

    if (persistKey && loadPersistedPanZoomTransform(persistKey)) {
      didInitialFitRef.current = true;
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      fitToView();
      didInitialFitRef.current = true;
    });

    return () => window.cancelAnimationFrame(frame);
  }, [fitOnMount, fitToView, persistKey]);

  useEffect(() => {
    if (!autoFitOnTokenChange || fitToken === undefined) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      fitToView();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [autoFitOnTokenChange, fitToken, fitToView]);

  const clearTouchGestures = useCallback(() => {
    touchPanRef.current = null;
    pinchRef.current = null;
  }, []);

  const applyPinch = useCallback(
    (touches: TouchList) => {
      const pinch = pinchRef.current;
      const viewport = viewportRef.current;
      if (!pinch || !viewport || touches.length !== 2) {
        return;
      }

      const distance = getTouchDistance(touches);
      if (!distance || !pinch.distance) {
        return;
      }

      const rect = viewport.getBoundingClientRect();
      const midpointX =
        (touches[0].clientX + touches[1].clientX) / 2 - rect.left;
      const midpointY =
        (touches[0].clientY + touches[1].clientY) / 2 - rect.top;
      const nextScale = clamp(
        pinch.scale * (distance / pinch.distance),
        minScale,
        maxScale,
      );
      const ratio = nextScale / pinch.scale;

      setTransform({
        scale: nextScale,
        x: midpointX - (midpointX - pinch.originX) * ratio,
        y: midpointY - (midpointY - pinch.originY) * ratio,
      });
    },
    [maxScale, minScale],
  );

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }

    const onTouchStart = (event: TouchEvent) => {
      if (event.touches.length === 2) {
        dragRef.current = null;
        touchPanRef.current = null;
        setIsDragging(false);

        const rect = viewport.getBoundingClientRect();
        const current = transformRef.current;
        const distance = getTouchDistance(event.touches);
        const midpointX =
          (event.touches[0].clientX + event.touches[1].clientX) / 2 - rect.left;
        const midpointY =
          (event.touches[0].clientY + event.touches[1].clientY) / 2 - rect.top;

        pinchRef.current = {
          distance,
          scale: current.scale,
          midpointX,
          midpointY,
          originX: current.x,
          originY: current.y,
        };
        return;
      }

      if (event.touches.length === 1 && !pinchRef.current) {
        if (isInteractivePanTarget(event.target)) {
          return;
        }

        const touch = event.touches[0];
        const current = transformRef.current;
        touchPanRef.current = {
          startX: touch.clientX,
          startY: touch.clientY,
          originX: current.x,
          originY: current.y,
        };
      }
    };

    const onTouchMove = (event: TouchEvent) => {
      if (event.touches.length === 2 && pinchRef.current) {
        event.preventDefault();
        applyPinch(event.touches);
        return;
      }

      const pan = touchPanRef.current;
      if (event.touches.length === 1 && pan && !pinchRef.current) {
        event.preventDefault();
        const touch = event.touches[0];
        setTransform((current) => ({
          ...current,
          x: pan.originX + (touch.clientX - pan.startX),
          y: pan.originY + (touch.clientY - pan.startY),
        }));
      }
    };

    const onTouchEnd = (event: TouchEvent) => {
      if (event.touches.length === 0) {
        clearTouchGestures();
        return;
      }

      if (event.touches.length === 1) {
        pinchRef.current = null;
        const touch = event.touches[0];
        const current = transformRef.current;
        touchPanRef.current = {
          startX: touch.clientX,
          startY: touch.clientY,
          originX: current.x,
          originY: current.y,
        };
      }
    };

    viewport.addEventListener("touchstart", onTouchStart, { passive: true });
    viewport.addEventListener("touchmove", onTouchMove, { passive: false });
    viewport.addEventListener("touchend", onTouchEnd, { passive: true });
    viewport.addEventListener("touchcancel", onTouchEnd, { passive: true });

    return () => {
      viewport.removeEventListener("touchstart", onTouchStart);
      viewport.removeEventListener("touchmove", onTouchMove);
      viewport.removeEventListener("touchend", onTouchEnd);
      viewport.removeEventListener("touchcancel", onTouchEnd);
    };
  }, [applyPinch, clearTouchGestures]);

  const canStartPan = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.pointerType === "touch") {
      return false;
    }

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
      clearTouchGestures();
      dragRef.current = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        originX: transformRef.current.x,
        originY: transformRef.current.y,
      };
      setIsDragging(true);
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    [canStartPan, clearTouchGestures],
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
        transformRef.current.scale * factor,
      );
    },
    [applyZoomAtPoint, zoomStep],
  );

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
    },
  };
}
