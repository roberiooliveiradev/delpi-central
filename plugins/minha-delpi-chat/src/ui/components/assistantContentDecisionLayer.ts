import type { ChatToolCall } from "../../data/api/chatTypes";

import type { AssistantContentSegment } from "./assistantContentTypes";
import { getStoryPresentationFromToolCalls } from "./chatPresentation";

export function stripSummarySectionFromMarkdown(markdown: string): string {
  const marker = "<!-- section:summary -->";
  const index = markdown.indexOf(marker);

  if (index < 0) {
    return markdown;
  }

  const tail = markdown.slice(index + marker.length);
  const nextMarkerMatch = tail.match(/\n<!-- section:[^>]+ -->/);

  if (nextMarkerMatch?.index != null) {
    const head = markdown.slice(0, index).trim();
    const remainder = tail.slice(nextMarkerMatch.index + 1).trim();

    return [head, remainder].filter(Boolean).join("\n\n").trim();
  }

  const highlightsIndex = tail.search(/\n\*\*Indicadores principais\*\*|\n\*\*Destaques\*\*/);

  if (highlightsIndex >= 0) {
    const head = markdown.slice(0, index).trim();
    const remainder = tail.slice(highlightsIndex + 1).trim();

    return [head, remainder].filter(Boolean).join("\n\n").trim();
  }

  return markdown.slice(0, index).trim();
}

export function withDecisionLayer(
  segments: AssistantContentSegment[],
  toolCalls: ChatToolCall[],
): AssistantContentSegment[] {
  const story = getStoryPresentationFromToolCalls(toolCalls);

  if (!story?.blocks?.length) {
    return segments;
  }

  const decisionSegment: AssistantContentSegment = {
    kind: "decision",
    presentation: story,
  };
  const normalized = segments.map((segment) => {
    if (segment.kind !== "markdown") {
      return segment;
    }

    const stripped = stripSummarySectionFromMarkdown(segment.markdown).trim();

    if (!stripped) {
      return segment;
    }

    return { ...segment, markdown: stripped };
  });

  return [decisionSegment, ...normalized];
}
