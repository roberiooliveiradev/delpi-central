import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  getPresentationDecisionFromToolCalls,
  getPresentationPairFromToolCalls,
  resolveCommentaryTextBody,
  type PresentationPair,
} from "./chatPresentation";
import type { AssistantContentSegment } from "./assistantContentTypes";

export type AssistantContentLayoutMode = "stack" | "markers" | "text-only";

export type AssistantVisualKind =
  | "table"
  | "chart"
  | "tree"
  | "kpi"
  | "dashboard";

const DEFAULT_VISUAL_ORDER: AssistantVisualKind[] = [
  "table",
  "tree",
  "chart",
  "kpi",
  "dashboard",
];

const CHART_VIEW_TOKENS = new Set([
  "chart",
  "line_chart",
  "bar_chart",
  "horizontal_bar",
  "donut",
  "grouped_bar",
  "stacked_bar",
  "combo_chart",
  "histogram",
  "heatmap",
  "gauge",
  "scatter",
]);

export function segmentVisualKind(
  segment: AssistantContentSegment,
): AssistantVisualKind | null {
  if (segment.kind === "table") {
    return "table";
  }

  if (segment.kind === "chart") {
    return "chart";
  }

  if (segment.kind === "tree") {
    return "tree";
  }

  if (segment.kind === "kpi") {
    return "kpi";
  }

  if (segment.kind === "dashboard") {
    return "dashboard";
  }

  return null;
}

function mapDecisionViewToVisualKind(view: string): AssistantVisualKind | null {
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

export function resolveVisualOrderFromToolCalls(
  toolCalls?: ChatToolCall[],
): AssistantVisualKind[] {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const rawOrder = decision?.visualOrder;

  if (!Array.isArray(rawOrder) || !rawOrder.length) {
    return [...DEFAULT_VISUAL_ORDER];
  }

  const mapped = rawOrder
    .map((view) => mapDecisionViewToVisualKind(String(view)))
    .filter((kind): kind is AssistantVisualKind => Boolean(kind));

  return mapped.length ? [...new Set(mapped)] : [...DEFAULT_VISUAL_ORDER];
}

export function orderVisualSegments(
  visuals: AssistantContentSegment[],
  visualOrder: AssistantVisualKind[],
): AssistantContentSegment[] {
  const buckets = new Map<AssistantVisualKind, AssistantContentSegment[]>();

  for (const visual of visuals) {
    const kind = segmentVisualKind(visual);

    if (!kind) {
      continue;
    }

    const list = buckets.get(kind) ?? [];
    list.push(visual);
    buckets.set(kind, list);
  }

  const ordered: AssistantContentSegment[] = [];

  for (const kind of visualOrder) {
    ordered.push(...(buckets.get(kind) ?? []));
  }

  for (const visual of visuals) {
    if (!ordered.includes(visual)) {
      ordered.push(visual);
    }
  }

  return ordered;
}

export function countVisualSegments(visuals: AssistantContentSegment[]): number {
  return visuals.filter((segment) => segmentVisualKind(segment) !== null).length;
}

export function resolveAssistantContentLayout(
  content: string,
  toolCalls: ChatToolCall[] = [],
  pair?: PresentationPair,
): AssistantContentLayoutMode {
  const resolvedPair = pair ?? getPresentationPairFromToolCalls(toolCalls);
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const commentary = resolveCommentaryTextBody(content, toolCalls, resolvedPair).trim();
  const hasMarkers = /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)/i.test(
    content,
  );

  if (decision?.layoutMode === "stack") {
    return "stack";
  }

  if (hasMarkers) {
    return "markers";
  }

  const path = String(
    toolCalls.find((call) => call.metadata?.path)?.metadata?.path ?? "",
  ).toLowerCase();

  if (
    path.includes("/analyser") ||
    path.includes("/structure") ||
    path.includes("/parents")
  ) {
    return commentary ? "stack" : "stack";
  }

  if (decision?.availableViews && decision.availableViews.length >= 2) {
    return "stack";
  }

  return commentary ? "text-only" : "text-only";
}
