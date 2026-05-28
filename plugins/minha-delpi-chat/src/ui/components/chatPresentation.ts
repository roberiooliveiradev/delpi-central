import type { ChatMessage, ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";

export type PresentationPair = {
  primary: ChatPresentation | null;
  table: ChatPresentation | null;
};

function getPresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const presentation = toolCall.metadata?.presentation;

    if (
      presentation &&
      typeof presentation === "object" &&
      "type" in presentation
    ) {
      return presentation as ChatPresentation;
    }
  }

  return null;
}

function getTablePresentationFromToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  if (!Array.isArray(toolCalls)) {
    return null;
  }

  for (const toolCall of toolCalls) {
    const tablePresentation = (toolCall.metadata as Record<string, unknown>)?.tablePresentation;

    if (
      tablePresentation &&
      typeof tablePresentation === "object" &&
      "type" in (tablePresentation as Record<string, unknown>)
    ) {
      return tablePresentation as ChatPresentation;
    }
  }

  return null;
}

export function getPresentationPairFromToolCalls(
  toolCalls?: ChatToolCall[],
): PresentationPair {
  return {
    primary: getPresentationFromToolCalls(toolCalls),
    table: getTablePresentationFromToolCalls(toolCalls),
  };
}

export function getPresentationFromMessages(
  messages: ChatMessage[],
): ChatPresentation | null {
  for (const message of [...messages].reverse()) {
    const toolCalls = message.metadata?.toolCalls;

    const presentation = getPresentationFromToolCalls(toolCalls);

    if (presentation) {
      return presentation;
    }
  }

  return null;
}

export function getPresentationFromStreamingToolCalls(
  toolCalls?: ChatToolCall[],
): ChatPresentation | null {
  return getPresentationFromToolCalls(toolCalls);
}

const RICH_PRESENTATION_TYPES = new Set(["table", "chart", "kpi"]);

export function hasRichPresentation(pair: PresentationPair): boolean {
  const primaryType = pair.primary?.type;

  if (primaryType && RICH_PRESENTATION_TYPES.has(primaryType)) {
    return true;
  }

  const tableType = pair.table?.type;

  return Boolean(tableType && RICH_PRESENTATION_TYPES.has(tableType));
}

/** Não renderiza markdown textual quando o painel rico já exibe os mesmos dados. */
export function shouldSuppressMarkdownForPresentation(
  content: string | null | undefined,
  pair: PresentationPair,
): boolean {
  if (!hasRichPresentation(pair)) {
    return false;
  }

  const trimmed = String(content || "").trim();

  if (!trimmed) {
    return false;
  }

  if (trimmed.includes("|") && trimmed.includes("-")) {
    return true;
  }

  if (pair.primary?.type === "kpi") {
    return trimmed.length > 80;
  }

  return trimmed.length > 100;
}
