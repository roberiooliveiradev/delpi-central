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
import {
  STACK_SECTION_BY_ID,
  stackSectionForRole,
  type StackSectionChrome,
} from "./presentationStackSections";
import { dedupeTableSegments } from "./presentationTableDedup";

const PRESENTATION_MARKER_RE =
  /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)(?::\d+)?]]/gi;

export function stripPresentationMarkersFromMarkdown(markdown: string): string {
  return String(markdown || "")
    .replace(PRESENTATION_MARKER_RE, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function stripInlineTableMarkers(markdown: string): string {
  return stripPresentationMarkersFromMarkdown(markdown);
}

export function commentaryHasStructuredSections(sections: CommentarySections): boolean {
  return sections.hasSectionBreaks;
}

function pushStackSection(
  segments: AssistantContentSegment[],
  section: StackSectionChrome,
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  appendUnique(segments, { kind: "stackSection", section });
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
  options?: { sectionPerRole?: boolean },
): void {
  const buckets = bucketTableSegmentsByRole(tables, inferTableRoleFromTitle);
  const sectionPerRole = options?.sectionPerRole === true;

  for (const role of roles) {
    const chrome = sectionPerRole ? stackSectionForRole(role) : null;

    if (chrome) {
      pushStackSection(segments, chrome, appendUnique);
    }

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
      pushStackSection(segments, STACK_SECTION_BY_ID.structure, appendUnique);

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
  const sections = partitionCommentarySections(
    stripPresentationMarkersFromMarkdown(commentary),
  );
  const segments: AssistantContentSegment[] = [];
  const tables = orderedVisuals.filter((segment) => segment.kind === "table");
  const profileRoles: StackTableRole[] = plan.profileFirst ? ["profile"] : [];
  const operationalRoles = operationalTableRoles(plan);

  const appendSlot = (slot: string) => {
    switch (slot) {
      case "lead":
        pushStackSection(segments, STACK_SECTION_BY_ID.scope, appendUnique);

        if (sections.lead) {
          pushMarkdownSegments(segments, sections.lead, parseMarkdown, appendUnique);
        } else if (!sections.hasSectionBreaks && commentary.trim()) {
          pushMarkdownSegments(segments, commentary, parseMarkdown, appendUnique);
        }

        break;

      case "profileTables":
        pushStackSection(segments, STACK_SECTION_BY_ID.profile, appendUnique);
        appendTablesForRoles(segments, tables, profileRoles, appendUnique);
        break;

      case "highlights":
        if (sections.destaques) {
          pushStackSection(segments, STACK_SECTION_BY_ID.highlights, appendUnique);
          pushMarkdownSegments(segments, sections.destaques, parseMarkdown, appendUnique);
        }

        break;

      case "operationalTables":
        appendTablesForRoles(segments, tables, operationalRoles, appendUnique, {
          sectionPerRole: true,
        });
        break;

      case "tailVisuals":
        appendTailVisuals(segments, orderedVisuals, plan, appendUnique);
        break;

      case "attention":
        if (sections.pontos) {
          pushStackSection(segments, STACK_SECTION_BY_ID.attention, appendUnique);
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
    pushStackSection(segments, STACK_SECTION_BY_ID.attention, appendUnique);
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
  const hasEmbeddedMarkers = PRESENTATION_MARKER_RE.test(trimmedCommentary);

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

  if (hasEmbeddedMarkers) {
    return buildPlanOrderedStackSegments(
      stripPresentationMarkersFromMarkdown(trimmedCommentary),
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
