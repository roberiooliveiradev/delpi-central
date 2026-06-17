import type { ChatToolCall } from "../../../../data/api/chatTypes";

import {
  bucketTableSegmentsByRole,
  partitionCommentarySections,
} from "../../message/assistantContentInterleave";
import type { AssistantContentSegment } from "../../message/assistantContentTypes";
import { getChartExplanationFromToolCalls } from "../pipeline/chartExplain";
import {
  getRenderPlanFromToolCalls,
  type PresentationRenderPlan,
} from "../../chatPresentation";
import { stripPresentationSectionMarkers } from "../../chatMarkdown";
import { dedupeTableSegments } from "../pipeline/presentationTableDedup";
import {
  getStackPresentationPlanFromToolCalls,
  planUsesHumanizedSections,
  planUsesSummaryThenEvidence,
  resolveTableRole,
  type StackPresentationPlan,
  type StackTableRole,
} from "../pipeline/presentationStackPlan";
import {
  buildStackSectionChrome,
  type StackSectionChrome,
  type StackSectionId,
} from "../pipeline/presentationStackSections";

const PRESENTATION_MARKER_RE =
  /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)(?::\d+)?]]/gi;

const VISUAL_TOKEN_TO_KEY: Record<string, string> = {
  kpi: "kpiPresentation",
  tree: "treePresentation",
  chart: "chartPresentation",
  dashboard: "dashboardPresentation",
  table: "tablePresentation",
};

const TABLE_BUNDLE_SOURCES = [
  "tablePresentations",
  "tablePresentation",
  "profileTablePresentation",
  "inspectionTablePresentation",
] as const;

type SynthesizeRenderPlanHints = {
  hasTableVisuals: boolean;
  visualKinds: Set<string>;
};

function getExternalActionMetadata(toolCalls: ChatToolCall[]): Record<string, unknown> | null {
  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    if (toolCall.metadata && typeof toolCall.metadata === "object") {
      return toolCall.metadata as Record<string, unknown>;
    }
  }

  return null;
}

function hasTextPresentation(metadata: Record<string, unknown>, commentary: string): boolean {
  if (String(commentary || "").trim()) {
    return true;
  }

  const textPresentation = metadata.textPresentation;

  if (!textPresentation || typeof textPresentation !== "object") {
    return false;
  }

  return Boolean(
    String((textPresentation as Record<string, unknown>).markdown || "").trim(),
  );
}

function hasTableBundle(metadata: Record<string, unknown>, hasTableVisuals: boolean): boolean {
  for (const key of TABLE_BUNDLE_SOURCES) {
    const presentation = metadata[key];

    if (Array.isArray(presentation) && presentation.length) {
      return true;
    }

    if (
      presentation &&
      typeof presentation === "object" &&
      (presentation as Record<string, unknown>).type === "table"
    ) {
      return true;
    }
  }

  return hasTableVisuals;
}

function hasVisualPresentation(
  metadata: Record<string, unknown>,
  token: string,
  visualKinds: Set<string>,
): boolean {
  const normalized = String(token || "").trim().toLowerCase();
  const source = VISUAL_TOKEN_TO_KEY[normalized];

  if (source && metadata[source]) {
    return true;
  }

  return visualKinds.has(normalized);
}

function shouldIncludeDecision(
  metadata: Record<string, unknown>,
  plan: StackPresentationPlan,
): boolean {
  if (planUsesSummaryThenEvidence(plan)) {
    return false;
  }

  const dataAnswer = metadata.dataAnswer;

  return Boolean(
    dataAnswer &&
      typeof dataAnswer === "object" &&
      (dataAnswer as Record<string, unknown>).summary &&
      typeof (dataAnswer as Record<string, unknown>).summary === "object",
  );
}

function markdownHasHighlights(commentary: string): boolean {
  const sections = partitionCommentarySections(
    stripPresentationMarkersFromMarkdown(commentary),
  );

  return Boolean(sections.destaques?.trim());
}

function markdownHasAttention(commentary: string): boolean {
  const sections = partitionCommentarySections(
    stripPresentationMarkersFromMarkdown(commentary),
  );

  return Boolean(sections.pontos?.trim());
}

function buildTailVisualSegments(
  metadata: Record<string, unknown>,
  plan: StackPresentationPlan,
  visualKinds: Set<string>,
): NonNullable<PresentationRenderPlan["segments"]> {
  const segments: NonNullable<PresentationRenderPlan["segments"]> = [];

  for (const token of plan.tailVisualOrder) {
    const normalized = String(token).trim().toLowerCase();
    const source = VISUAL_TOKEN_TO_KEY[normalized];

    if (!source || !hasVisualPresentation(metadata, normalized, visualKinds)) {
      continue;
    }

    segments.push({
      kind: normalized,
      slot: "tailVisuals",
      source,
    });
  }

  return segments;
}

