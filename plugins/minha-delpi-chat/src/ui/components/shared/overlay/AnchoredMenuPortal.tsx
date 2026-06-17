import { createPortal } from "react-dom";
import { useEffect, useRef, type ReactNode, type RefObject } from "react";

import type { ContextMenuAnchor } from "./menuPositionUtils";
import { isSidebarMenuTrigger } from "./modalPortalTarget";
import { OverlayScrim } from "./OverlayScrim";
import {
  useAnchoredMenuLayout,
  type AnchoredMenuPlacement,
} from "./useAnchoredMenuLayout";

import "../../../styles/chat-overlay-layer.css";
import "./menu-popover.css";

type AnchoredMenuPortalBaseProps = {
  open: boolean;
  itemCount: number;
  menuLabel: string;
  menuRole?: "menu" | "listbox";
  menuWidth?: number;
  menuHorizontalAlign?: "start" | "end";
  scrim?: "transparent" | "backdrop" | "none";
  scrimClassName?: string;
  shell?: "popover" | "overlay";
  panelClassName?: string;
  panelRef?: RefObject<HTMLDivElement | null>;
  onClose: () => void;
  children: ReactNode;
};

type AnchoredMenuPortalTriggerProps = AnchoredMenuPortalBaseProps & {
  triggerRef: RefObject<HTMLElement | null>;
  placement: Exclude<AnchoredMenuPlacement, "context-menu">;
  anchor?: never;
};

type AnchoredMenuPortalContextProps = AnchoredMenuPortalBaseProps & {
  anchor: ContextMenuAnchor;
  placement: "context-menu";
  triggerRef?: never;
};

export type AnchoredMenuPortalProps =
  | AnchoredMenuPortalTriggerProps
  | AnchoredMenuPortalContextProps;

export function AnchoredMenuPortal(props: AnchoredMenuPortalProps) {
  const {
    open,
    itemCount,
    placement,
    menuLabel,
    menuRole = "listbox",
    menuWidth,
    menuHorizontalAlign,
    scrim = "transparent",
    scrimClassName = "",
    shell = "popover",
    panelClassName = "",
    panelRef: panelRefProp,
    onClose,
    children,
  } = props;

  const internalPanelRef = useRef<HTMLDivElement | null>(null);
  const panelRef = panelRefProp ?? internalPanelRef;
  const triggerRef = "triggerRef" in props ? props.triggerRef : undefined;

  const menuAnchor = "anchor" in props ? props.anchor : undefined;

  const { canUsePortal, panelStyle, portalTarget } = useAnchoredMenuLayout({
    open,
    triggerRef,
    anchor: menuAnchor,
    itemCount,
    placement,
    menuWidth,
    menuHorizontalAlign,
    onClose,
  });

  useEffect(() => {
    if (!open || placement !== "context-menu") {
      return;
    }

    let cancelled = false;
    let removeListeners: (() => void) | undefined;

    const timeoutId = window.setTimeout(() => {
      if (cancelled) {
        return;
      }

      function handlePointerDown(event: MouseEvent) {
        const target = event.target as Node | null;
        const panel = panelRef.current;

        if (panel && target && !panel.contains(target)) {
          onClose();
        }
      }

      document.addEventListener("click", handlePointerDown, true);
      removeListeners = () => {
        document.removeEventListener("click", handlePointerDown, true);
      };
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
      removeListeners?.();
    };
  }, [onClose, open, panelRef, placement]);

  useEffect(() => {
    if (!open || shell !== "popover") {
      return;
    }

    let cancelled = false;
    let removeListeners: (() => void) | undefined;

    const timeoutId = window.setTimeout(() => {
      if (cancelled) {
        return;
      }

      function handlePointerDown(event: MouseEvent) {
        const target = event.target as Node | null;

        if (!target) {
          return;
        }

        if (panelRef.current?.contains(target)) {
          return;
        }

        if (triggerRef?.current?.contains(target)) {
          return;
        }

        onClose();
      }

      document.addEventListener("click", handlePointerDown, true);
      removeListeners = () => {
        document.removeEventListener("click", handlePointerDown, true);
      };
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
      removeListeners?.();
    };
  }, [onClose, open, panelRef, shell, triggerRef]);

  if (!open || !canUsePortal || !panelStyle || !portalTarget || typeof document === "undefined") {
    return null;
  }

  const container = portalTarget.container;
  const portalContained = portalTarget.contained;
  const isSidebarPortal = isSidebarMenuTrigger(triggerRef?.current);
  const showScrim = !isSidebarPortal && scrim !== "none";

  const popoverVariant =
    shell === "popover"
      ? placement === "composer-panel"
        ? "mdc-menu-popover--composer-panel"
        : placement === "composer-option"
          ? "mdc-menu-popover--composer"
          : "mdc-menu-popover--action"
      : "";

  const panelClasses =
    shell === "overlay"
      ? [
          "mdc-chat-overlay-panel",
          "mdc-chat-overlay-panel--anchored",
          panelClassName,
        ]
      : [
          "mdc-menu-popover",
          "mdc-menu-popover--portal",
          portalContained ? "mdc-menu-popover--contained" : "",
          popoverVariant,
          isSidebarPortal ? "mdc-menu-popover--sidebar-action" : "",
          panelClassName,
        ];

  const panel = (
    <div
      ref={panelRef}
      className={panelClasses.filter(Boolean).join(" ")}
      role={menuRole}
      aria-label={menuLabel}
      tabIndex={shell === "overlay" ? -1 : undefined}
      style={panelStyle}
      onMouseDown={(event) => event.stopPropagation()}
    >
      {children}
    </div>
  );

  if (shell === "popover") {
    return createPortal(
      <>
        {showScrim ? (
          <OverlayScrim className={scrimClassName} onMouseDown={onClose} />
        ) : null}
        {panel}
      </>,
      container,
    );
  }

  const theme = document.documentElement.getAttribute("data-theme");

  return createPortal(
    <div
      className={[
        "mdc-chat-overlay-portal",
        portalContained ? "mdc-chat-overlay-portal--contained" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-theme={theme ?? undefined}
      role="presentation"
    >
      {showScrim ? (
        <OverlayScrim className={scrimClassName} onMouseDown={onClose} />
      ) : null}
      {panel}
    </div>,
    container,
  );
}
