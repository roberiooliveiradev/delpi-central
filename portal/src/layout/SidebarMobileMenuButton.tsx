import { useCallback, useEffect, useRef, useState } from "react";
import { Menu } from "lucide-react";

const STORAGE_KEY = "portal-sidebar-mobile-menu-pos";
const BUTTON_SIZE_PX = 32;
const REVEAL_DURATION_MS = 3500;
const HOLD_TO_DRAG_MS = 400;

type MenuPosition = { x: number; y: number };

function readStoredPosition(): MenuPosition | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;

    const parsed = JSON.parse(raw) as Partial<MenuPosition>;
    if (
      typeof parsed.x === "number" &&
      Number.isFinite(parsed.x) &&
      typeof parsed.y === "number" &&
      Number.isFinite(parsed.y)
    ) {
      return { x: parsed.x, y: parsed.y };
    }
  } catch {
    /* ignore */
  }

  return null;
}

function clampPosition(position: MenuPosition): MenuPosition {
  const safeTop = 8;
  const safeLeft = 8;
  const safeRight = 8;
  const safeBottom = 8;
  const maxX = Math.max(safeLeft, window.innerWidth - BUTTON_SIZE_PX - safeRight);
  const maxY = Math.max(safeTop, window.innerHeight - BUTTON_SIZE_PX - safeBottom);

  return {
    x: Math.min(Math.max(position.x, safeLeft), maxX),
    y: Math.min(Math.max(position.y, safeTop), maxY),
  };
}

type SidebarMobileMenuButtonProps = {
  onOpen: () => void;
};

export function SidebarMobileMenuButton({ onOpen }: SidebarMobileMenuButtonProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const suppressClickRef = useRef(false);
  const activeListenersRef = useRef<(() => void) | null>(null);
  const revealTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [position, setPosition] = useState<MenuPosition | null>(() => readStoredPosition());
  const [isDragging, setIsDragging] = useState(false);
  const [isRevealed, setIsRevealed] = useState(false);

  const resolveCurrentPosition = useCallback((): MenuPosition => {
    if (position) return position;

    const button = buttonRef.current;
    if (!button) {
      return { x: 8, y: 8 };
    }

    const rect = button.getBoundingClientRect();
    return { x: rect.left, y: rect.top };
  }, [position]);

  const persistPosition = useCallback((next: MenuPosition) => {
    const clamped = clampPosition(next);
    setPosition(clamped);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(clamped));
  }, []);

  const clearActiveListeners = useCallback(() => {
    activeListenersRef.current?.();
    activeListenersRef.current = null;
  }, []);

  const revealBriefly = useCallback(() => {
    setIsRevealed(true);

    if (revealTimerRef.current) {
      clearTimeout(revealTimerRef.current);
    }

    revealTimerRef.current = setTimeout(() => {
      setIsRevealed(false);
      revealTimerRef.current = null;
    }, REVEAL_DURATION_MS);
  }, []);

  useEffect(() => {
    const onScreenTap = () => revealBriefly();

    document.addEventListener("pointerdown", onScreenTap, {
      capture: true,
      passive: true,
    });

    return () => {
      document.removeEventListener("pointerdown", onScreenTap, { capture: true });
      if (revealTimerRef.current) {
        clearTimeout(revealTimerRef.current);
        revealTimerRef.current = null;
      }
    };
  }, [revealBriefly]);

  useEffect(() => {
    return () => clearActiveListeners();
  }, [clearActiveListeners]);

  useEffect(() => {
    if (!position) return;

    const onResize = () => {
      setPosition((current) => (current ? clampPosition(current) : current));
    };

    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [position]);

  const handlePointerDown = (event: React.PointerEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    revealBriefly();

    if (event.pointerType === "mouse" && event.button !== 0) return;

    clearActiveListeners();

    const current = resolveCurrentPosition();
    const drag = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      originX: current.x,
      originY: current.y,
      dragEnabled: false,
      moved: false,
    };

    const holdTimer = window.setTimeout(() => {
      drag.dragEnabled = true;
      setIsDragging(true);
    }, HOLD_TO_DRAG_MS);

    const onPointerMove = (moveEvent: PointerEvent) => {
      if (moveEvent.pointerId !== drag.pointerId || !drag.dragEnabled) return;

      drag.moved = true;
      const deltaX = moveEvent.clientX - drag.startX;
      const deltaY = moveEvent.clientY - drag.startY;

      setPosition(
        clampPosition({
          x: drag.originX + deltaX,
          y: drag.originY + deltaY,
        }),
      );
    };

    const finishInteraction = (endEvent: PointerEvent) => {
      if (endEvent.pointerId !== drag.pointerId) return;

      window.clearTimeout(holdTimer);
      clearActiveListeners();
      setIsDragging(false);

      if (drag.moved) {
        const deltaX = endEvent.clientX - drag.startX;
        const deltaY = endEvent.clientY - drag.startY;
        persistPosition(
          clampPosition({
            x: drag.originX + deltaX,
            y: drag.originY + deltaY,
          }),
        );
        suppressClickRef.current = true;
      }
    };

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerup", finishInteraction);
    window.addEventListener("pointercancel", finishInteraction);

    activeListenersRef.current = () => {
      window.clearTimeout(holdTimer);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", finishInteraction);
      window.removeEventListener("pointercancel", finishInteraction);
    };
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();

    if (suppressClickRef.current) {
      suppressClickRef.current = false;
      return;
    }

    onOpen();
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onOpen();
  };

  return (
    <button
      ref={buttonRef}
      type="button"
      className={[
        "sidebar-mobile-menu-btn",
        position ? "sidebar-mobile-menu-btn--positioned" : "",
        isDragging ? "is-dragging" : "",
        isRevealed ? "is-revealed" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={
        position
          ? {
              top: `${position.y}px`,
              left: `${position.x}px`,
            }
          : undefined
      }
      aria-label="Abrir menu"
      aria-expanded={false}
      aria-controls="portal-sidebar"
      data-tour="sidebar-mobile-menu"
      onPointerDown={handlePointerDown}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
    >
      <Menu size={18} strokeWidth={2.25} aria-hidden="true" />
    </button>
  );
}