function buildStackRenderPlanSegments(
  metadata: Record<string, unknown>,
  plan: StackPresentationPlan,
  commentary: string,
  hints: SynthesizeRenderPlanHints,
): NonNullable<PresentationRenderPlan["segments"]> {
  const segments: NonNullable<PresentationRenderPlan["segments"]> = [];

  if (shouldIncludeDecision(metadata, plan)) {
    segments.push({ kind: "decision", slot: "lead", source: "dataAnswer" });
  }

  for (const slot of plan.narrativeOrder) {
    const token = String(slot).trim();

    if (token === "lead" && hasTextPresentation(metadata, commentary)) {
      segments.push({ kind: "markdown", slot: "lead", source: "textPresentation" });
      continue;
    }

    if (token === "highlights" && markdownHasHighlights(commentary)) {
      segments.push({ kind: "markdown", slot: "highlights", source: "textPresentation" });
      continue;
    }

    if (token === "attention" && markdownHasAttention(commentary)) {
      segments.push({ kind: "markdown", slot: "attention", source: "textPresentation" });
      continue;
    }

    if (token === "profileTables" && hasTableBundle(metadata, hints.hasTableVisuals)) {
      segments.push({
        kind: "table",
        slot: "profileTables",
        source: "tablePresentations",
      });
      continue;
    }

    if (token === "operationalTables" && hasTableBundle(metadata, hints.hasTableVisuals)) {
      segments.push({
        kind: "table",
        slot: "operationalTables",
        source: "tablePresentations",
      });
      continue;
    }

    if (token === "tailVisuals") {
      segments.push(...buildTailVisualSegments(metadata, plan, hints.visualKinds));
    }
  }

  return segments;
}

function resolveVisualSource(metadata: Record<string, unknown>, token: string): string | null {
  const normalized = String(token || "").trim().toLowerCase();
  const source = VISUAL_TOKEN_TO_KEY[normalized];

  if (source && metadata[source]) {
    return source;
  }

  if (normalized === "table") {
    const bulk = metadata.tablePresentations;

    if (Array.isArray(bulk) && bulk.length) {
      return "tablePresentations";
    }
  }

  const generic = metadata.presentation;

  if (
    generic &&
    typeof generic === "object" &&
    String((generic as Record<string, unknown>).type || "").trim().toLowerCase() === normalized
  ) {
    return "presentation";
  }

  return null;
}

function resolveExplicitSessionVisual(metadata: Record<string, unknown>): string | null {
  const explicit = String(metadata.explicitSessionFormat || "").trim().toLowerCase();

  if (!explicit || explicit === "text" || explicit === "topics") {
    return null;
  }

  return explicit;
}

function buildSingleViewRenderPlanSegments(
  metadata: Record<string, unknown>,
  plan: StackPresentationPlan,
  commentary: string,
): NonNullable<PresentationRenderPlan["segments"]> {
  const segments: NonNullable<PresentationRenderPlan["segments"]> = [];
  const decision = metadata.presentationDecision as Record<string, unknown> | undefined;
  const selected = String(decision?.selected || "").trim().toLowerCase();
  const explicitVisual = resolveExplicitSessionVisual(metadata);
  const visualToken =
    explicitVisual || (selected && selected !== "text" ? selected : null);

  if (shouldIncludeDecision(metadata, plan)) {
    segments.push({ kind: "decision", slot: "lead", source: "dataAnswer" });
  }

  if (hasTextPresentation(metadata, commentary) && (!selected || selected === "text") && !explicitVisual) {
    segments.push({ kind: "markdown", slot: "lead", source: "textPresentation" });
  }

  const visualSource = visualToken ? resolveVisualSource(metadata, visualToken) : null;

  if (visualToken && visualSource) {
    if (visualToken === "table") {
      const bulk = metadata.tablePresentations;
      const tableCount = Array.isArray(bulk)
        ? bulk.filter(
            (item) =>
              item &&
              typeof item === "object" &&
              (item as Record<string, unknown>).type === "table",
          ).length
        : 0;

      if (tableCount >= 2) {
        segments.push({
          kind: "table",
          slot: "operationalTables",
          source: "tablePresentations",
        });
      } else {
        segments.push({ kind: visualToken, slot: "primary", source: visualSource });
      }
    } else {
      segments.push({ kind: visualToken, slot: "primary", source: visualSource });
    }
  }

  if (!segments.length) {
    return segments;
  }

  return segments;
}

/** P6 legacy — sintetiza renderPlan mecânico a partir do stackPlan quando a API não enviou v1. */
export function synthesizeRenderPlanFromToolCalls(
  toolCalls: ChatToolCall[],
  commentary = "",
  hints?: Partial<SynthesizeRenderPlanHints>,
): PresentationRenderPlan | null {
  const metadata = getExternalActionMetadata(toolCalls);

  if (!metadata) {
    return null;
  }

  const plan = getStackPresentationPlanFromToolCalls(toolCalls);
  const decision = metadata.presentationDecision as Record<string, unknown> | undefined;
  const layoutMode = String(decision?.layoutMode || "stack").trim() || "stack";
  const resolvedHints: SynthesizeRenderPlanHints = {
    hasTableVisuals: hints?.hasTableVisuals ?? false,
    visualKinds: hints?.visualKinds ?? new Set<string>(),
  };

  const segments =
    layoutMode === "stack"
      ? buildStackRenderPlanSegments(metadata, plan, commentary, resolvedHints)
      : buildSingleViewRenderPlanSegments(metadata, plan, commentary);

  if (!segments.length && hasTextPresentation(metadata, commentary)) {
    segments.push({ kind: "markdown", slot: "lead", source: "textPresentation" });
  }

  if (!segments.length) {
    return null;
  }

  return {
    version: 1,
    layoutMode,
    segments,
  };
}

