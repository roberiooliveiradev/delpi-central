import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  bucketTableSegmentsByRole,
  partitionCommentarySections,
} from "./assistantContentInterleave";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { getChartExplanationFromToolCalls } from "./chartExplain";
import {
  getRenderPlanFromToolCalls,
  type PresentationRenderPlan,
} from "./chatPresentation";
import { stripPresentationSectionMarkers } from "./chatMarkdown";
import { dedupeTableSegments } from "./presentationTableDedup";
import {
  getStackPresentationPlanFromToolCalls,
  planUsesHumanizedSections,
  planUsesSummaryThenEvidence,
  resolveTableRole,
  type StackPresentationPlan,
  type StackTableRole,
} from "./presentationStackPlan";
import {
  buildStackSectionChrome,
  type StackSectionChrome,
  type StackSectionId,
} from "./presentationStackSections";

const PRESENTATION_MARKER_RE =
  /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)(?::\d+)?]]/gi;

function stripPresentationMarkersFromMarkdown(markdown: string): string {
  return stripPresentationSectionMarkers(
    String(markdown || "").replace(PRESENTATION_MARKER_RE, ""),
  );
}

function metadataStructureDedupApplied(toolCalls: ChatToolCall[]): boolean {
  return toolCalls.some(
    (toolCall) => (toolCall.metadata as Record<string, unknown> | undefined)?.structureDedupApplied === true,
  );
}

function usesStackSectionChrome(plan: StackPresentationPlan): boolean {
  return planUsesHumanizedSections(plan) && !planUsesSummaryThenEvidence(plan);
}

function pushStackSection(
  segments: AssistantContentSegment[],
  section: StackSectionChrome,
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
): void {
  appendUnique(segments, { kind: "stackSection", section });
}

