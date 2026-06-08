import { useEffect, useRef, useState } from "react";

import type { ChatSource, ChatToolCall } from "../../data/api/chatTypes";
import { shouldBypassIncrementalTextReveal } from "../../ui/components/assistantProseRendering";
import {
  isShortPresentationCaption,
  shouldShowRichPresentation,
} from "../../ui/components/chatPresentation";

import { runNaturalTextReveal } from "./naturalTextReveal";

export type ChatPlaybackPayload = {
  messageId: string;
  answer: string;
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
  adminDebug?: Record<string, unknown> | null;
  /** Evita reanimar texto já exibido durante o stream legado (tokens SSE). */
  skipReveal?: boolean;
};

const PLAYBACK_CHARS_PER_FRAME = 3;
const PRESENTATION_REVEAL_MS = 420;

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
    if (!payload) {
      setDisplayedAnswer("");
      setShowPresentation(false);
      setIsPlaying(false);
      return;
    }

    const hasRichPresentation = shouldShowRichPresentation(
      payload.answer,
      payload.toolCalls,
    );

    const skipIncrementalReveal =
      payload.skipReveal || shouldBypassIncrementalTextReveal(payload.answer);

    if (skipIncrementalReveal) {
      setDisplayedAnswer(payload.answer);
      setShowPresentation(hasRichPresentation);
      setIsPlaying(false);

      const timer = window.setTimeout(() => {
        onCompleteRef.current?.();
      }, 0);

      return () => {
        window.clearTimeout(timer);
      };
    }

    if (!payload.answer.trim()) {
      setDisplayedAnswer("");

      if (hasRichPresentation) {
        setShowPresentation(true);
        setIsPlaying(true);

        const timer = window.setTimeout(() => {
          setIsPlaying(false);
          onCompleteRef.current?.();
        }, 120);

        return () => {
          window.clearTimeout(timer);
        };
      }

      setShowPresentation(false);
      setIsPlaying(false);

      const timer = window.setTimeout(() => {
        onCompleteRef.current?.();
      }, 0);

      return () => {
        window.clearTimeout(timer);
      };
    }

    if (
      hasRichPresentation &&
      !isShortPresentationCaption(payload.answer, payload.toolCalls)
    ) {
      setDisplayedAnswer(payload.answer);
      setShowPresentation(true);
      setIsPlaying(false);

      const timer = window.setTimeout(() => {
        onCompleteRef.current?.();
      }, 120);

      return () => {
        window.clearTimeout(timer);
      };
    }

    const fullText = payload.answer;
    let cancelled = false;
    let presentationTimer = 0;
    let completeTimer = 0;

    setIsPlaying(true);
    setDisplayedAnswer("");
    setShowPresentation(false);

    const cancelReveal = runNaturalTextReveal({
      fullText,
      charsPerFrame: PLAYBACK_CHARS_PER_FRAME,
      onUpdate: (visible) => {
        if (!cancelled) {
          setDisplayedAnswer(visible);
        }
      },
      onComplete: () => {
        if (cancelled) {
          return;
        }

        presentationTimer = window.setTimeout(() => {
          if (cancelled) {
            return;
          }

          if (hasRichPresentation) {
            setShowPresentation(true);
          }

          completeTimer = window.setTimeout(() => {
            if (cancelled) {
              return;
            }

            setIsPlaying(false);
            onCompleteRef.current?.();
          }, PRESENTATION_REVEAL_MS);
        }, 40);
      },
    });

    return () => {
      cancelled = true;
      cancelReveal();
      window.clearTimeout(presentationTimer);
      window.clearTimeout(completeTimer);
    };
  }, [payload?.messageId, payload?.answer, payload?.toolCalls, payload?.skipReveal]);

  return {
    displayedAnswer,
    showPresentation,
    isPlaying,
  };
}
