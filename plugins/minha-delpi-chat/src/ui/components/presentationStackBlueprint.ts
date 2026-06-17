import type { ChatToolCall } from "../../data/api/chatTypes";

import { stripPresentationSectionMarkers } from "./chatMarkdown";
import type { AssistantContentSegment } from "./message/assistantContentTypes";
import type { CommentarySections } from "./message/assistantContentInterleave";
import { buildMultiRouteStackSegments } from "./presentationMultiRoute";
import { buildSegmentsFromRenderPlan } from "./renderPlanSegmentBuilder";

const PRESENTATION_MARKER_RE =
  /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)(?::\d+)?]]/gi;

export function stripPresentationMarkersFromMarkdown(markdown: string): string {
  return stripPresentationSectionMarkers(
    String(markdown || "").replace(PRESENTATION_MARKER_RE, ""),
  );
}

export function stripInlineTableMarkers(markdown: string): string {
  return stripPresentationMarkersFromMarkdown(markdown);
}

export function commentaryHasStructuredSections(sections: CommentarySections): boolean {
  return sections.hasSectionBreaks;
}

export function buildCanonicalStackSegments(
  commentary: string,
  orderedVisuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (segments: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  toolCalls: ChatToolCall[] = [],
): AssistantContentSegment[] {
  const trimmedCommentary = String(commentary || "").trim();
  const multiRoute = buildMultiRouteStackSegments(
    trimmedCommentary,
    toolCalls,
    appendUnique,
  );

  if (multiRoute?.length) {
    return multiRoute;
  }

  const fromRenderPlan = buildSegmentsFromRenderPlan(
    trimmedCommentary,
    orderedVisuals,
    parseMarkdown,
    appendUnique,
    toolCalls,
  );

  if (fromRenderPlan?.length) {
    return fromRenderPlan;
  }

  if (trimmedCommentary) {
    const fallback: AssistantContentSegment[] = [];

    for (const segment of parseMarkdown(trimmedCommentary)) {
      appendUnique(fallback, segment);
    }

    return fallback;
  }

  return [];
}
