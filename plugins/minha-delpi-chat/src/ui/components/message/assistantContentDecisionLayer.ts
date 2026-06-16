import type { ChatToolCall } from "../../../data/api/chatTypes";

import type { AssistantContentSegment } from "./assistantContentTypes";
import {
  getStackPresentationPlanFromToolCalls,
  planUsesSummaryThenEvidence,
} from "../presentationStackPlan";
import {
  getStoryPresentationFromToolCalls,
} from "../chatPresentation";

function stripHighlightsTail(tail: string): string {
  const nextMarkerMatch = tail.match(/\n<!-- section:[^>]+ -->/);

  if (nextMarkerMatch?.index != null) {
    return tail.slice(nextMarkerMatch.index + 1).trim();
  }

  const attentionIndex = tail.search(/\n\*\*Pontos de atenção\*\*/);

  if (attentionIndex >= 0) {
    return tail.slice(attentionIndex + 1).trim();
  }

  return "";
}

export function stripHighlightsSectionFromMarkdown(markdown: string): string {
  const marker = "<!-- section:highlights -->";
  const markerIndex = markdown.indexOf(marker);

  if (markerIndex >= 0) {
    const head = markdown.slice(0, markerIndex).trim();
    const remainder = stripHighlightsTail(markdown.slice(markerIndex + marker.length));

    return [head, remainder].filter(Boolean).join("\n\n").trim();
  }

  const headerMatch = markdown.match(/(?:^|\n)(\*\*Destaques\*\*|\*\*Indicadores principais\*\*)/);

  if (!headerMatch || headerMatch.index == null) {
    return markdown;
  }

  const headerIndex = headerMatch.index;
  const head = markdown.slice(0, headerIndex).trim();
  const remainder = stripHighlightsTail(markdown.slice(headerIndex));

  return [head, remainder].filter(Boolean).join("\n\n").trim();
}

export function stripQuickLayerFromMarkdown(markdown: string): string {
  const headers = [
    /\*\*Resumo\*\*/,
    /\*\*Próxima ação recomendada\*\*/,
    /\*\*Próxima ação\*\*/,
    /\*\*Interpretação\*\*/,
  ];
  let updated = markdown;

  for (const header of headers) {
    const match = updated.match(new RegExp(`(?:^|\\n)\\s*${header.source}\\s*`, "i"));

    if (!match || match.index == null) {
      continue;
    }

    const head = updated.slice(0, match.index).trim();
    const tail = updated.slice(match.index + match[0].length);
    const nextSection = tail.search(
      /\n(?:\*\*[^*]+\*\*|<!-- section:[^>]+ -->|#{1,3} )/,
    );
    const remainder = nextSection >= 0 ? tail.slice(nextSection + 1).trim() : "";

    updated = [head, remainder].filter(Boolean).join("\n\n").trim();
  }

  updated = updated
    .replace(
      /(?:^|\n)Status geral:\s*\*\*[^*]+\*\*[^\n]*/gi,
      "",
    )
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  return updated;
}

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
  const plan = getStackPresentationPlanFromToolCalls(toolCalls);

  if (planUsesSummaryThenEvidence(plan)) {
    return segments;
  }

  const story = getStoryPresentationFromToolCalls(toolCalls);

  if (!story?.blocks?.length) {
    return segments;
  }

  const decisionSegment: AssistantContentSegment = {
    kind: "decision",
    presentation: story,
  };
  const evidenceFirst = planUsesSummaryThenEvidence(plan);
  const normalized = segments.map((segment) => {
    if (segment.kind !== "markdown") {
      return segment;
    }

    let markdown = stripSummarySectionFromMarkdown(segment.markdown);

    if (!evidenceFirst) {
      markdown = stripQuickLayerFromMarkdown(stripHighlightsSectionFromMarkdown(markdown));
    } else {
      markdown = stripHighlightsSectionFromMarkdown(markdown);
    }

    return { ...segment, markdown: markdown.trim() };
  });

  return [decisionSegment, ...normalized];
}
