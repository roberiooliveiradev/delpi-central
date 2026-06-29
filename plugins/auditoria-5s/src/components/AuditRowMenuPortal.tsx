import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";

const MENU_WIDTH = 168;
const MENU_GAP = 6;
const VIEWPORT_PADDING = 8;
const MENU_ITEM_HEIGHT = 40;

type Props = {
  open: boolean;
  onClose: () => void;
  triggerRef: RefObject<HTMLButtonElement | null>;
  itemCount: number;
  children: ReactNode;
};

function resolveMenuPosition(
  triggerRect: DOMRect,
  itemCount: number,
): { top: number; left: number } {
  const estimatedHeight = Math.max(itemCount, 1) * MENU_ITEM_HEIGHT + 12;
  let left = triggerRect.right - MENU_WIDTH;
  let top = triggerRect.bottom + MENU_GAP;

  if (top + estimatedHeight > window.innerHeight - VIEWPORT_PADDING) {
    top = triggerRect.top - MENU_GAP - estimatedHeight;
  }

  if (left < VIEWPORT_PADDING) {
    left = VIEWPORT_PADDING;
  }

  if (left + MENU_WIDTH > window.innerWidth - VIEWPORT_PADDING) {
    left = window.innerWidth - MENU_WIDTH - VIEWPORT_PADDING;
  }

  if (top < VIEWPORT_PADDING) {
    top = VIEWPORT_PADDING;
  }

  return { top, left };
}

export function AuditRowMenuPortal({
  open,
  onClose,
  triggerRef,
  itemCount,
  children,
}: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

  useLayoutEffect(() => {
    if (!open || !triggerRef.current) {
      setPosition(null);
      return;
    }

    const triggerRect = triggerRef.current.getBoundingClientRect();
    setPosition(resolveMenuPosition(triggerRect, itemCount));
  }, [open, itemCount, triggerRef]);

  useLayoutEffect(() => {
    if (!open || !triggerRef.current || !panelRef.current || !position) {
      return;
    }

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const panelHeight = panelRef.current.offsetHeight;
    let top = triggerRect.bottom + MENU_GAP;

    if (top + panelHeight > window.innerHeight - VIEWPORT_PADDING) {
      top = Math.max(
        VIEWPORT_PADDING,
        triggerRect.top - MENU_GAP - panelHeight,
      );
    }

    if (top === position.top) {
      return;
    }

    setPosition({ top, left: position.left });
  }, [open, itemCount, position, triggerRef]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      const target = event.target as Node | null;
      if (
        panelRef.current?.contains(target) ||
        triggerRef.current?.contains(target)
      ) {
        return;
      }
      onClose();
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, open, triggerRef]);

  if (!open || !position || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div
      ref={panelRef}
      className="dashboard-auditoria-5s a5s-app a5s-row-menu__panel a5s-row-menu__panel--portal"
      role="menu"
      style={{ top: position.top, left: position.left }}
    >
      {children}
    </div>,
    document.body,
  );
}
