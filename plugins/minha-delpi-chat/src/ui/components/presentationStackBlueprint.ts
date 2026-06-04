import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  bucketTableSegmentsByRole,
  partitionCommentarySections,
  type CommentarySections,
} from "./assistantContentInterleave";
import type { AssistantContentSegment } from "./assistantContentTypes";
import {
  getStackPresentationPlanFromToolCalls,
  inferTableRoleFromTitle,
  type StackPresentationPlan,
  type StackTableRole,
} from "./presentationStackPlan";
import { dedupeTableSegments } from "./presentationTableDedup";

const TABLE_MARKER_RE = /\[\[(?:tabela|table)(?::\d+)?]]/gi;
const TAIL_MARKER_RE = /\[\[(?:grafico|chart|arvore|tree|kpi|dashboard)(?::\d+)?]]/gi;

export function stripInlineTableMarkers(markdown: string): string {
  return String(markdown || "")
    .replace(TABLE_MARKER_RE, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function commentaryHasStructuredSections(sections: CommentarySections): boolean {
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

function appendTablesForRoles(
  segments: AssistantContentSegment[],
  tables: AssistantContentSegment[],
  roles: StackTableRole[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  const buckets = bucketTableSegmentsByRole(tables, inferTableRoleFromTitle);

  for (const role of roles) {
    for (const segment of buckets[role]) {
      appendUnique(segments, segment);
    }
  }
}

function appendTailVisuals(
  segments: AssistantContentSegment[],
  orderedVisuals: AssistantContentSegment[],
  plan: StackPresentationPlan,
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  const byKind = new Map<string, AssistantContentSegment[]>();

  for (const visual of orderedVisuals) {
    if (visual.kind === "table" || visual.kind === "markdown" || visual.kind === "code") {
      continue;
    }

    const kind = visual.kind;
    const list = byKind.get(kind) ?? [];
    list.push(visual);
    byKind.set(kind, list);
  }

  const chartLike = [...(byKind.get("chart") ?? [])];

  for (const token of plan.tailVisualOrder) {
    if (token === "chart") {
      for (const segment of chartLike) {
        appendUnique(segments, segment);
      }

      continue;
    }

    if (token === "tree") {
      for (const segment of byKind.get("tree") ?? []) {
        appendUnique(segments, segment);
      }

      continue;
    }

    if (token === "kpi") {
      for (const segment of byKind.get("kpi") ?? []) {
        appendUnique(segments, segment);
      }

      continue;
    }

    if (token === "dashboard") {
      for (const segment of byKind.get("dashboard") ?? []) {
        appendUnique(segments, segment);
      }
    }
  }

  for (const [kind, list] of byKind.entries()) {
    if (plan.tailVisualOrder.includes(kind) || kind === "chart") {
      continue;
    }

    for (const segment of list) {
      appendUnique(segments, segment);
    }
  }
}

function operationalTableRoles(plan: StackPresentationPlan): StackTableRole[] {
  return plan.tableRoleOrder.filter((role) => role !== "profile");
}

export function buildPlanOrderedStackSegments(
  commentary: string,
  orderedVisuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (segments: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  plan: StackPresentationPlan,
): AssistantContentSegment[] {
  const sections = partitionCommentarySections(stripInlineTableMarkers(commentary));
  const segments: AssistantContentSegment[] = [];
  const tables = orderedVisuals.filter((segment) => segment.kind === "table");
  const profileRoles: StackTableRole[] = plan.profileFirst ? ["profile"] : [];
  const operationalRoles = operationalTableRoles(plan);

  const appendSlot = (slot: string) => {
    switch (slot) {
      case "lead":
        if (sections.lead) {
          pushMarkdownSegments(segments, sections.lead, parseMarkdown, appendUnique);
        } else if (!sections.hasSectionBreaks && commentary.trim()) {
          pushMarkdownSegments(segments, commentary, parseMarkdown, appendUnique);
        }

        break;

      case "profileTables":
        appendTablesForRoles(segments, tables, profileRoles, appendUnique);
        break;

      case "highlights":
        if (sections.destaques) {
          pushMarkdownSegments(segments, sections.destaques, parseMarkdown, appendUnique);
        }

        break;

      case "operationalTables":
        appendTablesForRoles(segments, tables, operationalRoles, appendUnique);
        break;

      case "tailVisuals":
        appendTailVisuals(segments, orderedVisuals, plan, appendUnique);
        break;

      case "attention":
        if (sections.pontos) {
          pushMarkdownSegments(segments, sections.pontos, parseMarkdown, appendUnique);
        }

        break;

      default:
        break;
    }
  };

  if (sections.hasSectionBreaks) {
    for (const slot of plan.narrativeOrder) {
      appendSlot(slot);
    }
  } else {
    appendSlot("lead");
    appendSlot("profileTables");
    appendSlot("operationalTables");
    appendSlot("tailVisuals");
  }

  if (plan.attentionLast && sections.pontos && !segments.some(
    (segment) =>
      segment.kind === "markdown" && segment.markdown.includes("Pontos de atenção"),
  )) {
    pushMarkdownSegments(segments, sections.pontos, parseMarkdown, appendUnique);
  }

  return dedupeTableSegments(segments);
}

export function buildCanonicalStackSegments(
  commentary: string,
  orderedVisuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (segments: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  toolCalls: ChatToolCall[] = [],
): AssistantContentSegment[] {
  const trimmedCommentary = String(commentary || "").trim();
  const plan = getStackPresentationPlanFromToolCalls(toolCalls);
  const sections = partitionCommentarySections(trimmedCommentary);
  const hasTailMarkers = TAIL_MARKER_RE.test(trimmedCommentary);
  const hasTableMarkers = TABLE_MARKER_RE.test(trimmedCommentary);

  if (
    commentaryHasStructuredSections(sections) ||
    plan.profileFirst ||
    plan.attentionLast
  ) {
    return buildPlanOrderedStackSegments(
      trimmedCommentary,
      orderedVisuals,
      parseMarkdown,
      appendUnique,
      plan,
    );
  }

  if (hasTableMarkers || hasTailMarkers) {
    return buildPlanOrderedStackSegments(
      stripInlineTableMarkers(trimmedCommentary),
      orderedVisuals,
      parseMarkdown,
      appendUnique,
      plan,
    );
  }

  return buildPlanOrderedStackSegments(
    trimmedCommentary,
    orderedVisuals,
    parseMarkdown,
    appendUnique,
    plan,
  );
}
