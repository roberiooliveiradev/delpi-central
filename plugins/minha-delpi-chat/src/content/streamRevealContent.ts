import streamRevealContent from "./stream_reveal.json";

import type { AssistantContentSegment } from "../ui/components/message/assistantContentTypes";

const CONTENT = streamRevealContent;

export function streamRevealCharsPerFrame(): number {
  return CONTENT.charsPerFrame;
}

export function streamRevealProseToVisualsDelayMs(): number {
  return CONTENT.proseToVisualsDelayMs;
}

export function streamRevealVisualsCompleteDelayMs(): number {
  return CONTENT.visualsCompleteDelayMs;
}

export function streamRevealEnrichmentDelayMs(): number {
  return CONTENT.enrichmentDelayMs;
}

export function streamRevealSkeletonMinMs(): number {
  return CONTENT.skeletonMinMs;
}

export function streamRevealSegmentDelayMs(
  kind: AssistantContentSegment["kind"] | "segmentSkeleton",
): number {
  const delays = CONTENT.segmentDelaysMs as Record<string, number>;
  return delays[kind] ?? 280;
}
