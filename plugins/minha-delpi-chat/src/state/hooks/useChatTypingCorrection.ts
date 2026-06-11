import { useEffect, useRef, useState } from "react";

import {
  dismissTypingSuggestion,
  fetchTypingSuggestion,
  shouldClearTypingSuggestion,
} from "../chatTypingCorrection";
import { recordTypingCorrectionTelemetry } from "../../ui/typingCorrectionTelemetry";

import type { ChatTypingSuggestion } from "../../data/api/chatTypes";

const TYPING_SUGGESTION_DEBOUNCE_MS = 500;

type UseChatTypingCorrectionOptions = {
  draft: string;
  sessionId?: string | null;
  enabled?: boolean;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function useChatTypingCorrection({
  draft,
  sessionId,
  enabled = false,
  getAccessToken,
}: UseChatTypingCorrectionOptions) {
  const [suggestion, setSuggestion] = useState<ChatTypingSuggestion | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const previousDraftRef = useRef(draft);
  const requestIdRef = useRef(0);
  const lastOfferedOriginalRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setSuggestion(null);
      setIsLoading(false);
      return;
    }

    if (shouldClearTypingSuggestion(previousDraftRef.current, draft)) {
      setSuggestion(null);
      lastOfferedOriginalRef.current = null;
    }

    previousDraftRef.current = draft;

    const trimmed = draft.trim();

    if (trimmed.length < 4) {
      setSuggestion(null);
      setIsLoading(false);
      return;
    }

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setIsLoading(true);

    const timer = window.setTimeout(() => {
      void fetchTypingSuggestion(trimmed, {
        enabled,
        sessionId,
        getAccessToken,
      })
        .then((nextSuggestion) => {
          if (requestIdRef.current !== requestId) {
            return;
          }

          setSuggestion(nextSuggestion);

          if (
            nextSuggestion &&
            lastOfferedOriginalRef.current !== nextSuggestion.original
          ) {
            lastOfferedOriginalRef.current = nextSuggestion.original;
            recordTypingCorrectionTelemetry("typing_correction_offered", {
              original: nextSuggestion.original,
              corrected: nextSuggestion.corrected,
              changeCount: nextSuggestion.changes.length,
            });
          }
        })
        .catch(() => {
          if (requestIdRef.current === requestId) {
            setSuggestion(null);
          }
        })
        .finally(() => {
          if (requestIdRef.current === requestId) {
            setIsLoading(false);
          }
        });
    }, TYPING_SUGGESTION_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
    };
  }, [draft, enabled, getAccessToken, sessionId]);

  const dismissSuggestion = () => {
    if (!suggestion) {
      return;
    }

    recordTypingCorrectionTelemetry("typing_correction_dismissed", {
      original: suggestion.original,
      corrected: suggestion.corrected,
    });
    dismissTypingSuggestion(sessionId, suggestion.original);
    setSuggestion(null);
    lastOfferedOriginalRef.current = null;
  };

  const clearSuggestion = () => {
    setSuggestion(null);
  };

  return {
    suggestion,
    isLoading,
    dismissSuggestion,
    clearSuggestion,
  };
}
