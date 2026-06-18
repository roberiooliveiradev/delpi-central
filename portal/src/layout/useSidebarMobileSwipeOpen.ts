import { useCallback, useEffect, useRef, useState } from "react";

import { isPortalSidebarEdgeHoldPoint } from "../utils/sidebar";

export const PORTAL_SIDEBAR_SWIPE_COMMIT_PX = 14;
export const PORTAL_SIDEBAR_SWIPE_OPEN_RATIO = 0.28;
export const PORTAL_SIDEBAR_SWIPE_OPEN_MIN_PX = 72;
export const PORTAL_SIDEBAR_SWIPE_HORIZONTAL_RATIO = 1.35;

const SWIPE_IGNORE_SELECTOR =
  "input, textarea, select, [contenteditable='true'], [data-portal-sidebar-swipe-ignore]";

type UseSidebarMobileSwipeOpenOptions = {
  enabled: boolean;
  sidebarRef: React.RefObject<HTMLElement | null>;
  onOpen: () => void;
  onSwipeStart?: () => void;
};

function shouldIgnoreSwipeTarget(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;
  return Boolean(target.closest(SWIPE_IGNORE_SELECTOR));
}

function isHorizontallyScrollableAncestor(element: Element | null): boolean {
  let node = element;

  while (node && node !== document.body) {
    if (!(node instanceof HTMLElement)) break;

    const { overflowX } = getComputedStyle(node);
    if (
      (overflowX === "auto" || overflowX === "scroll" || overflowX === "overlay") &&
      node.scrollWidth > node.clientWidth + 1
    ) {
      return true;
    }

    node = node.parentElement;
  }

  return false;
}

function resolveMobileSidebarWidth(sidebar: HTMLElement | null): number {
  if (sidebar) {
    const width = sidebar.getBoundingClientRect().width;
    if (width > 0) return width;
  }

  if (window.matchMedia("(max-width: 640px)").matches) {
    return window.innerWidth * 0.85;
  }

  return 280;
}

export function useSidebarMobileSwipeOpen({
  enabled,
  sidebarRef,
  onOpen,
  onSwipeStart,
}: UseSidebarMobileSwipeOpenOptions) {
  const onOpenRef = useRef(onOpen);
  const onSwipeStartRef = useRef(onSwipeStart);
  const activeListenersRef = useRef<(() => void) | null>(null);

  const [swipeOffsetPx, setSwipeOffsetPx] = useState(0);
  const [isSwipeDragging, setIsSwipeDragging] = useState(false);

  useEffect(() => {
    onOpenRef.current = onOpen;
    onSwipeStartRef.current = onSwipeStart;
  }, [onOpen, onSwipeStart]);

  const clearActiveListeners = useCallback(() => {
    activeListenersRef.current?.();
    activeListenersRef.current = null;
  }, []);

  const resetSwipe = useCallback(() => {
    clearActiveListeners();
    setIsSwipeDragging(false);
    setSwipeOffsetPx(0);
  }, [clearActiveListeners]);

  useEffect(() => {
    if (!enabled) {
      resetSwipe();
      return;
    }

    const drag = {
      pointerId: -1,
      startX: 0,
      startY: 0,
      committed: false,
      sidebarWidth: 280,
    };

    const finishSwipe = (offset: number) => {
      const openThreshold = Math.max(
        PORTAL_SIDEBAR_SWIPE_OPEN_MIN_PX,
        drag.sidebarWidth * PORTAL_SIDEBAR_SWIPE_OPEN_RATIO,
      );

      clearActiveListeners();
      setIsSwipeDragging(false);
      setSwipeOffsetPx(0);

      if (offset >= openThreshold) {
        onOpenRef.current();
      }
    };

    const onPointerDown = (event: PointerEvent) => {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      if (!isPortalSidebarEdgeHoldPoint(event.clientX, event.clientY)) return;
      if (shouldIgnoreSwipeTarget(event.target)) return;
      if (isHorizontallyScrollableAncestor(event.target instanceof Element ? event.target : null)) {
        return;
      }

      clearActiveListeners();

      drag.pointerId = event.pointerId;
      drag.startX = event.clientX;
      drag.startY = event.clientY;
      drag.committed = false;
      drag.sidebarWidth = resolveMobileSidebarWidth(sidebarRef.current);

      const onPointerMove = (moveEvent: PointerEvent) => {
        if (moveEvent.pointerId !== drag.pointerId) return;

        const deltaX = moveEvent.clientX - drag.startX;
        const deltaY = moveEvent.clientY - drag.startY;
        const absX = Math.abs(deltaX);
        const absY = Math.abs(deltaY);

        if (!drag.committed) {
          if (deltaX <= 0 || absX < PORTAL_SIDEBAR_SWIPE_COMMIT_PX) return;
          if (absX < absY * PORTAL_SIDEBAR_SWIPE_HORIZONTAL_RATIO) return;

          drag.committed = true;
          setIsSwipeDragging(true);
          onSwipeStartRef.current?.();
        }

        moveEvent.preventDefault();

        const offset = Math.min(Math.max(deltaX, 0), drag.sidebarWidth);
        setSwipeOffsetPx(offset);
      };

      const onPointerEnd = (endEvent: PointerEvent) => {
        if (endEvent.pointerId !== drag.pointerId) return;

        const deltaX = endEvent.clientX - drag.startX;

        if (drag.committed) {
          finishSwipe(Math.min(Math.max(deltaX, 0), drag.sidebarWidth));
          return;
        }

        clearActiveListeners();
      };

      window.addEventListener("pointermove", onPointerMove, { passive: false });
      window.addEventListener("pointerup", onPointerEnd, { passive: true });
      window.addEventListener("pointercancel", onPointerEnd, { passive: true });

      activeListenersRef.current = () => {
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerup", onPointerEnd);
        window.removeEventListener("pointercancel", onPointerEnd);
      };
    };

    window.addEventListener("pointerdown", onPointerDown, { passive: true });

    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      resetSwipe();
    };
  }, [enabled, resetSwipe, sidebarRef, clearActiveListeners]);

  const swipeBackdropOpacity = Math.min(
    0.42,
    (swipeOffsetPx / Math.max(resolveMobileSidebarWidth(sidebarRef.current), 1)) * 0.42,
  );

  return {
    swipeOffsetPx,
    isSwipeDragging,
    swipeBackdropOpacity,
    resetSwipe,
  };
}