function maybePushStackSection(
  plan: StackPresentationPlan,
  segments: AssistantContentSegment[],
  sectionId: StackSectionId,
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  toolCalls: ChatToolCall[],
): void {
  if (!usesStackSectionChrome(plan)) {
    return;
  }

  const visibility = plan.sectionVisibility;

  if (visibility && visibility[sectionId] !== true) {
    return;
  }

  pushStackSection(segments, buildStackSectionChrome(sectionId), appendUnique);
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

  for (const segment of parseMarkdown(framing)) {
    appendUnique(segments, segment);
  }
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

function operationalTableRoles(plan: StackPresentationPlan): StackTableRole[] {
  if (!plan.tableRoleOrder.length) {
    return [];
  }

  return plan.tableRoleOrder.filter((role) => role !== "profile");
}

function appendTablesForRoles(
  segments: AssistantContentSegment[],
  tables: AssistantContentSegment[],
  roles: StackTableRole[],
  plan: StackPresentationPlan,
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  toolCalls: ChatToolCall[],
  options?: { sectionPerRole?: boolean },
): void {
  const buckets = bucketTableSegmentsByRole(
    tables,
    resolveTableRole,
    metadataStructureDedupApplied(toolCalls),
  );
  const evidenceFirst = planUsesSummaryThenEvidence(plan);
  const explicitSectionPerRole = options?.sectionPerRole;
  const sectionPerRole =
    explicitSectionPerRole === true ||
    (explicitSectionPerRole !== false && usesStackSectionChrome(plan));
  const roleToSection: Partial<Record<StackTableRole, StackSectionId>> = {
    profile: "profile",
    guide: "guide",
    inspection: "inspection",
    stock: "profile",
    structure: "structure",
    list: "guide",
    pricing: "profile",
    other: "guide",
  };

  for (const role of roles) {
    const roleTables = buckets[role];

    if (!roleTables.length) {
      continue;
    }

    if (sectionPerRole || evidenceFirst) {
      const sectionId = roleToSection[role];
      const visibility = plan.sectionVisibility;

      if (sectionId && (!visibility || visibility[sectionId] === true)) {
        if (sectionPerRole) {
          maybePushStackSection(plan, segments, sectionId, appendUnique, toolCalls);
        }

        pushSectionFraming(plan, segments, sectionId, parseMarkdown, appendUnique);
      }
    }

    for (const segment of roleTables) {
      appendUnique(segments, segment);
    }
  }
}

function buildVisualPool(
  orderedVisuals: AssistantContentSegment[],
): Map<string, AssistantContentSegment[]> {
  const pool = new Map<string, AssistantContentSegment[]>();

  for (const visual of orderedVisuals) {
    if (visual.kind === "table" || visual.kind === "markdown" || visual.kind === "code") {
      continue;
    }

    const list = pool.get(visual.kind) ?? [];
    list.push(visual);
    pool.set(visual.kind, list);
  }

  return pool;
}

function takeVisual(
  kind: string,
  pool: Map<string, AssistantContentSegment[]>,
  used: Set<AssistantContentSegment>,
): AssistantContentSegment | null {
  const candidates = pool.get(kind) ?? [];
  const next = candidates.find((item) => !used.has(item));

  if (!next) {
    return null;
  }

  used.add(next);
  return next;
}

function appendLeadMarkdown(
  segments: AssistantContentSegment[],
  commentary: string,
  plan: StackPresentationPlan,
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (target: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  toolCalls: ChatToolCall[],
): void {
  const sections = partitionCommentarySections(stripPresentationMarkersFromMarkdown(commentary));
  const hasLead =
    Boolean(sections.lead?.trim()) || (!sections.hasSectionBreaks && commentary.trim());

  if (!hasLead) {
    return;
  }

  maybePushStackSection(plan, segments, "scope", appendUnique, toolCalls);

  const leadProse = sections.lead
    ? normalizeLeadProse(sections.lead)
    : normalizeLeadProse(commentary);

  if (leadProse) {
    pushMarkdownSegments(segments, leadProse, parseMarkdown, appendUnique);
  }
}

export function buildSegmentsFromRenderPlan(
  commentary: string,
  orderedVisuals: AssistantContentSegment[],
  parseMarkdown: (prose: string) => AssistantContentSegment[],
  appendUnique: (segments: AssistantContentSegment[], segment: AssistantContentSegment) => void,
  toolCalls: ChatToolCall[] = [],
): AssistantContentSegment[] | null {
  const renderPlan = getRenderPlanFromToolCalls(toolCalls);

  if (!isRenderablePlan(renderPlan)) {
    return null;
  }

  const plan = getStackPresentationPlanFromToolCalls(toolCalls);
  const segments: AssistantContentSegment[] = [];
  const sections = partitionCommentarySections(
    stripPresentationMarkersFromMarkdown(commentary),
  );
  const tables = orderedVisuals.filter((segment) => segment.kind === "table");
  const visualPool = buildVisualPool(orderedVisuals);
  const usedVisuals = new Set<AssistantContentSegment>();
  const profileRoles: StackTableRole[] = plan.profileFirst ? ["profile"] : [];

  for (const spec of renderPlan.segments ?? []) {
    const kind = String(spec.kind || "").trim().toLowerCase();
    const slot = String(spec.slot || "").trim();

    if (kind === "decision") {
      continue;
    }

    if (kind === "markdown") {
      if (slot === "lead") {
        appendLeadMarkdown(segments, commentary, plan, parseMarkdown, appendUnique, toolCalls);
        continue;
      }

      if (slot === "highlights" && sections.destaques?.trim()) {
        maybePushStackSection(plan, segments, "highlights", appendUnique, toolCalls);
        pushSectionFraming(plan, segments, "highlights", parseMarkdown, appendUnique);
        pushMarkdownSegments(
          segments,
          stripRedundantSectionHeadings(sections.destaques, "destaques"),
          parseMarkdown,
          appendUnique,
        );
        continue;
      }

      if (slot === "attention" && sections.pontos?.trim()) {
        maybePushStackSection(plan, segments, "attention", appendUnique, toolCalls);
        pushSectionFraming(plan, segments, "attention", parseMarkdown, appendUnique);
        pushMarkdownSegments(
          segments,
          stripRedundantSectionHeadings(sections.pontos, "pontos"),
          parseMarkdown,
          appendUnique,
        );
      }

      continue;
    }

    if (kind === "table") {
      if (slot === "profileTables") {
        maybePushStackSection(plan, segments, "profile", appendUnique, toolCalls);
        pushSectionFraming(plan, segments, "profile", parseMarkdown, appendUnique);
        appendTablesForRoles(
          segments,
          tables,
          profileRoles,
          plan,
          parseMarkdown,
          appendUnique,
          toolCalls,
          { sectionPerRole: false },
        );
      } else if (slot === "operationalTables") {
        appendTablesForRoles(
          segments,
          tables,
          operationalTableRoles(plan),
          plan,
          parseMarkdown,
          appendUnique,
          toolCalls,
          { sectionPerRole: true },
        );
      }

      continue;
    }

    if (kind === "chart") {
      const chartExplanation = getChartExplanationFromToolCalls(toolCalls);

      if (chartExplanation) {
        pushMarkdownSegments(segments, chartExplanation, parseMarkdown, appendUnique);
      }

      const chart = takeVisual("chart", visualPool, usedVisuals);

      if (chart) {
        appendUnique(segments, chart);
      }

      continue;
    }

    if (kind === "tree") {
      const tree = takeVisual("tree", visualPool, usedVisuals);

      if (tree) {
        maybePushStackSection(plan, segments, "structure", appendUnique, toolCalls);
        pushSectionFraming(plan, segments, "structure", parseMarkdown, appendUnique);
        appendUnique(segments, tree);
      }

      continue;
    }

    if (kind === "kpi" || kind === "dashboard") {
      const visual = takeVisual(kind, visualPool, usedVisuals);

      if (visual) {
        appendUnique(segments, visual);
      }
    }
  }

  if (
    plan.attentionLast &&
    sections.pontos?.trim() &&
    !renderPlan.segments?.some(
      (spec) => String(spec.slot || "").trim() === "attention",
    ) &&
    !segments.some(
      (segment) =>
        segment.kind === "markdown" && segment.markdown.includes("Pontos de atenção"),
    )
  ) {
    maybePushStackSection(plan, segments, "attention", appendUnique, toolCalls);
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

function isRenderablePlan(renderPlan: PresentationRenderPlan | null): renderPlan is PresentationRenderPlan {
  return Boolean(
    renderPlan &&
      renderPlan.version === 1 &&
      Array.isArray(renderPlan.segments) &&
      renderPlan.segments.length > 0,
  );
}
