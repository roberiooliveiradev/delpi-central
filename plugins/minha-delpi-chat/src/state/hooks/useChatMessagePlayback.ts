import { useEffect, useRef, useState } from "react";

import type { ChatSource, ChatToolCall } from "../../data/api/chatTypes";

export type ChatPlaybackPayload = {
  messageId: string;
  answer: string;
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
  adminDebug?: Record<string, unknown> | null;
};

const TEXT_CHUNK_CHARS = 2;
const TEXT_DELAY_MS = 45;
const PRESENTATION_REVEAL_MS = 480;

export function useChatMessagePlayback(
  payload: ChatPlaybackPayload | null,
  onComplete?: () => void,
) {
  const [displayedAnswer, setDisplayedAnswer] = useState("");
  const [showPresentation, setShowPresentation] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const onCompleteRef = useRef(onComplete);

  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (!payload?.answer) {
      setDisplayedAnswer("");
      setShowPresentation(false);
      setIsPlaying(false);
      return;
    }

    const fullText = payload.answer;
    let index = 0;
    let cancelled = false;

    setIsPlaying(true);
    setDisplayedAnswer("");
    setShowPresentation(false);

    const tick = () => {
      if (cancelled) {
        return;
      }

      index = Math.min(fullText.length, index + TEXT_CHUNK_CHARS);
      setDisplayedAnswer(fullText.slice(0, index));

      if (index < fullText.length) {
        window.setTimeout(tick, TEXT_DELAY_MS);
        return;
      }

      window.setTimeout(() => {
        if (cancelled) {
          return;
        }

        setShowPresentation(true);

        window.setTimeout(() => {
          if (cancelled) {
            return;
          }

          setIsPlaying(false);
          onCompleteRef.current?.();
        }, PRESENTATION_REVEAL_MS);
      }, 60);
    };

    window.setTimeout(tick, TEXT_DELAY_MS);

    return () => {
      cancelled = true;
    };
  }, [payload?.messageId, payload?.answer]);

  return {
    displayedAnswer,
    showPresentation,
    isPlaying,
  };
}
