import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  type AssistantVisualKind,
  resolveVisualOrderFromToolCalls,
  segmentVisualKind,
} from "./assistantContentLayout";
import type { AssistantContentSegment } from "./assistantContentTypes";
import {
  getPresentationDecisionFromToolCalls,
  getPreferredFormatFromToolCalls,
  mapPresentationDecisionToViewFormat,
  type ViewFormat,
} from "./chatPresentation";

export type VisualFormatOption = {
  kind: AssistantVisualKind;
  label: string;
};

const VISUAL_LABELS: Record<AssistantVisualKind, string> = {
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

export function collectPresentVisualKinds(
  segments: AssistantContentSegment[],
): Set<AssistantVisualKind> {
  const kinds = new Set<AssistantVisualKind>();

  for (const segment of segments) {
    const kind = segmentVisualKind(segment);

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
  const present = collectPresentVisualKinds(segments);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const order = resolveVisualOrderFromToolCalls(toolCalls);
  const orderedKinds: AssistantVisualKind[] = [];

  for (const kind of order) {
    if (present.has(kind) && !orderedKinds.includes(kind)) {
      orderedKinds.push(kind);
    }
  }

  for (const kind of present) {
    if (!orderedKinds.includes(kind)) {
      orderedKinds.push(kind);
    }
  }

  if (decision?.availableViews) {
    for (const view of decision.availableViews) {
      const mapped = mapViewTokenToVisualKind(String(view));

      if (mapped && present.has(mapped) && !orderedKinds.includes(mapped)) {
        orderedKinds.push(mapped);
      }
    }
  }

  return orderedKinds.map((kind) => ({
    kind,
    label: VISUAL_LABELS[kind],
  }));
}

function mapViewFormatToVisualKind(format: ViewFormat | null): AssistantVisualKind | null {
  if (!format || format === "text") {
    return null;
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
): AssistantVisualKind | null {
  if (!options.length) {
    return null;
  }

  const available = options.map((item) => item.kind);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const fromDecision = mapPresentationDecisionToViewFormat(decision?.selected);

  if (fromDecision) {
    const mapped = mapViewFormatToVisualKind(fromDecision);

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  const preferred = getPreferredFormatFromToolCalls(toolCalls);

  if (preferred) {
    const mapped = mapViewFormatToVisualKind(preferred);

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
  activeKind: AssistantVisualKind | null,
): AssistantContentSegment[] {
  if (!activeKind) {
    return segments;
  }

  return segments.filter((segment) => {
    const kind = segmentVisualKind(segment);

    return !kind || kind === activeKind;
  });
}
