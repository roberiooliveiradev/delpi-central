import type { ChatSource } from "../../data/api/chatTypes";

export function isGeneralChatSource(source: ChatSource): boolean {
  const scope = String(source.scope ?? "").trim().toLowerCase();

  if (scope === "global") {
    return true;
  }

  const sourceType = String(source.sourceType ?? "").trim().toLowerCase();

  return sourceType === "global";
}

export function filterVisibleChatSources(sources?: ChatSource[]): ChatSource[] {
  if (!sources?.length) {
    return [];
  }

  return sources.filter((source) => !isGeneralChatSource(source));
}
