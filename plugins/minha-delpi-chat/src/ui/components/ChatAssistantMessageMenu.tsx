import { useEffect, useRef, useState } from "react";
import { MoreHorizontal } from "lucide-react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import {
  buildAssistantMessageMenuActions,
  type AssistantMessageMenuAction,
} from "./chatAssistantMessageActions";
import "./ChatTableRowMenu.css";

type ChatAssistantMessageMenuProps = {
  toolCalls: ChatToolCall[];
  onSelect: (query: string) => void;
  disabled?: boolean;
};

export function ChatAssistantMessageMenu({
  toolCalls,
  onSelect,
  disabled = false,
}: ChatAssistantMessageMenuProps) {
  const [open, setOpen] = useState(false);
  const [anchor, setAnchor] = useState<{ x: number; y: number } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const actions = buildAssistantMessageMenuActions(toolCalls);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      const target = event.target as Node | null;
      const panel = document.getElementById("mdc-assistant-message-menu-panel");

      if (
        panel &&
        target &&
        !panel.contains(target) &&
        buttonRef.current &&
        !buttonRef.current.contains(target)
      ) {
        setOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  if (!actions.length || disabled) {
    return null;
  }

  function openMenu() {
    const rect = buttonRef.current?.getBoundingClientRect();

    if (!rect) {
      return;
    }

    setAnchor({ x: rect.right - 8, y: rect.bottom + 4 });
    setOpen(true);
  }

  function handleSelect(action: AssistantMessageMenuAction) {
    onSelect(action.query);
    setOpen(false);
  }

  const left = anchor ? Math.min(anchor.x, window.innerWidth - 240) : 0;
  const top = anchor ? Math.min(anchor.y, window.innerHeight - 280) : 0;

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        className="mdc-chat-message-action"
        aria-label="Mais ações da resposta"
        title="Mais ações"
        onClick={openMenu}
      >
        <MoreHorizontal size={15} aria-hidden="true" />
      </button>

      {open && anchor ? (
        <div
          id="mdc-assistant-message-menu-panel"
          className="mdc-table-row-menu"
          style={{ left, top }}
          role="menu"
          aria-label="Ações da resposta"
        >
          {actions.map((action) => (
            <button
              key={action.id}
              type="button"
              className="mdc-table-row-menu__item"
              role="menuitem"
              onClick={() => handleSelect(action)}
            >
              {action.label}
            </button>
          ))}
        </div>
      ) : null}
    </>
  );
}
