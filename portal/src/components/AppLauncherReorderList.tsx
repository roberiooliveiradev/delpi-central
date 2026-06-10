import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { mergeFavoriteOrder, reorderList } from "../utils/favoriteOrder";
import type { FavoriteAppItem } from "../data/coreApi";

type DragState = {
  appId: string;
  pointerId: number;
  startX: number;
  startY: number;
  activated: boolean;
};

const PREVENT_LINK_DRAG_PX = 3;

function preventNativeLinkDrag(event: Event) {
  event.preventDefault();
}

export type AppLauncherReorderContextValue = {
  holdingId: string | null;
  draggingId: string | null;
  dropTargetId: string | null;
  onPointerDown: (
    appId: string,
  ) => (event: React.PointerEvent<HTMLElement>) => void;
  onPointerMove: (event: React.PointerEvent<HTMLElement>) => void;
  onPointerFinish: (event: React.PointerEvent<HTMLElement>) => void;
  onClickCapture: (event: React.MouseEvent<HTMLElement>) => void;
};

const AppLauncherReorderContext =
  createContext<AppLauncherReorderContextValue | null>(null);

const DRAG_THRESHOLD_PX = 8;
const HOLD_HINT_MS = 380;
const DRAGGING_BODY_CLASS = "app-launcher-reorder-dragging";
const HOLDING_BODY_CLASS = "app-launcher-reorder-holding";

function shouldStartReorderDrag(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;
  if (target.closest(".sidebar-inline-routes, .sidebar-inline-route")) {
    return false;
  }
  if (target.closest("button")) return false;
  return !!target.closest(".launcher-app-main");
}

export function useAppLauncherReorder() {
  return useContext(AppLauncherReorderContext);
}

type AppLauncherReorderListProps = {
  appIds: string[];
  favorites: FavoriteAppItem[];
  onReorder: (appIds: string[]) => Promise<void>;
  className?: string;
  ariaLabel?: string;
  children: ReactNode;
};

