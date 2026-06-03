import { type ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";

import "./modal-layer.css";

type ModalPortalProps = {
  children: ReactNode;
  lockScroll?: boolean;
};

export function ModalPortal({ children, lockScroll = true }: ModalPortalProps) {
  useEffect(() => {
    if (!lockScroll) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [lockScroll]);

  const theme =
    typeof document !== "undefined"
      ? document.documentElement.getAttribute("data-theme")
      : null;

  return createPortal(
    <div
      className="mdc-modal-portal minha-delpi-chat"
      data-theme={theme ?? undefined}
      role="presentation"
    >
      {children}
    </div>,
    document.body,
  );
}
