import {
  bucketTableSegmentsByRole,
  partitionCommentarySections,
  splitMarkdownWithPresentationMarkers,
  type CommentarySections,
} from "./assistantContentInterleave";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { dedupeTableSegments } from "./presentationTableDedup";

const TABLE_MARKER_RE = /\[\[(?:tabela|table)(?::\d+)?]]/gi;
const TAIL_MARKER_RE = /\[\[(?:grafico|chart|arvore|tree|kpi|dashboard)(?::\d+)?]]/gi;

export const ANALYSER_TABLE_ORDER = ["guide", "inspection", "profile", "other"] as const;

export function stripInlineTableMarkers(markdown: string): string {
  return String(markdown || "")
    .replace(TABLE_MARKER_RE, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function commentaryHasAnalyserSections(sections: CommentarySections): boolean {
  return sections.hasSectionBreaks;
}

function pushMarkdownSegments(
  segments: AssistantContentSegment[],
  prose: string,
  parseMarkdown: (value: string) => AssistantContentSegment[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  for (const segment of parseMarkdown(prose)) {
    appendUnique(segments, segment);
  }
}

function appendTablesByRole(
  segments: AssistantContentSegment[],
  tables: AssistantContentSegment[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  const buckets = bucketTableSegmentsByRole(tables);

  for (const role of ANALYSER_TABLE_ORDER) {
    for (const segment of buckets[role]) {
      appendUnique(segments, segment);
    }
  }
}

function appendTailVisuals(
  segments: AssistantContentSegment[],
  orderedVisuals: AssistantContentSegment[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  const trees = orderedVisuals.filter((segment) => segment.kind === "tree");
  const charts = orderedVisuals.filter((segment) => segment.kind === "chart");
  const others = orderedVisuals.filter(
    (segment) =>
      segment.kind !== "table" &&
      segment.kind !== "tree" &&
      segment.kind !== "chart",
  );

  for (const segment of trees) {
    appendUnique(segments, segment);
  }

  for (const segment of charts) {
    appendUnique(segments, segment);
  }

  for (const segment of others) {
    appendUnique(segments, segment);
  }
}

export function buildSectionOrderedStackSegments(
  commentary: string,
  orderedVisuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (segments: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): AssistantContentSegment[] {
  const sections = partitionCommentarySections(stripInlineTableMarkers(commentary));
  const segments: AssistantContentSegment[] = [];
  const tables = orderedVisuals.filter((segment) => segment.kind === "table");

  if (sections.lead) {
    pushMarkdownSegments(segments, sections.lead, parseMarkdown, appendUnique);
  }

  if (sections.destaques) {
    pushMarkdownSegments(segments, sections.destaques, parseMarkdown, appendUnique);
  }

  appendTablesByRole(segments, tables, appendUnique);

  if (sections.pontos) {
    pushMarkdownSegments(segments, sections.pontos, parseMarkdown, appendUnique);
  }

  appendTailVisuals(segments, orderedVisuals, appendUnique);

  return dedupeTableSegments(segments);
}

export function buildCanonicalStackSegments(
  commentary: string,
  orderedVisuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (segments: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): AssistantContentSegment[] {
  const trimmedCommentary = String(commentary || "").trim();
  const sections = partitionCommentarySections(trimmedCommentary);
  const hasTailMarkers = TAIL_MARKER_RE.test(trimmedCommentary);
  const hasTableMarkers = TABLE_MARKER_RE.test(trimmedCommentary);

  if (commentaryHasAnalyserSections(sections)) {
    return buildSectionOrderedStackSegments(
      trimmedCommentary,
      orderedVisuals,
      parseMarkdown,
      appendUnique,
    );
  }

  if (hasTableMarkers || hasTailMarkers) {
    const markerBody = hasTableMarkers
      ? trimmedCommentary
      : stripInlineTableMarkers(trimmedCommentary);

    return dedupeTableSegments(
      splitMarkdownWithPresentationMarkers(markerBody, orderedVisuals, parseMarkdown),
    );
  }

  const segments: AssistantContentSegment[] = [];

  if (trimmedCommentary) {
    pushMarkdownSegments(segments, trimmedCommentary, parseMarkdown, appendUnique);
  }

  for (const visual of orderedVisuals) {
    appendUnique(segments, visual);
  }

  return dedupeTableSegments(segments);
}
