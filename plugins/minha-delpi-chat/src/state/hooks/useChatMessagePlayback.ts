import { useEffect, useRef } from "react";

import { useSegmentRevealQueue } from "./useSegmentRevealQueue";

export type ChatPlaybackPayload = {
  messageId: string;
  answer: string;
  sources: import("../../data/api/chatTypes").ChatSource[];
  toolCalls: import("../../data/api/chatTypes").ChatToolCall[];
  adminDebug?: Record<string, unknown> | null;
  metadata?: import("../../data/api/chatTypes").ChatMessageMetadata | null;
  /** Evita reanimar texto já exibido durante o stream legado (tokens SSE). */
  skipReveal?: boolean;
};

export function useChatMessagePlayback(
  payload: ChatPlaybackPayload | null,
  onComplete?: () => void,
) {
  const reveal = useSegmentRevealQueue({
    messageId: payload?.messageId,
    answer: payload?.answer ?? "",
    toolCalls: payload?.toolCalls ?? [],
    enabled: Boolean(payload),
    skipReveal: payload?.skipReveal,
  });

  const completedRef = useRef(false);

  useEffect(() => {
    completedRef.current = false;
  }, [payload?.messageId]);

  useEffect(() => {
    if (!payload || reveal.isPlaying || reveal.phase !== "done") {
      return;
    }

    if (completedRef.current) {
      return;
    }

    completedRef.current = true;
    onComplete?.();
  }, [onComplete, payload, reveal.isPlaying, reveal.phase]);

  return {
    displayedAnswer: reveal.displayedAnswer,
    showPresentation: reveal.showPresentation,
    visibleSegmentLimit: reveal.visibleSegmentLimit,
    showSegmentSkeleton: reveal.showSegmentSkeleton,
    isPlaying: reveal.isPlaying,
  };
}