export function resolveRenderPlanForExecution(
  toolCalls: ChatToolCall[],
  commentary = "",
  hints?: Partial<SynthesizeRenderPlanHints>,
): PresentationRenderPlan | null {
  const existing = getRenderPlanFromToolCalls(toolCalls);

  if (isRenderablePlan(existing)) {
    return existing;
  }

  return synthesizeRenderPlanFromToolCalls(toolCalls, commentary, hints);
}

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
  _toolCalls: ChatToolCall[],
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

    if (
      unique.some(
        (item) =>
          (item.length >= 24 &&
            key.length >= 24 &&
            (item.includes(key) || key.includes(item))) ||
          (item.includes("visão integrada") && key.includes("visão integrada")),
      )
    ) {
      continue;
    }

    unique.push(paragraph);
  }

  return unique.join("\n\n");
}

function shouldSkipScopeSectionFraming(leadProse: string, framing: string): boolean {
  const lead = String(leadProse || "").trim().toLowerCase();
  const scope = String(framing || "").trim().toLowerCase();

  if (!lead || !scope) {
    return false;
  }

  if (lead.includes(scope) || scope.includes(lead.slice(0, Math.min(lead.length, 96)))) {
    return true;
  }

  return lead.includes("visão integrada") && scope.includes("visão integrada");
}

function operationalTableRoles(plan: StackPresentationPlan): StackTableRole[] {
  if (!plan.tableRoleOrder.length) {
    return [];
  }

  return plan.tableRoleOrder.filter((role) => role !== "profile");
}

function orderTableVisualSegments(
  tables: AssistantContentSegment[],
  roles: StackTableRole[],
  toolCalls: ChatToolCall[],
): AssistantContentSegment[] {
  if (!tables.length) {
    return [];
  }

  if (!roles.length) {
    return tables;
  }

  const buckets = bucketTableSegmentsByRole(
    tables,
    resolveTableRole,
    metadataStructureDedupApplied(toolCalls),
  );
  const ordered: AssistantContentSegment[] = [];

  for (const role of roles) {
    ordered.push(...(buckets[role] ?? []));
  }

  for (const table of tables) {
    if (!ordered.includes(table)) {
      ordered.push(table);
    }
  }

  return ordered;
}

function resolveTableSegmentsForRenderSpec(
  spec: { source?: string; slot?: string },
  tables: AssistantContentSegment[],
  plan: StackPresentationPlan,
  toolCalls: ChatToolCall[],
): AssistantContentSegment[] {
  if (!tables.length) {
    return [];
  }

  const source = String(spec.source || "").trim();
  const slot = String(spec.slot || "").trim();
  const multiTable =
    source === "tablePresentations" ||
    slot === "operationalTables" ||
    slot === "profileTables";

  if (!multiTable) {
    return [tables[0]];
  }

  const roles =
    slot === "profileTables"
      ? plan.profileFirst
        ? (["profile"] as StackTableRole[])
        : (["profile"] as StackTableRole[])
      : operationalTableRoles(plan);

  return orderTableVisualSegments(tables, roles, toolCalls);
}

/** Resolve visuais de um segmento do renderPlan (modo single / native view). */
export function resolveVisualSegmentsForRenderSpec(
  spec: { kind?: string; source?: string; slot?: string },
  visuals: AssistantContentSegment[],
  toolCalls: ChatToolCall[],
): AssistantContentSegment[] {
  const kind = String(spec.kind || "").trim().toLowerCase();

  if (kind === "decision" || kind === "markdown") {
    return [];
  }

  if (kind === "table") {
    const plan = getStackPresentationPlanFromToolCalls(toolCalls);
    const tables = visuals.filter((visual) => visual.kind === "table");

    return resolveTableSegmentsForRenderSpec(spec, tables, plan, toolCalls);
  }

  const match = visuals.find((visual) => visual.kind === kind);

  return match ? [match] : [];
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
  const scopeFraming = String(plan.sectionFraming?.scope || "").trim();

  if (!shouldSkipScopeSectionFraming(leadProse, scopeFraming)) {
    pushSectionFraming(plan, segments, "scope", parseMarkdown, appendUnique);
  }

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
  const visualKinds = new Set(
    orderedVisuals
      .map((segment) => String(segment.kind || "").trim().toLowerCase())
      .filter(Boolean),
  );
  const renderPlan = resolveRenderPlanForExecution(toolCalls, commentary, {
    hasTableVisuals: orderedVisuals.some((segment) => segment.kind === "table"),
    visualKinds,
  });

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
      } else if (slot === "primary") {
        for (const table of resolveTableSegmentsForRenderSpec(spec, tables, plan, toolCalls)) {
          appendUnique(segments, table);
        }
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
