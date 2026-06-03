import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import {
  buildAssistantMessageMenuActions,
  type AssistantMessageMenuAction,
} from "./chatAssistantMessageActions";
import { ChatTableRowMenu } from "./ChatTableRowMenu";
import { menuAnchorRectFromElement } from "./menuPositionUtils";
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
  const [menu, setMenu] = useState<{
    anchor: { rect: ReturnType<typeof menuAnchorRectFromElement> };
    actions: ReturnType<typeof buildAssistantMessageMenuActions>;
  } | null>(null);
  const actions = buildAssistantMessageMenuActions(toolCalls);

  if (!actions.length || disabled) {
    return null;
  }

  function openMenu(element: HTMLButtonElement) {
    setMenu({
      anchor: { rect: menuAnchorRectFromElement(element) },
      actions,
    });
  }

  function handleSelect(action: AssistantMessageMenuAction) {
    onSelect(action.query);
    setMenu(null);
  }

  return (
    <>
      <button
        type="button"
        className="mdc-chat-message-action"
        aria-label="Mais ações da resposta"
        title="Mais ações"
        onClick={(event) => openMenu(event.currentTarget)}
      >
        <MoreHorizontal size={15} aria-hidden="true" />
      </button>

      {menu ? (
        <ChatTableRowMenu
          actions={menu.actions.map((action) => ({
            id: action.id,
            label: action.label,
            query: action.query,
          }))}
          anchor={menu.anchor}
          scrim="light"
          variant="actions"
          menuLabel="Ações da resposta"
          onSelect={(query) => {
            const action = menu.actions.find((item) => item.query === query);

            if (action) {
              handleSelect(action);
            }
          }}
          onClose={() => setMenu(null)}
        />
      ) : null}
    </>
  );
}
