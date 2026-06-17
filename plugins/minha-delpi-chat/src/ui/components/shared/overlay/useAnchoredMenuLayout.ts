import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useState,
  type CSSProperties,
  type RefObject,
} from "react";

import {
  isSidebarMenuTrigger,
  resolveAnchoredMenuPortalTarget,
} from "./modalPortalTarget";
import {
  menuAnchorRectFromElement,
  resolveActionMenuPosition,
  resolveComposerOptionMenuPosition,
  resolveComposerPanelMenuPosition,
  resolveContextMenuPosition,
  type ActionMenuHorizontalAlign,
  type ActionMenuLayout,
  type ComposerOptionMenuLayout,
  type ContextMenuAnchor,
  type ContextMenuLayout,
} from "./menuPositionUtils";
import type { AnchoredMenuPortalTarget } from "./modalPortalTarget";

export type AnchoredMenuPlacement =
  | "composer-option"
  | "composer-panel"
  | "action-menu"
  | "context-menu";

export type AnchoredMenuLayoutUnion =
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

type AnchoredMenuLayoutState = {
  layout: AnchoredMenuLayoutUnion;
  portalTarget: AnchoredMenuPortalTarget;
} | null;

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
  previous: AnchoredMenuLayoutUnion | null,
  next: AnchoredMenuLayoutUnion,
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

    if (previousMaxHeight !== nextMaxHeight) {
      return false;
    }
  }

  if ("anchorAbove" in previous || "anchorAbove" in next) {
    const previousAnchorAbove =
      "anchorAbove" in previous ? previous.anchorAbove : undefined;
    const nextAnchorAbove = "anchorAbove" in next ? next.anchorAbove : undefined;

    return previousAnchorAbove === nextAnchorAbove;
  }

  return true;
}

function portalTargetsEqual(
  previous: AnchoredMenuPortalTarget | null | undefined,
  next: AnchoredMenuPortalTarget,
): boolean {
  if (!previous) {
    return false;
  }

  return previous.container === next.container && previous.contained === next.contained;
}

function resolveContainedScope(trigger?: HTMLElement | null) {
  const portalTarget = resolveAnchoredMenuPortalTarget(trigger);
  const containerRect = portalTarget.contained
    ? menuAnchorRectFromElement(portalTarget.container)
    : undefined;

  return {
    portalTarget,
    containedLayout: {
      contained: portalTarget.contained,
      containerRect,
    },
  };
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
  const [layoutState, setLayoutState] = useState<AnchoredMenuLayoutState>(null);
  const [canUsePortal, setCanUsePortal] = useState(false);
  const anchorKey = anchorLayoutKey(anchor);

  const commitLayoutState = useCallback((next: AnchoredMenuLayoutState) => {
    setLayoutState((previous) => {
      if (!next) {
        return null;
      }

      if (
        previous &&
        layoutsEqual(previous.layout, next.layout) &&
        portalTargetsEqual(previous.portalTarget, next.portalTarget)
      ) {
        return previous;
      }

      return next;
    });
  }, []);

  const updateLayout = useCallback(() => {
    const trigger = triggerRef?.current;
    const { portalTarget, containedLayout } = resolveContainedScope(trigger ?? null);

    if (placement === "context-menu" && anchor) {
      if ("rect" in anchor) {
        commitLayoutState({
          layout: resolveActionMenuPosition({
            rect: anchor.rect,
            itemCount,
            menuWidth,
            ...containedLayout,
            horizontalAlign: "end",
            verticalAlign: "corner",
          }),
          portalTarget,
        });
        return;
      }

      commitLayoutState({
        layout: resolveContextMenuPosition({
          anchor,
          itemCount,
          menuWidth,
          contained: containedLayout.contained,
          containerRect: containedLayout.containerRect,
        }),
        portalTarget,
      });
      return;
    }

    if (!trigger) {
      return;
    }

    const triggerRect = menuAnchorRectFromElement(trigger);

    if (placement === "composer-option") {
      commitLayoutState({
        layout: resolveComposerOptionMenuPosition({
          rect: triggerRect,
          itemCount,
          menuWidth,
          ...containedLayout,
        }),
        portalTarget,
      });
      return;
    }

    if (placement === "composer-panel") {
      commitLayoutState({
        layout: resolveComposerPanelMenuPosition({
          rect: triggerRect,
          itemCount,
          menuWidth,
          ...containedLayout,
        }),
        portalTarget,
      });
      return;
    }

    if (placement === "context-menu") {
      return;
    }

    const isSidebarAction = isSidebarMenuTrigger(trigger);

    commitLayoutState({
      layout: resolveActionMenuPosition({
        rect: triggerRect,
        itemCount,
        menuWidth,
        ...containedLayout,
        horizontalAlign: isSidebarAction ? "start" : (menuHorizontalAlign ?? "end"),
        verticalAlign: isSidebarAction ? "beside" : "corner",
      }),
      portalTarget,
    });
  }, [
    anchorKey,
    commitLayoutState,
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
      setLayoutState(null);
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

  const layout = layoutState?.layout ?? null;
  const portalTarget = layoutState?.portalTarget ?? null;

  const anchorAbove = Boolean(layout && "anchorAbove" in layout && layout.anchorAbove);

  const panelStyle: CSSProperties | undefined = layout
    ? {
        top: layout.top,
        left: layout.left,
        ...(placement === "composer-option" || placement === "composer-panel"
          ? {
              ...("maxHeight" in layout ? { maxHeight: layout.maxHeight } : {}),
              height: "max-content",
              ...(anchorAbove ? { transform: "translateY(-100%)" } : {}),
            }
          : placement === "action-menu" || placement === "context-menu"
            ? {
                ...("maxHeight" in layout && layout.maxHeight != null
                  ? { maxHeight: layout.maxHeight, overflowY: "auto" as const }
                  : {}),
                ...(anchorAbove ? { transform: "translateY(-100%)" } : {}),
              }
            : {}),
      }
    : undefined;

  return {
    canUsePortal,
    layout,
    panelStyle,
    portalTarget,
    updateLayout,
  };
}
