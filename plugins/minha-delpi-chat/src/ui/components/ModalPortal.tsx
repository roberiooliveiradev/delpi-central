import { type ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";

import { resolveModalPortalContainer } from "./modalPortalTarget";
import "./modal-layer.css";

type ModalPortalProps = {
  children: ReactNode;
  lockScroll?: boolean;
};

export function ModalPortal({ children, lockScroll = true }: ModalPortalProps) {
  const container = resolveModalPortalContainer();

  useEffect(() => {
    if (!lockScroll) {
      return;
    }

    const scrollTarget =
      container === document.body ? document.body : container;

    const previousOverflow = scrollTarget.style.overflow;
    scrollTarget.style.overflow = "hidden";

    return () => {
      scrollTarget.style.overflow = previousOverflow;
    };
  }, [container, lockScroll]);

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
    container,
  );
}
