import { useEffect, useMemo, useRef, useState } from "react";

import type { ChatToolCall } from "../../data/api/chatTypes";
import { buildAssistantContentSegments } from "../../ui/components/message/assistantContentSegments";
import type { AssistantContentSegment } from "../../ui/components/message/assistantContentTypes";
import { shouldBypassIncrementalTextReveal } from "../../ui/components/message/assistantProseRendering";
import {
  isShortPresentationCaption,
  shouldShowRichPresentation,
} from "../../ui/components/chatPresentation";
import {
  streamRevealCharsPerFrame,
  streamRevealProseToVisualsDelayMs,
  streamRevealSegmentDelayMs,
  streamRevealSkeletonMinMs,
  streamRevealVisualsCompleteDelayMs,
} from "../../content/streamRevealContent";

import { runNaturalTextReveal } from "./naturalTextReveal";

export type SegmentRevealPhase = "idle" | "prose" | "visuals" | "done";

export type SegmentRevealInput = {
  messageId?: string;
  answer: string;
  toolCalls: ChatToolCall[];
  enabled?: boolean;
  skipReveal?: boolean;
  showPresentation?: boolean;
};

export type SegmentRevealResult = {
  displayedAnswer: string;
  showPresentation: boolean;
  visibleSegmentLimit: number | undefined;
  showSegmentSkeleton: boolean;
  phase: SegmentRevealPhase;
  isPlaying: boolean;
};

function isVisualSegment(segment: AssistantContentSegment): boolean {
  return segment.kind !== "markdown" && segment.kind !== "code";
}

function resolveRevealSegments(
  answer: string,
  toolCalls: ChatToolCall[],
): AssistantContentSegment[] {
  return buildAssistantContentSegments(answer, toolCalls);
}

export function useSegmentRevealQueue({
  messageId,
  answer,
  toolCalls,
  enabled = true,
  skipReveal = false,
  showPresentation: showPresentationOverride,
}: SegmentRevealInput): SegmentRevealResult {
  const [displayedAnswer, setDisplayedAnswer] = useState("");
  const [showPresentation, setShowPresentation] = useState(false);
  const [visibleSegmentLimit, setVisibleSegmentLimit] = useState<number | undefined>(
    undefined,
  );
  const [showSegmentSkeleton, setShowSegmentSkeleton] = useState(false);
  const [phase, setPhase] = useState<SegmentRevealPhase>("idle");
  const [isPlaying, setIsPlaying] = useState(false);

  const segments = useMemo(
    () => resolveRevealSegments(answer, toolCalls),
    [answer, toolCalls],
  );

  const visualSegmentCount = useMemo(
    () => segments.filter((segment) => isVisualSegment(segment)).length,
    [segments],
  );

  useEffect(() => {
    if (!enabled) {
      setDisplayedAnswer(answer);
      setShowPresentation(Boolean(showPresentationOverride));
      setVisibleSegmentLimit(undefined);
      setShowSegmentSkeleton(false);
      setPhase("done");
      setIsPlaying(false);
      return;
    }

    const hasRichPresentation = shouldShowRichPresentation(answer, toolCalls);
    const skipIncrementalReveal =
      skipReveal || shouldBypassIncrementalTextReveal(answer);

    if (skipIncrementalReveal) {
      setDisplayedAnswer(answer);
      setShowPresentation(hasRichPresentation);
      setVisibleSegmentLimit(undefined);
      setShowSegmentSkeleton(false);
      setPhase("done");
      setIsPlaying(false);
      return;
    }

    if (!answer.trim()) {
      setDisplayedAnswer("");

      if (hasRichPresentation) {
        setShowPresentation(true);
        setVisibleSegmentLimit(segments.length);
        setShowSegmentSkeleton(false);
        setPhase("done");
        setIsPlaying(true);

        const timer = window.setTimeout(() => {
          setIsPlaying(false);
        }, streamRevealSkeletonMinMs());

        return () => {
          window.clearTimeout(timer);
        };
      }

      setShowPresentation(false);
      setVisibleSegmentLimit(undefined);
      setShowSegmentSkeleton(false);
      setPhase("done");
      setIsPlaying(false);
      return;
    }

    if (
      hasRichPresentation &&
      !isShortPresentationCaption(answer, toolCalls) &&
      segments.every((segment) => segment.kind === "markdown")
    ) {
      setDisplayedAnswer(answer);
      setShowPresentation(true);
      setVisibleSegmentLimit(segments.length);
      setShowSegmentSkeleton(false);
      setPhase("done");
      setIsPlaying(false);
      return;
    }

    let cancelled = false;
    let proseTimer = 0;
    let segmentTimer = 0;
    let completeTimer = 0;
    let segmentIndex = 0;

    setIsPlaying(true);
    setDisplayedAnswer("");
    setShowPresentation(false);
    setVisibleSegmentLimit(0);
    setShowSegmentSkeleton(Boolean(hasRichPresentation));
    setPhase("prose");

    const revealNextSegment = () => {
      if (cancelled) {
        return;
      }

      segmentIndex += 1;
      setVisibleSegmentLimit(segmentIndex);

      if (segmentIndex >= segments.length) {
        setShowSegmentSkeleton(false);
        setPhase("done");
        completeTimer = window.setTimeout(() => {
          if (!cancelled) {
            setIsPlaying(false);
          }
        }, streamRevealVisualsCompleteDelayMs());
        return;
      }

      const nextSegment = segments[segmentIndex];
      const delay = streamRevealSegmentDelayMs(
        nextSegment?.kind ?? "segmentSkeleton",
      );

      segmentTimer = window.setTimeout(revealNextSegment, delay);
    };

    const startVisualReveal = () => {
      if (cancelled) {
        return;
      }

      if (!hasRichPresentation || segments.length === 0) {
        setShowPresentation(false);
        setVisibleSegmentLimit(undefined);
        setShowSegmentSkeleton(false);
        setPhase("done");
        setIsPlaying(false);
        return;
      }

      setShowPresentation(true);
      setPhase("visuals");
      setShowSegmentSkeleton(false);

      if (segments.length <= 1) {
        setVisibleSegmentLimit(segments.length);
        setPhase("done");
        completeTimer = window.setTimeout(() => {
          if (!cancelled) {
            setIsPlaying(false);
          }
        }, streamRevealVisualsCompleteDelayMs());
        return;
      }

      setVisibleSegmentLimit(1);
      const firstDelay = streamRevealSegmentDelayMs(segments[1]?.kind ?? "table");
      segmentTimer = window.setTimeout(revealNextSegment, firstDelay);
    };

    const cancelReveal = runNaturalTextReveal({
      fullText: answer,
      charsPerFrame: streamRevealCharsPerFrame(),
      onUpdate: (visible) => {
        if (!cancelled) {
          setDisplayedAnswer(visible);
        }
      },
      onComplete: () => {
        if (cancelled) {
          return;
        }

        proseTimer = window.setTimeout(startVisualReveal, streamRevealProseToVisualsDelayMs());
      },
    });

    return () => {
      cancelled = true;
      cancelReveal();
      window.clearTimeout(proseTimer);
      window.clearTimeout(segmentTimer);
      window.clearTimeout(completeTimer);
    };
  }, [
    answer,
    enabled,
    messageId,
    segments,
    showPresentationOverride,
    skipReveal,
    toolCalls,
    visualSegmentCount,
  ]);

  return {
    displayedAnswer,
    showPresentation: showPresentationOverride ?? showPresentation,
    visibleSegmentLimit,
    showSegmentSkeleton,
    phase,
    isPlaying,
  };
}
