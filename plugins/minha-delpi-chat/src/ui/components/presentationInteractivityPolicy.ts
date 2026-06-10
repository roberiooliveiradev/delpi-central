import type { ChatPresentationDecision, ChatToolCall } from "../../data/api/chatTypes";
import presentationVocabulary from "../../content/presentation_vocabulary.json";

import {
  getPresentationDecisionFromToolCalls,
  mapPresentationDecisionToViewFormat,
} from "./chatPresentation";

type PostResponseChipVocabulary = {
  viewLabels: Record<string, string>;
  viewQueries: Record<string, string>;
};

const CHART_VIEW_TOKENS = new Set([
  "chart",
  "line_chart",
  "area_chart",
  "bar_chart",
  "horizontal_bar",
  "donut",
  "scatter",
]);

const postResponseChips = presentationVocabulary.postResponseChips as PostResponseChipVocabulary;

export type FormatSwitchAction = {
  id: string;
  label: string;
  query: string;
};

function normalizedViews(decision: ChatPresentationDecision): string[] {
  return (decision.availableViews ?? [])
    .map((view) => String(view).trim().toLowerCase())
    .filter(Boolean);
}

function isChartView(view: string): boolean {
  const token = view.trim().toLowerCase();

  return CHART_VIEW_TOKENS.has(token) || token.includes("chart");
}

function chartViewsAvailable(available: string[], selected: string): boolean {
  if (isChartView(selected)) {
    return false;
  }

  return available.some((view) => isChartView(view));
}

function labelForView(view: string): string | null {
  const token = view.trim().toLowerCase();
  const label = postResponseChips.viewLabels[token];

  return label ? String(label) : null;
}

function queryForView(view: string): string {
  const token = view.trim().toLowerCase();

  return String(
    postResponseChips.viewQueries[token] ??
      postResponseChips.viewQueries.chart ??
      `mostre o último resultado em ${token}`,
  );
}

function viewOrder(decision: ChatPresentationDecision): string[] {
  const ordered = (decision.visualOrder ?? decision.availableViews ?? [])
    .map((view) => String(view).trim().toLowerCase())
    .filter(Boolean);

  return [...new Set(ordered)];
}

export function buildFormatSwitchActionsFromDecision(
  decision: ChatPresentationDecision | null | undefined,
): FormatSwitchAction[] {
  if (!decision) {
    return [];
  }

  const selected = mapPresentationDecisionToViewFormat(decision.selected)?.trim().toLowerCase() ?? "";
  const available = normalizedViews(decision);
  const actions: FormatSwitchAction[] = [];
  const seen = new Set<string>();

  for (const view of viewOrder(decision)) {
    if (!available.includes(view) || view === selected) {
      continue;
    }

    if (isChartView(view) && isChartView(selected)) {
      continue;
    }

    if (isChartView(view) && !chartViewsAvailable(available, selected)) {
      continue;
    }

    const label = labelForView(view);

    if (!label || seen.has(label)) {
      continue;
    }

    seen.add(label);
    actions.push({
      id: `format-${view}`,
      label,
      query: queryForView(view),
    });
  }

  const canvasLabel = postResponseChips.viewLabels.canvas;

  if (canvasLabel && available.length >= 1 && !seen.has(canvasLabel)) {
    actions.push({
      id: "format-canvas",
      label: canvasLabel,
      query: queryForView("canvas"),
    });
  }

  return actions;
}

export function buildFormatSwitchActionsFromToolCalls(
  toolCalls: ChatToolCall[],
): FormatSwitchAction[] {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);

  return buildFormatSwitchActionsFromDecision(decision);
}
