import { createPortal } from "react-dom";
import type { ReactNode, RefObject } from "react";

import { useComposerMentionMenuLayout } from "../../hooks/useComposerMentionMenuLayout";

import "../../styles/chat-overlay-layer.css";
import "./ChatComposerMentionMenu.css";

type ComposerMentionMenuPortalProps = {
  open: boolean;
  textareaRef: RefObject<HTMLTextAreaElement | null>;
  anchorIndex: number;
  itemCount: number;
  value: string;
  children: ReactNode;
};

export function ComposerMentionMenuPortal({
  open,
  textareaRef,
  anchorIndex,
  itemCount,
  value,
  children,
}: ComposerMentionMenuPortalProps) {
  const { canUsePortal, layoutState, panelStyle } = useComposerMentionMenuLayout({
    open,
    textareaRef,
    anchorIndex,
    itemCount,
    value,
  });

  if (
    !open ||
    !canUsePortal ||
    !panelStyle ||
    !layoutState ||
    typeof document === "undefined"
  ) {
    return null;
  }

  const contained = layoutState.portalTarget.contained;

  return createPortal(
    <div
      className={[
        "mdc-chat-composer-mention-menu",
        "mdc-chat-composer-mention-menu--portal",
        contained ? "mdc-chat-composer-mention-menu--contained" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      style={panelStyle}
      role="presentation"
      onMouseDown={(event) => event.stopPropagation()}
    >
      {children}
    </div>,
    layoutState.portalTarget.container,
  );
}
