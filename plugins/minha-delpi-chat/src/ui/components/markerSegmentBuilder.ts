import type { AssistantContentSegment } from "./assistantContentTypes";
import { buildInterleavedStackSegments } from "./assistantContentInterleave";
import { appendVisualSegment } from "./segmentDedupe";
import { parseMarkdownAndCodeSegments } from "./sqlMarkdownNormalizer";

export function splitMarkdownWithPresentationMarkers(
  markdown: string,
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] {
  return buildInterleavedStackSegments(
    markdown,
    visuals,
    parseMarkdownAndCodeSegments,
    appendVisualSegment,
  );
}

export function hasPresentationMarkerSyntax(markdown: string): boolean {
  return /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)/i.test(markdown);
}
