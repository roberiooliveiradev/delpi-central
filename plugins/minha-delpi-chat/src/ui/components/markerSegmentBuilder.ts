import type { AssistantContentSegment } from "./assistantContentTypes";
import { splitMarkdownWithPresentationMarkers as splitMarkerSegments } from "./assistantContentInterleave";
import { parseMarkdownAndCodeSegments } from "./sqlMarkdownNormalizer";

export function splitMarkdownWithPresentationMarkers(
  markdown: string,
  visuals: AssistantContentSegment[],
): AssistantContentSegment[] {
  return splitMarkerSegments(markdown, visuals, parseMarkdownAndCodeSegments);
}

export function hasPresentationMarkerSyntax(markdown: string): boolean {
  return /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)/i.test(markdown);
}
