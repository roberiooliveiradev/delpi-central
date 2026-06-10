import type { ChatToolCall } from "../../data/api/chatTypes";

import {
  getPresentationDecisionFromToolCalls,
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

export type StackLayoutSlot = "text" | AssistantVisualKind;

/** Formato selecionável na toolbar (narrativa + visuais nativos). */
export type ContentFormatKind = StackLayoutSlot;

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

function mapDecisionViewToStackSlot(view: string): StackLayoutSlot | null {
  const token = view.trim().toLowerCase();

  if (token === "text") {
    return "text";
  }

  return mapDecisionViewToVisualKind(view);
}

const CHART_SELECTED_TOKENS = new Set([
  "chart",
  "line_chart",
  "bar_chart",
  "horizontal_bar",
  "donut",
  "area_chart",
  "grouped_bar",
  "stacked_bar",
  "combo_chart",
  "histogram",
  "heatmap",
  "gauge",
  "scatter",
]);

const NATIVE_SINGLE_VIEW_KINDS = new Set<ContentFormatKind>([
  "table",
  "tree",
  "chart",
  "kpi",
  "dashboard",
]);

export function mapSelectedViewToContentFormatKind(
  selected: string | null | undefined,
): ContentFormatKind | null {
  const token = String(selected ?? "").trim().toLowerCase();

  if (!token || token === "text") {
    return null;
  }

  if (token === "canvas") {
    return null;
  }

  if (CHART_SELECTED_TOKENS.has(token) || token.includes("chart")) {
    return "chart";
  }

  if (NATIVE_SINGLE_VIEW_KINDS.has(token as ContentFormatKind)) {
    return token as ContentFormatKind;
  }

  return null;
}

function explicitNativeFormatFromToolCalls(
  toolCalls: ChatToolCall[] = [],
): ContentFormatKind | null {
  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    const metadata = toolCall.metadata as Record<string, unknown> | undefined;

    if (!metadata) {
      continue;
    }

    for (const key of ["explicitSessionFormat", "preferredFormat"] as const) {
      const kind = mapSelectedViewToContentFormatKind(String(metadata[key] ?? ""));

      if (kind) {
        return kind;
      }
    }
  }

  return null;
}

/** Visão nativa explícita em layout single (ex.: preferência Tabela na UI). */
export function isNativeSingleViewSelection(toolCalls: ChatToolCall[] = []): {
  active: boolean;
  kind: ContentFormatKind | null;
} {
  const explicitKind = explicitNativeFormatFromToolCalls(toolCalls);

  if (explicitKind) {
    return { active: true, kind: explicitKind };
  }

  const decision = getPresentationDecisionFromToolCalls(toolCalls);

  if (decision?.layoutMode === "stack") {
    return { active: false, kind: null };
  }

  const selectedKind = mapSelectedViewToContentFormatKind(decision?.selected);

  if (selectedKind) {
    return { active: true, kind: selectedKind };
  }

  return { active: false, kind: null };
}

export function resolveStackLayoutOrderFromToolCalls(
  toolCalls?: ChatToolCall[],
): StackLayoutSlot[] {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const rawOrder = decision?.visualOrder;

  if (!Array.isArray(rawOrder) || !rawOrder.length) {
    return ["text", ...DEFAULT_VISUAL_ORDER];
  }

  const mapped = rawOrder
    .map((view) => mapDecisionViewToStackSlot(String(view)))
    .filter((slot): slot is StackLayoutSlot => Boolean(slot));

  if (!mapped.length) {
    return ["text", ...DEFAULT_VISUAL_ORDER];
  }

  const unique = [...new Set(mapped)];

  if (!unique.includes("text")) {
    unique.unshift("text");
  }

  return unique;
}

export function resolveVisualOrderFromToolCalls(
  toolCalls?: ChatToolCall[],
): AssistantVisualKind[] {
  return resolveStackLayoutOrderFromToolCalls(toolCalls).filter(
    (slot): slot is AssistantVisualKind => slot !== "text",
  );
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

/** Empilha narrativa + todos os visuais nativos (sem alternar um por vez). */
export function shouldShowAllVisualSegments(toolCalls: ChatToolCall[] = []): boolean {
  return resolveAssistantContentLayout("", toolCalls) === "stack";
}

export function resolveAssistantContentLayout(
  content: string,
  toolCalls: ChatToolCall[] = [],
  _pair?: PresentationPair,
): AssistantContentLayoutMode {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const hasMarkers = /\[\[(?:tabela|table|grafico|chart|arvore|tree|kpi|dashboard)/i.test(
    content,
  );

  if (decision?.layoutMode === "stack") {
    return "stack";
  }

  if (hasMarkers) {
    return "markers";
  }

  return "text-only";
}