export function AppLauncherReorderList({
  appIds,
  favorites,
  onReorder,
  className,
  ariaLabel = "Apps favoritos",
  children,
}: AppLauncherReorderListProps) {
  const listRef = useRef<HTMLDivElement>(null);
  const dragStateRef = useRef<DragState | null>(null);
  const dragActivatedRef = useRef(false);
  const holdActivatedRef = useRef(false);
  const holdTimerRef = useRef<number | null>(null);
  const dropTargetRef = useRef<string | null>(null);
  const nativeDragBlockRef = useRef(false);

  const [holdingId, setHoldingId] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dropTargetId, setDropTargetId] = useState<string | null>(null);

  const commitReorder = useCallback(
    async (fromIndex: number, toIndex: number) => {
      if (fromIndex === toIndex || fromIndex < 0 || toIndex < 0) return;

      const newVisibleOrder = reorderList(appIds, fromIndex, toIndex);
      const allFavoriteIds = favorites.map((fav) => fav.id);
      const mergedOrder = mergeFavoriteOrder(
        allFavoriteIds,
        appIds,
        newVisibleOrder,
      );

      await onReorder(mergedOrder);
    },
    [appIds, favorites, onReorder],
  );

  const resolveDropTarget = useCallback((clientY: number, sourceId: string) => {
    const list = listRef.current;
    if (!list) return null;

    const items = Array.from(
      list.querySelectorAll<HTMLElement>(".app-launcher-reorder-item[data-app-id]"),
    );

    for (const item of items) {
      const id = item.dataset.appId;
      if (!id || id === sourceId) continue;

      const rect = item.getBoundingClientRect();
      if (clientY < rect.top + rect.height / 2) {
        return id;
      }
    }

    const lastItem = items[items.length - 1];
    return lastItem?.dataset.appId ?? null;
  }, []);

  const clearHoldTimer = useCallback(() => {
    if (holdTimerRef.current !== null) {
      window.clearTimeout(holdTimerRef.current);
      holdTimerRef.current = null;
    }
  }, []);

  const stopBlockingNativeDrag = useCallback(() => {
    if (!nativeDragBlockRef.current) return;
    document.removeEventListener("dragstart", preventNativeLinkDrag, true);
    document.removeEventListener("selectstart", preventNativeLinkDrag, true);
    nativeDragBlockRef.current = false;
  }, []);

  const startBlockingNativeDrag = useCallback(() => {
    if (nativeDragBlockRef.current) return;
    document.addEventListener("dragstart", preventNativeLinkDrag, true);
    document.addEventListener("selectstart", preventNativeLinkDrag, true);
    nativeDragBlockRef.current = true;
  }, []);

  const resetDrag = useCallback(() => {
    clearHoldTimer();
    stopBlockingNativeDrag();
    dragStateRef.current = null;
    dropTargetRef.current = null;
    holdActivatedRef.current = false;
    setHoldingId(null);
    setDraggingId(null);
    setDropTargetId(null);
    document.body.classList.remove(DRAGGING_BODY_CLASS, HOLDING_BODY_CLASS);
  }, [clearHoldTimer, stopBlockingNativeDrag]);

  const activateDrag = useCallback((appId: string) => {
    dragActivatedRef.current = true;
    setHoldingId(null);
    setDraggingId(appId);
    document.body.classList.remove(HOLDING_BODY_CLASS);
    document.body.classList.add(DRAGGING_BODY_CLASS);
  }, []);

  const onPointerDown = useCallback(
    (appId: string) => (event: React.PointerEvent<HTMLElement>) => {
      if (event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (!shouldStartReorderDrag(event.target)) return;

      dragActivatedRef.current = false;
      holdActivatedRef.current = false;
      dragStateRef.current = {
        appId,
        pointerId: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        activated: false,
      };

      clearHoldTimer();
      holdTimerRef.current = window.setTimeout(() => {
        const dragState = dragStateRef.current;
        if (!dragState || dragState.appId !== appId || dragState.activated) return;

        holdActivatedRef.current = true;
        setHoldingId(appId);
        startBlockingNativeDrag();
        document.body.classList.add(HOLDING_BODY_CLASS);
      }, HOLD_HINT_MS);

      event.currentTarget.setPointerCapture(event.pointerId);
    },
    [clearHoldTimer, startBlockingNativeDrag],
  );

  const onPointerMove = useCallback(
    (event: React.PointerEvent<HTMLElement>) => {
      const dragState = dragStateRef.current;
      if (!dragState || dragState.pointerId !== event.pointerId) return;

      const deltaX = Math.abs(event.clientX - dragState.startX);
      const deltaY = Math.abs(event.clientY - dragState.startY);
      const movedEnoughToBlockLink =
        deltaX >= PREVENT_LINK_DRAG_PX || deltaY >= PREVENT_LINK_DRAG_PX;

      if (movedEnoughToBlockLink || holdActivatedRef.current) {
        startBlockingNativeDrag();
        event.preventDefault();
      }

      if (!dragState.activated) {
        const movedEnoughToDrag = deltaY >= DRAG_THRESHOLD_PX;
        const holdReady = holdActivatedRef.current;

        if (!movedEnoughToDrag && !holdReady) {
          return;
        }

        dragState.activated = true;
        dragStateRef.current = dragState;
        activateDrag(dragState.appId);
      }

      event.preventDefault();
      const nextTarget = resolveDropTarget(event.clientY, dragState.appId);
      dropTargetRef.current = nextTarget;
      setDropTargetId(nextTarget);
    },
    [activateDrag, resolveDropTarget, startBlockingNativeDrag],
  );

  const onPointerFinish = useCallback(
    async (event: React.PointerEvent<HTMLElement>) => {
      const dragState = dragStateRef.current;
      if (!dragState || dragState.pointerId !== event.pointerId) return;

      if (event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }

      const targetId = dropTargetRef.current;
      const sourceId = dragState.appId;
      const wasActivated = dragState.activated;

      resetDrag();

      if (!wasActivated || !targetId || targetId === sourceId) return;

      const fromIndex = appIds.indexOf(sourceId);
      const toIndex = appIds.indexOf(targetId);
      await commitReorder(fromIndex, toIndex);
    },
    [appIds, commitReorder, resetDrag],
  );

  const onClickCapture = useCallback((event: React.MouseEvent<HTMLElement>) => {
    if (dragActivatedRef.current || holdActivatedRef.current) {
      event.preventDefault();
      event.stopPropagation();
      dragActivatedRef.current = false;
      holdActivatedRef.current = false;
    }
  }, []);

  const contextValue: AppLauncherReorderContextValue = {
    holdingId,
    draggingId,
    dropTargetId,
    onPointerDown,
    onPointerMove,
    onPointerFinish,
    onClickCapture,
  };

  useEffect(() => () => stopBlockingNativeDrag(), [stopBlockingNativeDrag]);

  if (appIds.length === 0) return null;

  return (
    <AppLauncherReorderContext.Provider value={contextValue}>
      <div
        ref={listRef}
        className={["app-launcher-reorder-list", className].filter(Boolean).join(" ")}
        aria-label={ariaLabel}
      >
        {children}
      </div>
    </AppLauncherReorderContext.Provider>
  );
}
