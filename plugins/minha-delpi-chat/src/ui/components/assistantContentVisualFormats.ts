import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  type AssistantVisualKind,
  type ContentFormatKind,
  resolveStackLayoutOrderFromToolCalls,
  segmentVisualKind,
} from "./assistantContentLayout";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { isStackSectionVisible } from "./presentationStackSections";
import { isHierarchyDuplicateTable } from "./presentationStructureDedup";
import {
  getPresentationDecisionFromToolCalls,
  getPreferredFormatFromToolCalls,
  mapPresentationDecisionToViewFormat,
  type ViewFormat,
} from "./chatPresentation";

export type VisualFormatOption = {
  kind: ContentFormatKind;
  label: string;
};

const FORMAT_LABELS: Record<ContentFormatKind, string> = {
  text: "Texto",
  table: "Tabela",
  tree: "Árvore",
  chart: "Gráfico",
  kpi: "KPI",
  dashboard: "Painel",
};

const CHART_VIEW_TOKENS = new Set([
  "chart",
  "line_chart",
  "bar_chart",
  "horizontal_bar",
  "donut",
]);

function mapViewTokenToVisualKind(view: string): AssistantVisualKind | null {
  const token = view.trim().toLowerCase();

  if (token === "table") {
    return "table";
  }

  if (token === "tree") {
    return "tree";
  }

  if (CHART_VIEW_TOKENS.has(token) || token.includes("chart")) {
    return "chart";
  }

  if (token === "kpi") {
    return "kpi";
  }

  if (token === "dashboard") {
    return "dashboard";
  }

  return null;
}

function mapViewTokenToContentKind(view: string): ContentFormatKind | null {
  const token = view.trim().toLowerCase();

  if (token === "text") {
    return "text";
  }

  return mapViewTokenToVisualKind(view);
}

function hasTextFormatContent(segments: AssistantContentSegment[]): boolean {
  return segments.some(
    (segment) => segment.kind === "markdown" || segment.kind === "code",
  );
}

function hasFormatContent(
  segments: AssistantContentSegment[],
  kind: ContentFormatKind,
): boolean {
  if (kind === "text") {
    return hasTextFormatContent(segments);
  }

  return collectPresentVisualKinds(segments).has(kind);
}

export function collectPresentVisualKinds(
  segments: AssistantContentSegment[],
): Set<AssistantVisualKind> {
  const kinds = new Set<AssistantVisualKind>();

  for (const segment of segments) {
    const kind = segmentVisualKind(segment);

    if (
      segment.kind === "table" &&
      isHierarchyDuplicateTable(segment.presentation)
    ) {
      continue;
    }

    if (kind) {
      kinds.add(kind);
    }
  }

  return kinds;
}

export function resolveAvailableVisualFormatOptions(
  segments: AssistantContentSegment[],
  toolCalls: ChatToolCall[] = [],
): VisualFormatOption[] {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const order = resolveStackLayoutOrderFromToolCalls(toolCalls);
  const candidates = new Set<ContentFormatKind>();

  for (const slot of order) {
    if (hasFormatContent(segments, slot)) {
      candidates.add(slot);
    }
  }

  if (decision?.availableViews) {
    for (const view of decision.availableViews) {
      const mapped = mapViewTokenToContentKind(String(view));

      if (mapped && hasFormatContent(segments, mapped)) {
        candidates.add(mapped);
      }
    }
  }

  const orderedKinds: ContentFormatKind[] = [];

  for (const slot of order) {
    if (candidates.has(slot) && !orderedKinds.includes(slot)) {
      orderedKinds.push(slot);
    }
  }

  for (const kind of candidates) {
    if (!orderedKinds.includes(kind)) {
      orderedKinds.push(kind);
    }
  }

  return orderedKinds.map((kind) => ({
    kind,
    label: FORMAT_LABELS[kind],
  }));
}

function mapViewFormatToContentKind(format: ViewFormat | null): ContentFormatKind | null {
  if (!format) {
    return null;
  }

  if (format === "text") {
    return "text";
  }

  return format;
}

function isTableFirstRouteToolCalls(toolCalls: ChatToolCall[]): boolean {
  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const path = String((toolCall.metadata as Record<string, unknown> | undefined)?.path ?? "")
      .trim()
      .toLowerCase();

    if (
      path.includes("/guide") ||
      path.includes("/inspection") ||
      path.includes("/suppliers") ||
      path.includes("/customers") ||
      path.includes("/stock")
    ) {
      return true;
    }
  }

  return false;
}

function isStructureHeavyToolCalls(toolCalls: ChatToolCall[]): boolean {
  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const path = String((toolCall.metadata as Record<string, unknown> | undefined)?.path ?? "")
      .trim()
      .toLowerCase();

    if (
      path.includes("/structure") ||
      path.includes("/parents") ||
      path.includes("/analyser")
    ) {
      return true;
    }
  }

  return false;
}

export function resolveDefaultVisualKind(
  toolCalls: ChatToolCall[],
  options: VisualFormatOption[],
): ContentFormatKind | null {
  if (!options.length) {
    return null;
  }

  const available = options.map((item) => item.kind);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const fromDecision = mapPresentationDecisionToViewFormat(decision?.selected);

  if (fromDecision) {
    const mapped = mapViewFormatToContentKind(fromDecision);

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  const preferred = getPreferredFormatFromToolCalls(toolCalls);

  if (preferred) {
    const mapped = mapViewFormatToContentKind(preferred);

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  if (
    available.includes("tree") &&
    available.includes("table") &&
    isStructureHeavyToolCalls(toolCalls)
  ) {
    return "tree";
  }

  if (available.includes("table") && isTableFirstRouteToolCalls(toolCalls)) {
    const preferred = getPreferredFormatFromToolCalls(toolCalls);

    if (preferred === "chart" && available.includes("chart")) {
      return "chart";
    }

    return "table";
  }

  return available[0] ?? null;
}

export function filterSegmentsByVisualKind(
  segments: AssistantContentSegment[],
  activeKind: ContentFormatKind | null,
): AssistantContentSegment[] {
  if (!activeKind) {
    return segments;
  }

  return segments.filter((segment) => {
    if (segment.kind === "stackSection") {
      return isStackSectionVisible(segment.section, activeKind);
    }

    if (segment.kind === "markdown" || segment.kind === "code") {
      return activeKind === "text";
    }

    if (segment.kind === "table" && isHierarchyDuplicateTable(segment.presentation)) {
      return activeKind === "table";
    }

    const kind = segmentVisualKind(segment);

    return kind === activeKind;
  });
}

export function shouldShowCompleteStackView(toolCalls: ChatToolCall[]): boolean {
  return getPresentationDecisionFromToolCalls(toolCalls)?.layoutMode === "stack";
}

export function resolveInitialToolbarKind(
  toolCalls: ChatToolCall[],
  options: VisualFormatOption[],
): ContentFormatKind | null {
  if (options.length < 2) {
    return resolveDefaultVisualKind(toolCalls, options);
  }

  if (shouldShowCompleteStackView(toolCalls)) {
    return null;
  }

  return resolveDefaultVisualKind(toolCalls, options);
}
