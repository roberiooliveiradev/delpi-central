import type { ChatPresentation } from "../../data/api/chatTypes";

import type { AssistantContentSegment } from "./assistantContentTypes";
import { buildCanonicalStackSegments } from "./presentationStackBlueprint";
import { isHierarchyDuplicateTable } from "./presentationStructureDedup";

const PRESENTATION_MARKER_RE =
  /\[\[(tabela|table|grafico|chart|arvore|tree|kpi|dashboard)(?::(\d+))?]]/gi;

export type CommentarySections = {
  hasSectionBreaks: boolean;
  lead: string;
  destaques: string;
  pontos: string;
};

function sectionStartIndex(markdown: string, pattern: RegExp): number {
  const match = markdown.match(pattern);

  if (!match || match.index === undefined) {
    return -1;
  }

  return match.index;
}

const DESTAQUES_SECTION_RE = /(?:^|\n)\s*\*\*Destaques\*\*/i;
const PONTOS_SECTION_RE = /(?:^|\n)\s*\*\*Pontos de atenção/i;

export function partitionCommentarySections(markdown: string): CommentarySections {
  const trimmed = String(markdown || "").trim();

  if (!trimmed) {
    return { hasSectionBreaks: false, lead: "", destaques: "", pontos: "" };
  }

  const destaqueIndex = sectionStartIndex(trimmed, DESTAQUES_SECTION_RE);

  if (destaqueIndex < 0) {
    return { hasSectionBreaks: false, lead: trimmed, destaques: "", pontos: "" };
  }

  const pontosIndex = sectionStartIndex(trimmed, PONTOS_SECTION_RE);
  const destaquesEnd = pontosIndex >= 0 ? pontosIndex : trimmed.length;

  return {
    hasSectionBreaks: true,
    lead: trimmed.slice(0, destaqueIndex).trim(),
    destaques: trimmed.slice(destaqueIndex, destaquesEnd).trim(),
    pontos: pontosIndex >= 0 ? trimmed.slice(pontosIndex).trim() : "",
  };
}

import {
  inferTableRoleFromTitle,
  type StackTableRole,
} from "./presentationStackPlan";

function emptyRoleBuckets(): Record<StackTableRole, AssistantContentSegment[]> {
  return {
    profile: [],
    guide: [],
    inspection: [],
    stock: [],
    pricing: [],
    structure: [],
    list: [],
    other: [],
  };
}

export function bucketTableSegmentsByRole(
  tables: AssistantContentSegment[],
  resolveRole: (title: string) => StackTableRole = inferTableRoleFromTitle,
): Record<StackTableRole, AssistantContentSegment[]> {
  const buckets = emptyRoleBuckets();

  for (const segment of tables) {
    if (segment.kind !== "table") {
      continue;
    }

    if (isHierarchyDuplicateTable(segment.presentation)) {
      continue;
    }

    const role = resolveRole(String(segment.presentation.title || ""));

    buckets[role].push(segment);
  }

  return buckets;
}

function resolveMarkerPresentation(
  marker: string,
  index: number | undefined,
  visuals: AssistantContentSegment[],
  usedVisuals: Set<AssistantContentSegment>,
): AssistantContentSegment | null {
  const kind =
    marker === "tabela" || marker === "table"
      ? "table"
      : marker === "grafico" || marker === "chart"
        ? "chart"
        : marker === "arvore" || marker === "tree"
          ? "tree"
          : marker === "kpi"
            ? "kpi"
            : "dashboard";

  const pool = visuals.filter((item) => item.kind === kind);

  if (!pool.length) {
    return null;
  }

  const position = index ?? 1;
  const preferred = pool[Math.max(0, Math.min(pool.length, position) - 1)] ?? null;

  if (preferred && !usedVisuals.has(preferred)) {
    return preferred;
  }

  return pool.find((item) => !usedVisuals.has(item)) ?? null;
}

export function splitMarkdownWithPresentationMarkers(
  markdown: string,
  visuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
): AssistantContentSegment[] {
  const segments: AssistantContentSegment[] = [];
  const usedVisuals = new Set<AssistantContentSegment>();
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  const pattern = new RegExp(PRESENTATION_MARKER_RE);

  while ((match = pattern.exec(markdown)) !== null) {
    const index = match.index ?? 0;
    const prose = markdown.slice(lastIndex, index).trim();

    if (prose) {
      segments.push(...parseMarkdown(prose));
    }

    const marker = String(match[1] || "").toLowerCase();
    const markerIndex = match[2] ? Number.parseInt(match[2], 10) : undefined;
    const visual = resolveMarkerPresentation(marker, markerIndex, visuals, usedVisuals);

    if (visual) {
      usedVisuals.add(visual);
      segments.push(visual);
    }

    lastIndex = index + match[0].length;
  }

  const tail = markdown.slice(lastIndex).trim();

  if (tail) {
    segments.push(...parseMarkdown(tail));
  }

  return segments;
}

export function buildInterleavedStackSegments(
  commentary: string,
  orderedVisuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (segments: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  toolCalls: import("../../data/api/chatTypes").ChatToolCall[] = [],
): AssistantContentSegment[] {
  return buildCanonicalStackSegments(
    commentary,
    orderedVisuals,
    parseMarkdown,
    appendUnique,
    toolCalls,
  );
}

export function tablePresentationTitle(
  presentation: Extract<ChatPresentation, { type: "table" }>,
): string {
  return String(presentation.title || "").trim();
}
