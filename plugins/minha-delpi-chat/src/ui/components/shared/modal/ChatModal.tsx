import { useEffect, type MouseEvent, type ReactNode } from "react";

import { ModalPortal } from "../../ModalPortal";

import "../../chat-modal-surface.css";
import "./chat-modal.css";

export type ChatModalSize = "sm" | "md" | "lg" | "none";

export type ChatModalScrimLayout = "centered" | "drawer-end";

type ChatModalProps = {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  size?: ChatModalSize;
  scrimLayout?: ChatModalScrimLayout;
  role?: "dialog" | "alertdialog";
  ariaLabelledBy?: string;
  ariaDescribedBy?: string;
  panelClassName?: string;
  backdropClassName?: string;
  closeOnBackdrop?: boolean;
  lockScroll?: boolean;
  onPanelMouseDown?: (event: MouseEvent<HTMLElement>) => void;
};

export function ChatModal({
  open,
  onClose,
  children,
  size = "md",
  scrimLayout = "centered",
  role = "dialog",
  ariaLabelledBy,
  ariaDescribedBy,
  panelClassName = "",
  backdropClassName = "",
  closeOnBackdrop = true,
  lockScroll = true,
  onPanelMouseDown,
}: ChatModalProps) {
  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  const scrimLayoutClass =
    scrimLayout === "drawer-end"
      ? "mdc-chat-overlay-scrim--drawer-end"
      : "mdc-chat-overlay-scrim--centered";

  const sizeClass = size === "none" ? "" : `mdc-chat-modal--${size}`;

  return (
    <ModalPortal lockScroll={lockScroll}>
      <div
        className={[
          "mdc-chat-overlay-scrim",
          scrimLayoutClass,
          "mdc-chat-modal__backdrop",
          backdropClassName,
        ]
          .filter(Boolean)
          .join(" ")}
        role="presentation"
        onMouseDown={(event) => {
          if (closeOnBackdrop && event.target === event.currentTarget) {
            onClose();
          }
        }}
      >
        <section
          className={[
            "mdc-chat-overlay-panel",
            "mdc-chat-modal",
            sizeClass,
            panelClassName,
          ]
            .filter(Boolean)
            .join(" ")}
          role={role}
          aria-modal="true"
          aria-labelledby={ariaLabelledBy}
          aria-describedby={ariaDescribedBy}
          onMouseDown={onPanelMouseDown ?? ((event) => event.stopPropagation())}
        >
          {children}
        </section>
      </div>
    </ModalPortal>
  );
}
