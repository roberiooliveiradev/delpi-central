import {
  Archive,
  MoreHorizontal,
  Pencil,
  Pin,
  Share2,
  Trash2,
} from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import "./ChatConversationMenu.css";

type ChatConversationMenuProps = {
  open: boolean;
  disabled?: boolean;
  onOpenChange: (open: boolean) => void;
  onShare?: () => void;
  onRename: () => void;
  pinLabel?: string;
  archiveLabel?: string;
  onPin?: () => void;
  onArchive?: () => void;
  onDelete: () => void;
};

type MenuPosition = {
  top: number;
  left: number;
};

const MENU_WIDTH = 240;
const MENU_HEIGHT = 286;
const MENU_MARGIN = 8;

export function ChatConversationMenu({
  open,
  disabled,
  onOpenChange,
  onShare,
  onRename,
  pinLabel = "Fixar chat",
  archiveLabel = "Arquivar",
  onPin,
  onArchive,
  onDelete,
}: ChatConversationMenuProps) {
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [position, setPosition] = useState<MenuPosition>({ top: 0, left: 0 });
  const [canUsePortal, setCanUsePortal] = useState(false);

  function updatePosition() {
    const trigger = triggerRef.current;

    if (!trigger) {
      return;
    }

    const rect = trigger.getBoundingClientRect();

    const preferredLeft = rect.right + MENU_MARGIN;
    const fallbackLeft = rect.left - MENU_WIDTH - MENU_MARGIN;

    const left =
      preferredLeft + MENU_WIDTH <= window.innerWidth - MENU_MARGIN
        ? preferredLeft
        : Math.max(MENU_MARGIN, fallbackLeft);

    const preferredTop = rect.top;
    const maxTop = window.innerHeight - MENU_HEIGHT - MENU_MARGIN;
    const top = Math.max(MENU_MARGIN, Math.min(preferredTop, maxTop));

    setPosition({ top, left });
  }

  useEffect(() => {
    setCanUsePortal(true);
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      return;
    }

    updatePosition();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    }

    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onOpenChange]);

  const menu = open ? (
    <>
      <div
        className="mdc-chat-conversation-menu__scrim"
        role="presentation"
        onMouseDown={() => onOpenChange(false)}
      />

      <div
        className="mdc-chat-conversation-menu__panel"
        role="menu"
        style={{
          top: position.top,
          left: position.left,
        }}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          role="menuitem"
          onClick={(event) => {
            event.stopPropagation();
            onOpenChange(false);
            onShare?.();
          }}
        >
          <Share2 size={18} aria-hidden="true" />
          <span>Compartilhar</span>
        </button>

        <button
          type="button"
          role="menuitem"
          onClick={(event) => {
            event.stopPropagation();
            onOpenChange(false);
            onRename();
          }}
        >
          <Pencil size={18} aria-hidden="true" />
          <span>Renomear</span>
        </button>

        <hr />

        <button
          type="button"
          role="menuitem"
          className={!onPin ? "mdc-chat-conversation-menu__disabled" : undefined}
          onClick={(event) => {
            event.stopPropagation();

            if (!onPin) {
              return;
            }

            onOpenChange(false);
            onPin();
          }}
        >
          <Pin size={18} aria-hidden="true" />
          <span>{pinLabel}</span>
        </button>

        <button
          type="button"
          role="menuitem"
          className={!onArchive ? "mdc-chat-conversation-menu__disabled" : undefined}
          onClick={(event) => {
            event.stopPropagation();

            if (!onArchive) {
              return;
            }

            onOpenChange(false);
            onArchive();
          }}
        >
          <Archive size={18} aria-hidden="true" />
          <span>{archiveLabel}</span>
        </button>

        <button
          type="button"
          role="menuitem"
          className="mdc-chat-conversation-menu__danger"
          onClick={(event) => {
            event.stopPropagation();
            onOpenChange(false);
            onDelete();
          }}
        >
          <Trash2 size={18} aria-hidden="true" />
          <span>Excluir</span>
        </button>
      </div>
    </>
  ) : null;

  return (
    <div className="mdc-chat-conversation-menu">
      <button
        ref={triggerRef}
        type="button"
        className="mdc-chat-conversation-menu__trigger"
        disabled={disabled}
        onClick={(event) => {
          event.stopPropagation();
          updatePosition();
          onOpenChange(!open);
        }}
        aria-label="Abrir opções da conversa"
        aria-expanded={open}
        title="Opções"
      >
        <MoreHorizontal size={17} aria-hidden="true" />
      </button>

      {canUsePortal && menu ? createPortal(menu, document.body) : null}
    </div>
  );
}
