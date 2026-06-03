import { type ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";

import {
  isOverlayPortalContained,
  resolveOverlayPortalContainer,
} from "./modalPortalTarget";
import "./chat-overlay-layer.css";
import "./modal-layer.css";

type ModalPortalProps = {
  children: ReactNode;
  lockScroll?: boolean;
};

export function ModalPortal({ children, lockScroll = true }: ModalPortalProps) {
  const container = resolveOverlayPortalContainer();
  const contained = isOverlayPortalContained(container);

  useEffect(() => {
    if (!lockScroll) {
      return;
    }

    const scrollTarget = contained ? container : document.body;
    const previousOverflow = scrollTarget.style.overflow;
    scrollTarget.style.overflow = "hidden";

    return () => {
      scrollTarget.style.overflow = previousOverflow;
    };
  }, [container, contained, lockScroll]);

  const theme =
    typeof document !== "undefined"
      ? document.documentElement.getAttribute("data-theme")
      : null;

  return createPortal(
    <div
      className={[
        "mdc-chat-overlay-portal",
        "minha-delpi-chat",
        contained ? "mdc-chat-overlay-portal--contained" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      data-theme={theme ?? undefined}
      role="presentation"
    >
      {children}
    </div>,
    container,
  );
}
