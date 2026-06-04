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
  planUsesHumanizedSections,
  type StackPresentationPlan,
  type StackTableRole,
} from "./presentationStackPlan";
import {
  buildStackSectionChrome,
  type StackSectionChrome,
  type StackSectionId,
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

function resolveStackSection(sectionId: StackSectionId): StackSectionChrome {
  return buildStackSectionChrome(sectionId);
}

function maybePushStackSection(
  plan: StackPresentationPlan,
  segments: AssistantContentSegment[],
  sectionId: StackSectionId,
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  if (!planUsesHumanizedSections(plan)) {
    return;
  }

  const visibility = plan.sectionVisibility;

  if (visibility && visibility[sectionId] !== true) {
    return;
  }

  pushStackSection(segments, resolveStackSection(sectionId), appendUnique);
}

function pushSectionFraming(
  plan: StackPresentationPlan,
  segments: AssistantContentSegment[],
  sectionId: StackSectionId,
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  const framing = String(plan.sectionFraming?.[sectionId] || "").trim();

  if (!framing) {
    return;
  }

  pushMarkdownSegments(segments, framing, parseMarkdown, appendUnique);
}

/** Remove cabeçalhos internos que duplicam o título da seção humanizada. */
function stripRedundantSectionHeadings(markdown: string, kind: "destaques" | "pontos"): string {
  if (kind === "destaques") {
    return markdown.replace(/^\s*\*\*Destaques\*\*\s*\n*/i, "").trim();
  }

  return markdown
    .replace(/^\s*\*\*Pontos de atenção[^*]*\*\*\s*\n*/i, "")
    .trim();
}

function normalizeLeadProse(lead: string): string {
  const paragraphs = lead.split(/\n{2,}/).map((part) => part.trim()).filter(Boolean);
  const unique: string[] = [];

  for (const paragraph of paragraphs) {
    const key = paragraph.toLowerCase();

    if (unique.some((item) => item.toLowerCase() === key)) {
      continue;
    }

    unique.push(paragraph);
  }

  return unique.join("\n\n");
}

function pushMarkdownSegments(
  segments: AssistantContentSegment[],
  prose: string,
  parseMarkdown: (prose: string) => AssistantContentSegment[],
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
  plan: StackPresentationPlan,
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  options?: { sectionPerRole?: boolean },
): void {
  const buckets = bucketTableSegmentsByRole(tables, inferTableRoleFromTitle);
  const sectionPerRole = options?.sectionPerRole === true;
  const roleToSection: Partial<Record<StackTableRole, StackSectionId>> = {
    guide: "guide",
    inspection: "inspection",
  };

  for (const role of roles) {
    const roleTables = buckets[role];

    if (!roleTables.length) {
      continue;
    }

    if (sectionPerRole && planUsesHumanizedSections(plan)) {
      const sectionId = roleToSection[role];
      const visibility = plan.sectionVisibility;

      if (sectionId && (!visibility || visibility[sectionId] === true)) {
        maybePushStackSection(plan, segments, sectionId, appendUnique);
        pushSectionFraming(plan, segments, sectionId, parseMarkdown, appendUnique);
      }
    }

    for (const segment of roleTables) {
      appendUnique(segments, segment);
    }
  }
}

function appendTailVisuals(
  segments: AssistantContentSegment[],
  orderedVisuals: AssistantContentSegment[],
  plan: StackPresentationPlan,
  parseMarkdown: (prose: string) => AssistantContentSegment[],
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
      const trees = byKind.get("tree") ?? [];

      if (trees.length) {
        maybePushStackSection(plan, segments, "structure", appendUnique);
        pushSectionFraming(plan, segments, "structure", parseMarkdown, appendUnique);

        for (const segment of trees) {
          appendUnique(segments, segment);
        }
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

function profileTablesForPlan(
  tables: AssistantContentSegment[],
  profileRoles: StackTableRole[],
): AssistantContentSegment[] {
  const buckets = bucketTableSegmentsByRole(tables, inferTableRoleFromTitle);

  return profileRoles.flatMap((role) => buckets[role]);
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
  const narrativeSlots = new Set(plan.narrativeOrder);

  const appendSlot = (slot: string) => {
    if (!narrativeSlots.has(slot as (typeof plan.narrativeOrder)[number])) {
      return;
    }

    switch (slot) {
      case "lead": {
        const hasLead =
          Boolean(sections.lead?.trim()) ||
          (!sections.hasSectionBreaks && commentary.trim());

        if (!hasLead) {
          break;
        }

        maybePushStackSection(plan, segments, "scope", appendUnique);
        pushSectionFraming(plan, segments, "scope", parseMarkdown, appendUnique);

        const leadProse = sections.lead
          ? normalizeLeadProse(sections.lead)
          : normalizeLeadProse(commentary);

        if (leadProse) {
          pushMarkdownSegments(segments, leadProse, parseMarkdown, appendUnique);
        }

        break;
      }

      case "profileTables": {
        const profileTables = profileTablesForPlan(tables, profileRoles);

        if (!profileTables.length) {
          break;
        }

        maybePushStackSection(plan, segments, "profile", appendUnique);
        pushSectionFraming(plan, segments, "profile", parseMarkdown, appendUnique);
        appendTablesForRoles(segments, tables, profileRoles, plan, parseMarkdown, appendUnique);
        break;
      }

      case "highlights":
        if (sections.destaques?.trim()) {
          maybePushStackSection(plan, segments, "highlights", appendUnique);
          pushSectionFraming(plan, segments, "highlights", parseMarkdown, appendUnique);
          pushMarkdownSegments(
            segments,
            stripRedundantSectionHeadings(sections.destaques, "destaques"),
            parseMarkdown,
            appendUnique,
          );
        }

        break;

      case "operationalTables":
        appendTablesForRoles(segments, tables, operationalRoles, plan, parseMarkdown, appendUnique, {
          sectionPerRole: true,
        });
        break;

      case "tailVisuals":
        appendTailVisuals(segments, orderedVisuals, plan, parseMarkdown, appendUnique);
        break;

      case "attention":
        if (sections.pontos?.trim()) {
          maybePushStackSection(plan, segments, "attention", appendUnique);
          pushSectionFraming(plan, segments, "attention", parseMarkdown, appendUnique);
          pushMarkdownSegments(
            segments,
            stripRedundantSectionHeadings(sections.pontos, "pontos"),
            parseMarkdown,
            appendUnique,
          );
        }

        break;

      default:
        break;
    }
  };

  for (const slot of plan.narrativeOrder) {
    appendSlot(slot);
  }

  if (
    plan.attentionLast &&
    sections.pontos?.trim() &&
    !segments.some(
      (segment) =>
        segment.kind === "markdown" && segment.markdown.includes("Pontos de atenção"),
    )
  ) {
    maybePushStackSection(plan, segments, "attention", appendUnique);
    pushSectionFraming(plan, segments, "attention", parseMarkdown, appendUnique);
    pushMarkdownSegments(
      segments,
      stripRedundantSectionHeadings(sections.pontos, "pontos"),
      parseMarkdown,
      appendUnique,
    );
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

  return buildPlanOrderedStackSegments(
    trimmedCommentary,
    orderedVisuals,
    parseMarkdown,
    appendUnique,
    plan,
  );
}
