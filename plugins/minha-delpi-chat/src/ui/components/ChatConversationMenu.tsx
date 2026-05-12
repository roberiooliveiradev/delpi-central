import {
  Archive,
  MoreHorizontal,
  Pencil,
  Pin,
  Share2,
  Trash2,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

import "./ChatConversationMenu.css";

type ChatConversationMenuProps = {
  open: boolean;
  disabled?: boolean;
  onOpenChange: (open: boolean) => void;
  onShare?: () => void;
  onRename: () => void;
  onPin?: () => void;
  onArchive?: () => void;
  onDelete: () => void;
};

type MenuPosition = {
  top: number;
  left: number;
};

const MENU_WIDTH = 240;
const MENU_MARGIN = 8;

export function ChatConversationMenu({
  open,
  disabled,
  onOpenChange,
  onShare,
  onRename,
  onPin,
  onArchive,
  onDelete,
}: ChatConversationMenuProps) {
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [position, setPosition] = useState<MenuPosition>({ top: 0, left: 0 });

  function updatePosition() {
    const trigger = triggerRef.current;

    if (!trigger) {
      return;
    }

    const rect = trigger.getBoundingClientRect();
    const left = Math.min(
      window.innerWidth - MENU_WIDTH - MENU_MARGIN,
      Math.max(MENU_MARGIN, rect.right - MENU_WIDTH),
    );

    const top = Math.min(
      window.innerHeight - MENU_MARGIN,
      rect.bottom + MENU_MARGIN,
    );

    setPosition({ top, left });
  }

  useEffect(() => {
    if (!open) {
      return;
    }

    updatePosition();

    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);

    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [open]);

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
        title="Opções"
      >
        <MoreHorizontal size={17} aria-hidden="true" />
      </button>

      {open ? (
        <>
          <button
            type="button"
            className="mdc-chat-conversation-menu__scrim"
            aria-label="Fechar opções"
            onClick={(event) => {
              event.stopPropagation();
              onOpenChange(false);
            }}
          />

          <div
            className="mdc-chat-conversation-menu__panel"
            role="menu"
            style={{
              top: position.top,
              left: position.left,
            }}
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
              <span>Fixar chat</span>
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
              <span>Arquivar</span>
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
      ) : null}
    </div>
  );
}
