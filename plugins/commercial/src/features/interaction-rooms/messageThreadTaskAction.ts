/**
 * Slot de ação «criar tarefa» do MessageThread — host monta, kit só renderiza.
 */
import type { MessageThreadAction, MessageThreadItem } from "@delpi/plugin-ui/index";

import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

export const CREATE_TASK_MESSAGE_ACTION_ID = "create-task";

export function canCreateTaskFromMessage(
  message: Pick<MessageThreadItem, "kind" | "deleted">,
): boolean {
  if (message.deleted) return false;
  const kind = String(message.kind || "").trim();
  if (kind === "system" || kind === "task_ref" || kind === "pin") return false;
  return true;
}

export function buildCreateTaskMessageAction(options: {
  message: Pick<MessageThreadItem, "id" | "kind" | "deleted">;
  onCreateTask: (messageId: string) => void;
  busy?: boolean;
  label?: string;
}): MessageThreadAction | null {
  if (!canCreateTaskFromMessage(options.message)) return null;
  if (options.busy) return null;
  return {
    id: CREATE_TASK_MESSAGE_ACTION_ID,
    label: options.label ?? INTERACTION_ROOMS_CONTENT.createTaskActionLabel,
    onClick: () => options.onCreateTask(options.message.id),
  };
}

export function resolveInteractionMessageActions(options: {
  message: MessageThreadItem;
  onCreateTask: (messageId: string) => void;
  creatingMessageId?: string | null;
}): MessageThreadAction[] {
  const action = buildCreateTaskMessageAction({
    message: options.message,
    onCreateTask: options.onCreateTask,
    busy: options.creatingMessageId === options.message.id,
  });
  return action ? [action] : [];
}
