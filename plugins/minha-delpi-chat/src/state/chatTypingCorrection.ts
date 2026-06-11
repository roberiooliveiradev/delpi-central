import { getTypingSuggestions } from "../data/api/chatApi";

import type { ChatTypingCorrectionMetadata, ChatTypingSuggestion } from "../data/api/chatTypes";

const dismissedBySession = new Map<string, Set<string>>();

export function isTypingSuggestionDismissed(sessionId: string | null | undefined, original: string): boolean {
  if (!sessionId || !original.trim()) {
    return false;
  }

  return dismissedBySession.get(sessionId)?.has(original) ?? false;
}

export function dismissTypingSuggestion(sessionId: string | null | undefined, original: string): void {
  if (!sessionId || !original.trim()) {
    return;
  }

  const bucket = dismissedBySession.get(sessionId) ?? new Set<string>();
  bucket.add(original);
  dismissedBySession.set(sessionId, bucket);
}

export function buildTypingCorrectionMetadata(
  suggestion: ChatTypingSuggestion,
  accepted: boolean,
): ChatTypingCorrectionMetadata {
  return {
    original: suggestion.original,
    corrected: suggestion.corrected,
    accepted,
    source: "domain_dictionary",
    changes: suggestion.changes.map((change) => ({
      from: change.from,
      to: change.to,
      kind: change.kind,
    })),
  };
}

export async function fetchTypingSuggestion(
  text: string,
  options: {
    enabled: boolean;
    sessionId?: string | null;
    getAccessToken?: () => string | undefined | Promise<string | undefined>;
  },
): Promise<ChatTypingSuggestion | null> {
  const trimmed = text.trim();

  if (!options.enabled || trimmed.length < 4) {
    return null;
  }

  if (isTypingSuggestionDismissed(options.sessionId, trimmed)) {
    return null;
  }

  const response = await getTypingSuggestions(trimmed, {
    getAccessToken: options.getAccessToken,
  });

  const corrected = String(response.corrected ?? "").trim();

  if (!response.hasSuggestions || !corrected || corrected === trimmed) {
    return null;
  }

  return {
    original: response.original,
    corrected: response.corrected,
    changes: response.changes,
  };
}

export function shouldClearTypingSuggestion(previousDraft: string, nextDraft: string): boolean {
  return previousDraft.trim() !== nextDraft.trim();
}
