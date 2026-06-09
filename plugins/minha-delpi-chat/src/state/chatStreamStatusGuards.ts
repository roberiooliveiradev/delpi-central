import type { ChatSource, ChatToolCall } from "../data/api/chatTypes";

/** Evita status enganoso de RAG quando o turno não trouxe fontes. */
export function shouldPatchStreamStatusForSources(sources: ChatSource[]): boolean {
  return sources.length > 0;
}

/** Evita status enganoso de tools quando nenhuma ferramenta rodou. */
export function shouldPatchStreamStatusForToolCalls(toolCalls: ChatToolCall[]): boolean {
  return toolCalls.length > 0;
}
