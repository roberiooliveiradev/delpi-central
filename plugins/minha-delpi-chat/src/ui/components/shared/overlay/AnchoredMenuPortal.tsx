import { createPortal } from "react-dom";
import { useEffect, useRef, type ReactNode, type RefObject } from "react";

import type { ContextMenuAnchor } from "./menuPositionUtils";
import {
  isOverlayPortalContained,
  resolveOverlayPortalContainer,
} from "./modalPortalTarget";
import {
  useAnchoredMenuLayout,
  type AnchoredMenuPlacement,
} from "./useAnchoredMenuLayout";

import "../../chat-overlay-layer.css";
import "./menu-popover.css";

type AnchoredMenuPortalBaseProps = {
  open: boolean;
  itemCount: number;
  menuLabel: string;
  menuRole?: "menu" | "listbox";
  menuWidth?: number;
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

  const { canUsePortal, panelStyle } = useAnchoredMenuLayout({
    open,
    triggerRef,
    anchor: menuAnchor,
    itemCount,
    placement,
    menuWidth,
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

      document.addEventListener("mousedown", handlePointerDown);
      removeListeners = () => {
        document.removeEventListener("mousedown", handlePointerDown);
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

      document.addEventListener("mousedown", handlePointerDown);
      removeListeners = () => {
        document.removeEventListener("mousedown", handlePointerDown);
      };
    }, 0);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
      removeListeners?.();
    };
  }, [onClose, open, panelRef, shell, triggerRef]);

  if (!open || !canUsePortal || !panelStyle || typeof document === "undefined") {
    return null;
  }

  const container = resolveOverlayPortalContainer();
  const portalContained = isOverlayPortalContained(container);

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
    return createPortal(panel, container);
  }

  const theme = document.documentElement.getAttribute("data-theme");

  const scrimClasses =
    scrim === "none"
      ? null
      : [
          scrim === "backdrop"
            ? "mdc-chat-overlay-scrim mdc-menu-popover__scrim mdc-menu-popover__scrim--backdrop"
            : "mdc-table-row-menu__scrim",
          scrimClassName,
        ]
          .filter(Boolean)
          .join(" ");

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
      {scrimClasses ? (
        <div
          className={scrimClasses}
          role="presentation"
          aria-hidden="true"
          onMouseDown={onClose}
        />
      ) : null}
      {panel}
    </div>,
    container,
  );
}
