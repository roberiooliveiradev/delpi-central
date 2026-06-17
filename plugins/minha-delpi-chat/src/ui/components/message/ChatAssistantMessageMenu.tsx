import type { ChatToolCall } from "../../../data/api/chatTypes";
import type { ActionMenuItem } from "../shared/menus/ActionMenuPanel";
import { DropdownMenuTrigger } from "../shared/menus/DropdownMenuTrigger";
import { buildAssistantMessageMenuActions } from "./chatAssistantMessageActions";

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
  const actions = buildAssistantMessageMenuActions(toolCalls);

  if (!actions.length || disabled) {
    return null;
  }

  const items: ActionMenuItem[] = actions.map((action) => ({
    id: action.id,
    label: action.label,
    onSelect: () => onSelect(action.query),
  }));

  return (
    <DropdownMenuTrigger
      items={items}
      menuLabel="Ações da resposta"
      ariaLabel="Mais ações da resposta"
      title="Mais ações"
      iconSize={15}
      wrapClassName="mdc-chat-message-action-wrap"
      triggerClassName="mdc-chat-message-action"
      scrim="transparent"
    />
  );
}
