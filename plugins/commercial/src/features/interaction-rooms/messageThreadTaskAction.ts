/**
 * Slots de ação do MessageThread (tarefa + pin) — host monta, kit só renderiza.
 */
import { createElement } from "react";
import { ListTodo, Pin, PinOff } from "lucide-react";
import type { MessageThreadAction, MessageThreadItem } from "@delpi/plugin-ui/index";

import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

const ACTION_ICON_SIZE = 16;

export const CREATE_TASK_MESSAGE_ACTION_ID = "create-task";
export const PIN_MESSAGE_ACTION_ID = "pin-message";
export const UNPIN_MESSAGE_ACTION_ID = "unpin-message";

export function canCreateTaskFromMessage(
  message: Pick<MessageThreadItem, "kind" | "deleted">,
): boolean {
  if (message.deleted) return false;
  const kind = String(message.kind || "").trim();
  if (kind === "system" || kind === "task_ref" || kind === "pin") return false;
  return true;
}

export function canPinMessage(
  message: Pick<MessageThreadItem, "kind" | "deleted">,
): boolean {
  if (message.deleted) return false;
  const kind = String(message.kind || "").trim();
  if (kind === "system") return false;
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
  const label = options.label ?? INTERACTION_ROOMS_CONTENT.createTaskActionLabel;
  return {
    id: CREATE_TASK_MESSAGE_ACTION_ID,
    label,
    title: label,
    icon: createElement(ListTodo, { size: ACTION_ICON_SIZE, "aria-hidden": true }),
    onClick: () => options.onCreateTask(options.message.id),
  };
}

export function buildPinMessageAction(options: {
  message: Pick<MessageThreadItem, "id" | "kind" | "deleted">;
  pinned: boolean;
  onTogglePin: (messageId: string, nextPinned: boolean) => void;
  busy?: boolean;
}): MessageThreadAction | null {
  if (!canPinMessage(options.message)) return null;
  if (options.busy) return null;
  if (options.pinned) {
    const label = INTERACTION_ROOMS_CONTENT.unpinActionLabel;
    return {
      id: UNPIN_MESSAGE_ACTION_ID,
      label,
      title: label,
      icon: createElement(PinOff, { size: ACTION_ICON_SIZE, "aria-hidden": true }),
      onClick: () => options.onTogglePin(options.message.id, false),
    };
  }
  const label = INTERACTION_ROOMS_CONTENT.pinActionLabel;
  return {
    id: PIN_MESSAGE_ACTION_ID,
    label,
    title: label,
    icon: createElement(Pin, { size: ACTION_ICON_SIZE, "aria-hidden": true }),
    onClick: () => options.onTogglePin(options.message.id, true),
  };
}

export function resolveInteractionMessageActions(options: {
  message: MessageThreadItem;
  onCreateTask: (messageId: string) => void;
  creatingMessageId?: string | null;
  pinnedMessageIds?: ReadonlySet<string>;
  onTogglePin?: (messageId: string, nextPinned: boolean) => void;
  pinningMessageId?: string | null;
}): MessageThreadAction[] {
  const actions: MessageThreadAction[] = [];
  const createTask = buildCreateTaskMessageAction({
    message: options.message,
    onCreateTask: options.onCreateTask,
    busy: options.creatingMessageId === options.message.id,
  });
  if (createTask) actions.push(createTask);

  if (options.onTogglePin) {
    const pin = buildPinMessageAction({
      message: options.message,
      pinned: Boolean(options.pinnedMessageIds?.has(options.message.id)),
      onTogglePin: options.onTogglePin,
      busy: options.pinningMessageId === options.message.id,
    });
    if (pin) actions.push(pin);
  }
  return actions;
}
