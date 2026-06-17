import type { ChatDataCoverageNotice, ChatToolCall } from "../../../data/api/chatTypes";

import {
  getDataAnswerFromToolCalls,
  getDataCoverageNoticeFromToolCall,
  getDataCoverageNoticeFromToolCalls,
} from "../chatPresentation";

function limitationLines(toolCalls?: ChatToolCall[]): string[] {
  const dataAnswer = getDataAnswerFromToolCalls(toolCalls);
  const storyLimitations = new Set<string>();

  for (const toolCall of toolCalls ?? []) {
    const story = (toolCall.metadata as Record<string, unknown> | undefined)?.storyPresentation;

    if (!story || typeof story !== "object") {
      continue;
    }

    const blocks = (story as { blocks?: unknown }).blocks;

    if (!Array.isArray(blocks)) {
      continue;
    }

    for (const block of blocks) {
      if (
        block &&
        typeof block === "object" &&
        (block as { kind?: string }).kind === "limitation"
      ) {
        const text = String((block as { text?: string }).text ?? "").trim();

        if (text) {
          storyLimitations.add(text);
        }
      }
    }
  }

  const fromAnswer = (dataAnswer?.limitations ?? [])
    .map((line) => String(line ?? "").trim())
    .filter(Boolean);

  return [...new Set([...fromAnswer, ...storyLimitations])];
}

export function resolveHumanizedCoverageNotice(
  toolCalls?: ChatToolCall[],
): ChatDataCoverageNotice | null {
  const base = getDataCoverageNoticeFromToolCalls(toolCalls);
  const limitations = limitationLines(toolCalls);

  if (!limitations.length) {
    return base;
  }

  if (!base) {
    return {
      kind: "partial",
      message: limitations.join(" "),
      messages: limitations,
    };
  }

  const mergedMessages = [
    String(base.message ?? "").trim(),
    ...(base.messages ?? []).map((line) => String(line).trim()).filter(Boolean),
  ].filter(Boolean);

  for (const line of limitations) {
    if (!mergedMessages.includes(line)) {
      mergedMessages.push(line);
    }
  }

  const messageParts = [String(base.message ?? "").trim(), ...limitations].filter(Boolean);
  const uniqueParts = [...new Set(messageParts)];

  return {
    ...base,
    message: uniqueParts.join(" "),
    messages: mergedMessages.length ? mergedMessages : uniqueParts,
  };
}

export function resolveHumanizedCoverageNoticeFromToolCall(
  toolCall?: ChatToolCall,
): ChatDataCoverageNotice | null {
  if (!toolCall) {
    return null;
  }

  return resolveHumanizedCoverageNotice([toolCall]) ?? getDataCoverageNoticeFromToolCall(toolCall);
}
