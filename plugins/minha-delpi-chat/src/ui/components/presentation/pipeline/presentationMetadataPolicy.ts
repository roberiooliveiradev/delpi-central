import type { ChatPresentationDecision, ChatToolCall } from "../../../../data/api/chatTypes";

import type { AssistantVisualKind, ContentFormatKind } from "../../message/assistantContentLayout";
import {
  getPresentationDecisionFromToolCalls,
  mapPresentationDecisionToViewFormat,
  type ViewFormat,
} from "../../chatPresentation";

const CHART_VIEW_TOKENS = new Set([
  "chart",
  "line_chart",
  "bar_chart",
  "horizontal_bar",
  "donut",
]);

export function mapViewTokenToVisualKind(view: string): AssistantVisualKind | null {
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

export function mapViewTokenToContentKind(view: string): ContentFormatKind | null {
  const token = view.trim().toLowerCase();

  if (token === "text") {
    return "text";
  }

  return mapViewTokenToVisualKind(view);
}

export function resolveVisualKindsFromDecision(
  decision: ChatPresentationDecision | null | undefined,
): AssistantVisualKind[] | null {
  const rawOrder = decision?.visualOrder;

  if (!Array.isArray(rawOrder) || !rawOrder.length) {
    return null;
  }

  const kinds: AssistantVisualKind[] = [];

  for (const view of rawOrder) {
    const mapped = mapViewTokenToVisualKind(String(view));

    if (mapped && !kinds.includes(mapped)) {
      kinds.push(mapped);
    }
  }

  return kinds.length ? kinds : null;
}

export function resolveInitialContentKindFromDecision(
  decision: ChatPresentationDecision | null | undefined,
  available: ContentFormatKind[],
): ContentFormatKind | null {
  if (!available.length) {
    return null;
  }

  const selected = mapPresentationDecisionToViewFormat(decision?.selected);

  if (selected) {
    const mapped = mapViewFormatToContentKind(selected);

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  if (decision?.dataShape?.hasHierarchy && available.includes("tree")) {
    return "tree";
  }

  if (metadataPrefersTableView(decision, available)) {
    return "table";
  }

  for (const view of decision?.visualOrder ?? []) {
    const mapped = mapViewTokenToContentKind(String(view));

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  for (const view of decision?.availableViews ?? []) {
    const mapped = mapViewTokenToContentKind(String(view));

    if (mapped && available.includes(mapped)) {
      return mapped;
    }
  }

  return available[0] ?? null;
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

function metadataPrefersTableView(
  decision: ChatPresentationDecision | null | undefined,
  available: ContentFormatKind[],
): boolean {
  if (!available.includes("table")) {
    return false;
  }

  if (mapPresentationDecisionToViewFormat(decision?.selected) === "table") {
    return true;
  }

  if (decision?.dataShape?.hasHierarchy) {
    return false;
  }

  const order = decision?.visualOrder ?? [];
  const tableIndex = order.findIndex(
    (view) => mapViewTokenToContentKind(String(view)) === "table",
  );
  const treeIndex = order.findIndex(
    (view) => mapViewTokenToContentKind(String(view)) === "tree",
  );

  if (tableIndex < 0) {
    return false;
  }

  return treeIndex < 0 || tableIndex < treeIndex;
}

export function getPresentationDecisionFromToolCall(
  toolCall?: ChatToolCall,
): ChatPresentationDecision | null {
  if (!toolCall) {
    return null;
  }

  return getPresentationDecisionFromToolCalls([toolCall]);
}
