import type { ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";
import { formatChartColumnLabel } from "./chartAxisSelection";
import { getPresentationDecisionFromToolCalls } from "./chatPresentation";

export const EXPLAIN_CHART_CHIP_LABEL = "Explique esse gráfico";
export const EXPLAIN_CHART_INLINE_ACTION = "explain_chart";
export const EXPLAIN_DASHBOARD_CHIP_LABEL = "Explique esse painel";
export const EXPLAIN_DASHBOARD_INLINE_ACTION = "explain_dashboard";

const CHART_TYPE_LABELS: Record<string, string> = {
  bar: "gráfico de barras",
  horizontal_bar: "gráfico de barras horizontais",
  line: "gráfico de linhas",
  area: "gráfico de área",
  donut: "gráfico de rosca",
  scatter: "gráfico de dispersão",
  combo: "gráfico combinado",
  histogram: "histograma",
};

type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

export function isExplainChartSuggestion(suggestion: {
  label?: string;
  inlineAction?: string;
}): boolean {
  return (
    suggestion.inlineAction === EXPLAIN_CHART_INLINE_ACTION ||
    String(suggestion.label ?? "").trim() === EXPLAIN_CHART_CHIP_LABEL
  );
}

export function isExplainDashboardSuggestion(suggestion: {
  label?: string;
  inlineAction?: string;
}): boolean {
  return (
    suggestion.inlineAction === EXPLAIN_DASHBOARD_INLINE_ACTION ||
    String(suggestion.label ?? "").trim() === EXPLAIN_DASHBOARD_CHIP_LABEL
  );
}

export function getDashboardExplanationFromToolCalls(toolCalls?: ChatToolCall[]): string {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);

  return String(decision?.dashboardExplanation ?? "").trim();
}

export function messageHasDashboardPresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  return toolCalls.some((toolCall) => {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;
    const presentation = metadata?.presentation;

    return (
      presentation &&
      typeof presentation === "object" &&
      (presentation as { type?: string }).type === "dashboard"
    );
  });
}

export function getChartExplanationFromToolCalls(toolCalls?: ChatToolCall[]): string {
  const decision = getPresentationDecisionFromToolCalls(toolCalls);
  const fromDecision = String(decision?.chartExplanation ?? "").trim();

  if (fromDecision) {
    return fromDecision;
  }

  for (const toolCall of toolCalls ?? []) {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;
    const presentation = metadata?.presentation ?? metadata?.chartPresentation;

    if (presentation && typeof presentation === "object" && (presentation as ChartPresentation).type === "chart") {
      return buildChartExplanationFallback(presentation as ChartPresentation, decision);
    }
  }

  return "";
}

export function messageHasChartPresentation(toolCalls?: ChatToolCall[]): boolean {
  if (!Array.isArray(toolCalls)) {
    return false;
  }

  return toolCalls.some((toolCall) => {
    const metadata = toolCall.metadata as Record<string, unknown> | undefined;
    const presentation = metadata?.presentation ?? metadata?.chartPresentation;

    return (
      presentation &&
      typeof presentation === "object" &&
      (presentation as ChartPresentation).type === "chart"
    );
  });
}

/** Fallback para mensagens antigas sem `chartExplanation` na API. */
export function buildChartExplanationFallback(
  presentation: ChartPresentation,
  decision?: ReturnType<typeof getPresentationDecisionFromToolCalls>,
): string {
  const rows = presentation.data ?? [];

  if (!rows.length) {
    return "Não há dados suficientes para explicar este gráfico.";
  }

  const config = presentation.config ?? {};
  const fieldLabels = config.fieldLabels;
  const chartType = presentation.chartType ?? "bar";
  const chartLabel = CHART_TYPE_LABELS[chartType] ?? "gráfico";
  const xAxis = config.xAxis ?? guessCategoryKey(rows[0]);
  const yAxis = Array.isArray(config.yAxis) ? config.yAxis[0] : config.yAxis ?? guessNumericKey(rows[0]);
  const insight = String(decision?.insight ?? "").trim();
  const reason = String(decision?.reason ?? "").trim();

  const numericValues = rows
    .map((row) => Number(row[yAxis ?? ""]))
    .filter((value) => Number.isFinite(value));

  const leader = [...rows].sort(
    (left, right) => Number(right[yAxis ?? ""]) - Number(left[yAxis ?? ""]),
  )[0];
  const leaderLabel = String(leader?.[xAxis ?? ""] ?? "o destaque");

  const parts = [
    insight,
    reason
      ? `Este ${chartLabel} mostra ${rows.length} registro(s): ${reason}.`
      : `Este ${chartLabel} mostra ${rows.length} registro(s).`,
    `No eixo horizontal está «${formatChartColumnLabel(String(xAxis), fieldLabels)}»; no vertical, «${formatChartColumnLabel(String(yAxis), fieldLabels)}».`,
    numericValues.length
      ? `O maior valor aparece em ${leaderLabel}; a média de «${formatChartColumnLabel(String(yAxis), fieldLabels)}» é ${formatNumber(statisticsMean(numericValues))}.`
      : "",
    "Use os seletores do gráfico para trocar eixos ou filtrar sem enviar nova pergunta.",
  ];

  return parts.filter(Boolean).join("\n\n");
}

function guessCategoryKey(row: Record<string, unknown>): string {
  const entry = Object.entries(row).find(([, value]) => typeof value === "string");

  return entry?.[0] ?? "name";
}

function guessNumericKey(row: Record<string, unknown>): string {
  const entry = Object.entries(row).find(
    ([, value]) => typeof value === "number" && Number.isFinite(value),
  );

  return entry?.[0] ?? "value";
}

function statisticsMean(values: number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function formatNumber(value: number): string {
  if (Math.abs(value - Math.round(value)) < 0.01) {
    return String(Math.round(value));
  }

  return value.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}
