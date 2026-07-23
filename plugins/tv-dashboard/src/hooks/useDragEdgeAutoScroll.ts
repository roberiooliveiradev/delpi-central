import { useEffect, useRef, type RefObject } from "react";

import {
  scrollContainerOnDragEdge,
  type DragEdgeScrollOptions,
} from "../utils/scrollContainerOnDragEdge";

/**
 * Enquanto `active`, acompanha `dragover` e mantém rAF para scroll automático
 * nas bordas do container (útil ao reordenar itens longos na lista).
 */
export function useDragEdgeAutoScroll(
  containerRef: RefObject<HTMLElement | null>,
  active: boolean,
  options?: DragEdgeScrollOptions,
) {
  const optionsRef = useRef(options);
  optionsRef.current = options;

  useEffect(() => {
    if (!active) return;

    let armed = false;
    let lastClientY = 0;
    let rafId = 0;

    const onDragOver = (event: DragEvent) => {
      if (!Number.isFinite(event.clientY)) return;
      armed = true;
      lastClientY = event.clientY;
      const el = containerRef.current;
      if (el) scrollContainerOnDragEdge(el, lastClientY, optionsRef.current);
    };

    const tick = () => {
      const el = containerRef.current;
      if (armed && el) {
        scrollContainerOnDragEdge(el, lastClientY, optionsRef.current);
      }
      rafId = window.requestAnimationFrame(tick);
    };

    window.addEventListener("dragover", onDragOver, { passive: true });
    rafId = window.requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("dragover", onDragOver);
      window.cancelAnimationFrame(rafId);
    };
  }, [active, containerRef]);
}
