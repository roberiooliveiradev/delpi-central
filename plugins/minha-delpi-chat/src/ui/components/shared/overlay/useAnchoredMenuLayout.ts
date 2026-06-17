import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useState,
  type CSSProperties,
  type RefObject,
} from "react";

import {
  isOverlayPortalContained,
  resolveOverlayPortalContainer,
} from "./modalPortalTarget";
import {
  isMenuAnchorOutsideContainer,
  menuAnchorRectFromElement,
  resolveActionMenuPosition,
  resolveComposerOptionMenuPosition,
  resolveComposerPanelMenuPosition,
  resolveContextMenuPosition,
  toContainerRelativeRect,
  type ActionMenuHorizontalAlign,
  type ActionMenuLayout,
  type ComposerOptionMenuLayout,
  type ContextMenuAnchor,
  type ContextMenuLayout,
} from "./menuPositionUtils";

export type AnchoredMenuPlacement =
  | "composer-option"
  | "composer-panel"
  | "action-menu"
  | "context-menu";

export type AnchoredMenuLayout =
  | ComposerOptionMenuLayout
  | ActionMenuLayout
  | ContextMenuLayout;

/** @deprecated Prefer triggerRef / anchor explícitos no hook. */
export type MenuPortalSource =
  | { kind: "trigger"; triggerRef: RefObject<HTMLElement | null> }
  | { kind: "anchor"; anchor: ContextMenuAnchor };

type UseAnchoredMenuLayoutOptions = {
  open: boolean;
  triggerRef?: RefObject<HTMLElement | null>;
  anchor?: ContextMenuAnchor;
  itemCount: number;
  placement: AnchoredMenuPlacement;
  menuWidth?: number;
  menuHorizontalAlign?: ActionMenuHorizontalAlign;
  onClose: () => void;
};

function anchorLayoutKey(anchor?: ContextMenuAnchor): string {
  if (!anchor) {
    return "";
  }

  if ("point" in anchor) {
    return `p:${anchor.point.x},${anchor.point.y}`;
  }

  const { left, top, right, bottom } = anchor.rect;

  return `r:${left},${top},${right},${bottom}`;
}

function layoutsEqual(
  previous: AnchoredMenuLayout | null,
  next: AnchoredMenuLayout,
): boolean {
  if (!previous) {
    return false;
  }

  if (previous.left !== next.left || previous.top !== next.top) {
    return false;
  }

  if ("maxHeight" in previous || "maxHeight" in next) {
    const previousMaxHeight =
      "maxHeight" in previous ? previous.maxHeight : undefined;
    const nextMaxHeight = "maxHeight" in next ? next.maxHeight : undefined;

    return previousMaxHeight === nextMaxHeight;
  }

  return true;
}

export function useAnchoredMenuLayout({
  open,
  triggerRef,
  anchor,
  itemCount,
  placement,
  menuWidth,
  menuHorizontalAlign,
  onClose,
}: UseAnchoredMenuLayoutOptions) {
  const [layout, setLayout] = useState<AnchoredMenuLayout | null>(null);
  const [canUsePortal, setCanUsePortal] = useState(false);
  const [useViewportPositioning, setUseViewportPositioning] = useState(false);
  const anchorKey = anchorLayoutKey(anchor);

  const commitLayout = useCallback((next: AnchoredMenuLayout) => {
    setLayout((previous) => (layoutsEqual(previous, next) ? previous : next));
  }, []);

  const updateLayout = useCallback(() => {
    const container = resolveOverlayPortalContainer();
    const portalContained = isOverlayPortalContained(container);
    const containerRect = portalContained
      ? menuAnchorRectFromElement(container)
      : undefined;
    const containedLayout = {
      contained: portalContained,
      containerRect,
    };

    if (placement === "context-menu" && anchor) {
      commitLayout(
        resolveContextMenuPosition({
          anchor,
          itemCount,
          menuWidth,
          contained: portalContained,
          containerRect,
        }),
      );
      return;
    }

    const trigger = triggerRef?.current;

    if (!trigger) {
      return;
    }

    const triggerRect = menuAnchorRectFromElement(trigger);
    const anchorOutsideContainer =
      portalContained &&
      containerRect != null &&
      isMenuAnchorOutsideContainer(triggerRect, containerRect);
    const useViewportCoords = anchorOutsideContainer;
    const rect = useViewportCoords
      ? triggerRect
      : portalContained && containerRect
        ? toContainerRelativeRect(triggerRect, containerRect)
        : triggerRect;
    const actionMenuContained = portalContained && !useViewportCoords;

    setUseViewportPositioning(useViewportCoords);

    if (placement === "composer-option") {
      commitLayout(
        resolveComposerOptionMenuPosition({
          rect,
          itemCount,
          menuWidth,
          ...containedLayout,
        }),
      );
      return;
    }

    if (placement === "composer-panel") {
      commitLayout(
        resolveComposerPanelMenuPosition({
          rect,
          itemCount,
          menuWidth,
          ...containedLayout,
        }),
      );
      return;
    }

    if (placement === "context-menu") {
      return;
    }

    commitLayout(
      resolveActionMenuPosition({
        rect,
        itemCount,
        menuWidth,
        contained: actionMenuContained,
        containerRect: actionMenuContained ? containerRect : undefined,
        horizontalAlign: menuHorizontalAlign,
      }),
    );
  }, [
    anchorKey,
    commitLayout,
    itemCount,
    menuHorizontalAlign,
    menuWidth,
    placement,
    triggerRef,
  ]);

  useEffect(() => {
    setCanUsePortal(true);
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      setLayout(null);
      setUseViewportPositioning(false);
      return;
    }

    updateLayout();

    window.addEventListener("resize", updateLayout);
    window.addEventListener("scroll", updateLayout, true);

    return () => {
      window.removeEventListener("resize", updateLayout);
      window.removeEventListener("scroll", updateLayout, true);
    };
  }, [open, updateLayout]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, open]);

  const panelStyle: CSSProperties | undefined = layout
    ? {
        top: layout.top,
        left: layout.left,
        ...(placement === "composer-option" || placement === "composer-panel"
          ? {
              ...("maxHeight" in layout ? { maxHeight: layout.maxHeight } : {}),
              height: "max-content",
              ...("anchorAbove" in layout && layout.anchorAbove
                ? { transform: "translateY(-100%)" }
                : {}),
            }
          : {}),
      }
    : undefined;

  return {
    canUsePortal,
    layout,
    panelStyle,
    updateLayout,
    useViewportPositioning,
  };
}
