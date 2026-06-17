import type { ChatMessage } from "../data/api/chatTypes";

export const AGENT_BUILDER_PREVIEW_SESSION_ID = "agent-builder-preview";

export type PreviewTurn = {
  role: "user" | "assistant";
  content: string;
};

export function createAgentPreviewChatMessage(
  role: PreviewTurn["role"],
  content: string,
): ChatMessage {
  return {
    id: `preview-${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    session_id: AGENT_BUILDER_PREVIEW_SESSION_ID,
    role,
    content,
    metadata: null,
    created_at: new Date().toISOString(),
  };
}

export function toPreviewPreviousMessages(messages: ChatMessage[]): PreviewTurn[] {
  return messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({
      role: message.role as PreviewTurn["role"],
      content: message.content,
    }));
}
