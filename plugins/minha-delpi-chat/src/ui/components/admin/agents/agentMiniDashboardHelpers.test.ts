import { describe, expect, it } from "vitest";

import {
  agentDashboardKpisFromPresentation,
  agentUsageKpisFromStats,
  dashboardWithoutKpiPanels,
} from "./agentMiniDashboardHelpers";

describe("agentMiniDashboardHelpers", () => {
  it("monta KPIs de uso a partir das estatísticas", () => {
    const items = agentUsageKpisFromStats({
      agentId: "a1",
      windowHours: 168,
      sessionsInWindow: 12,
      messagesInWindow: 48,
      totalSessions: 200,
      actionProvidersCount: 3,
      sharesCount: 1,
    });

    expect(items).toHaveLength(5);
    expect(items[0]?.title).toBe("Sessões na janela");
    expect(items[0]?.value).toBe("12");
  });

  it("extrai cards KPI do mini dashboard", () => {
    const items = agentDashboardKpisFromPresentation({
      type: "dashboard",
      title: "Uso",
      panels: [
        {
          id: "kpi-1",
          title: "Volume",
          presentation: {
            type: "kpi",
            title: "Volume",
            cards: [{ label: "Turnos", value: 9 }],
          },
        },
      ],
    });

    expect(items).toHaveLength(1);
    expect(items[0]?.title).toBe("Volume · Turnos");
    expect(items[0]?.value).toBe("9");
  });

  it("remove painéis KPI para renderizar só gráficos", () => {
    const filtered = dashboardWithoutKpiPanels({
      type: "dashboard",
      title: "Painel",
      panels: [
        {
          id: "kpi",
          presentation: { type: "kpi", title: "KPI", cards: [{ label: "A", value: 1 }] },
        },
        {
          id: "chart",
          presentation: {
            type: "chart",
            title: "Série",
            chartType: "bar",
            labels: ["a"],
            datasets: [{ label: "x", data: [1] }],
          },
        },
      ],
    });

    expect(filtered?.panels).toHaveLength(1);
    expect(filtered?.panels[0]?.presentation.type).toBe("chart");
  });
});
