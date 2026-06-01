import { useEffect, useState } from "react";

import { getChatFeedbackReasons } from "../../data/api/chatApi";
import type { ChatFeedbackReasonsPayload } from "../../data/api/chatTypes";
import {
  CHAT_FEEDBACK_PRIMARY_REASON_IDS,
  CHAT_FEEDBACK_REASONS,
} from "../../ui/chatFeedbackReasons";

type UseChatFeedbackReasonsOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

const FALLBACK: ChatFeedbackReasonsPayload = {
  reasons: CHAT_FEEDBACK_REASONS,
  primaryReasonIds: CHAT_FEEDBACK_PRIMARY_REASON_IDS,
};

export function useChatFeedbackReasons(options: UseChatFeedbackReasonsOptions = {}) {
  const [payload, setPayload] = useState<ChatFeedbackReasonsPayload>(FALLBACK);
  const [isLoading, setIsLoading] = useState(Boolean(options.getAccessToken));

  useEffect(() => {
    if (!options.getAccessToken) {
      setPayload(FALLBACK);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    void getChatFeedbackReasons({ getAccessToken: options.getAccessToken })
      .then((response) => {
        if (cancelled) {
          return;
        }

        if (response.reasons?.length) {
          setPayload(response);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPayload(FALLBACK);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [options.getAccessToken]);

  return {
    reasons: payload.reasons,
    primaryReasonIds: payload.primaryReasonIds,
    downPrompt: payload.downPrompt,
    isLoading,
  };
}
