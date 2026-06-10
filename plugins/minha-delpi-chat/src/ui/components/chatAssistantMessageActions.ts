import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  buildFormatSwitchActionsFromToolCalls,
  type FormatSwitchAction,
} from "./presentationInteractivityPolicy";

export type AssistantMessageMenuAction = FormatSwitchAction;

export function buildAssistantMessageMenuActions(
  toolCalls: ChatToolCall[],
): AssistantMessageMenuAction[] {
  const actions = buildFormatSwitchActionsFromToolCalls(toolCalls);
  const seen = new Set<string>();

  return actions.filter((action) => {
    if (seen.has(action.query)) {
      return false;
    }

    seen.add(action.query);
    return true;
  });
}
