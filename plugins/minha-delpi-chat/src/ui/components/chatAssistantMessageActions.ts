import type { ChatToolCall } from "../../data/api/chatTypes";

import type { FormatSwitchAction } from "./presentationInteractivityPolicy";

export type AssistantMessageMenuAction = FormatSwitchAction;

export function buildAssistantMessageMenuActions(
  _toolCalls: ChatToolCall[],
): AssistantMessageMenuAction[] {
  return [];
}
