import type { ChatAgentStats, ChatPresentation } from "../../../../data/api/chatTypes";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;
type KpiPresentation = Extract<ChatPresentation, { type: "kpi" }>;

export type AgentAdminKpiItem = {
  key: string;
  title: string;
  value: string;
  hint?: string;
};

export function agentUsageKpisFromStats(stats: ChatAgentStats): AgentAdminKpiItem[] {
  const hours = stats.windowHours;

  return [
    {
      key: "sessions-window",
      title: "Sessões na janela",
      value: formatMetricNumber(stats.sessionsInWindow),
      hint: `Últimas ${hours}h.`,
    },
    {
      key: "messages-window",
      title: "Mensagens na janela",
      value: formatMetricNumber(stats.messagesInWindow),
      hint: `Últimas ${hours}h.`,
    },
    {
      key: "sessions-total",
      title: "Sessões (total)",
      value: formatMetricNumber(stats.totalSessions),
    },
    {
      key: "actions",
      title: "Providers de action",
      value: formatMetricNumber(stats.actionProvidersCount),
    },
    {
      key: "shares",
      title: "Compartilhamentos",
      value: formatMetricNumber(stats.sharesCount),
    },
  ];
}

export function agentDashboardKpisFromPresentation(
  presentation: DashboardPresentation | undefined,
): AgentAdminKpiItem[] {
  if (!presentation?.panels?.length) {
    return [];
  }

  const items: AgentAdminKpiItem[] = [];

  for (const panel of presentation.panels) {
    if (panel.presentation.type !== "kpi") {
      continue;
    }

    const kpi = panel.presentation as KpiPresentation;
    const panelTitle = panel.title?.trim() || kpi.title?.trim();

    for (const [index, card] of kpi.cards.entries()) {
      const label = String(card.label || "").trim() || "Indicador";
      const title = panelTitle ? `${panelTitle} · ${label}` : label;
      const value =
        typeof card.value === "number"
          ? formatMetricNumber(card.value)
          : String(card.value ?? "—");
      const unit = card.unit ? ` ${card.unit}` : "";
      const hintParts = [card.delta, card.trend ? `tendência: ${card.trend}` : ""].filter(Boolean);

      items.push({
        key: `${panel.id}-${index}-${label}`,
        title,
        value: `${value}${unit}`.trim(),
        hint: hintParts.length ? hintParts.join(" · ") : undefined,
      });
    }
  }

  return items;
}

export function dashboardWithoutKpiPanels(
  presentation: DashboardPresentation,
): DashboardPresentation | null {
  const panels = presentation.panels.filter((panel) => panel.presentation.type !== "kpi");

  if (panels.length === 0) {
    return null;
  }

  return {
    ...presentation,
    panels,
  };
}
