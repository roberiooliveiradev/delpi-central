import { useMemo } from "react";
import { LayoutPanelLeft } from "lucide-react";
import type { ChatCanvasOpenPayload, ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";
import { presentationToCanvasPayload } from "./chartCanvasMarkdown";
import { downloadDashboardCsv } from "./dashboardExportCsv";
import {
  getChartPresentationFromPair,
  getPresentationPairFromToolCalls,
} from "./chatPresentation";
import { ChatDashboardDataPanel } from "./ChatDashboardDataPanel";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import "./ChatRichDashboard.css";

type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;
type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

function renderAuxChartPanel(
  presentation: ChartPresentation,
  onDrillDown?: (query: string) => void,
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void,
) {
  return (
    <ChatRichChart
      presentation={presentation}
      hideTitle
      onDrillDown={onDrillDown}
      onOpenCanvas={onOpenCanvas}
    />
  );
}

export function ChatRichDashboard({
  presentation,
  toolCalls,
  onDrillDown,
  onOpenCanvas,
}: {
  presentation: DashboardPresentation;
  toolCalls?: ChatToolCall[];
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
}) {
  const { title, panels } = presentation;

  const { kpiPanels, chartPanels, tablePanels } = useMemo(() => {
    const kpis: DashboardPresentation["panels"] = [];
    const charts: DashboardPresentation["panels"] = [];
    const tables: DashboardPresentation["panels"] = [];

    for (const panel of panels) {
      switch (panel.presentation.type) {
        case "kpi":
          kpis.push(panel);
          break;
        case "chart":
          charts.push(panel);
          break;
        case "table":
          tables.push(panel);
          break;
        default:
          break;
      }
    }

    return { kpiPanels: kpis, chartPanels: charts, tablePanels: tables };
  }, [panels]);

  const fallbackItemsChart = useMemo(() => {
    const pair = getPresentationPairFromToolCalls(toolCalls);

    return getChartPresentationFromPair(pair, toolCalls);
  }, [toolCalls]);

  return (
    <div className="mdc-rich-dashboard">
      <div className="mdc-rich-dashboard__header">
        {title ? <div className="mdc-rich-dashboard__title">{title}</div> : <span />}
        <div className="mdc-rich-dashboard__actions">
          <button
            type="button"
            className="mdc-rich-chart__btn"
            onClick={() => downloadDashboardCsv(presentation)}
            title="Baixar dashboard em CSV"
          >
            ↓ CSV
          </button>
          {onOpenCanvas ? (
            <button
              type="button"
              className="mdc-rich-chart__btn"
              onClick={() => onOpenCanvas(presentationToCanvasPayload(presentation))}
              title="Salvar dashboard na lousa"
            >
              <LayoutPanelLeft size={14} aria-hidden="true" />
              Lousa
            </button>
          ) : null}
        </div>
      </div>

      <div className="mdc-rich-dashboard__stack">
        {kpiPanels.length > 0 ? (
          <div className="mdc-rich-dashboard__kpis">
            {kpiPanels.map((panel) =>
              panel.presentation.type === "kpi" ? (
                <section key={panel.id} className="mdc-rich-dashboard__panel">
                  {panel.title ? (
                    <h4 className="mdc-rich-dashboard__panel-title">{panel.title}</h4>
                  ) : null}
                  <div className="mdc-rich-dashboard__panel-body">
                    <ChatRichKpi presentation={panel.presentation} />
                  </div>
                </section>
              ) : null,
            )}
          </div>
        ) : null}

        {chartPanels.length > 0 ? (
          <div className="mdc-rich-dashboard__charts">
            {chartPanels.map((panel) =>
              panel.presentation.type === "chart" ? (
                <section key={panel.id} className="mdc-rich-dashboard__panel">
                  {panel.title ? (
                    <h4 className="mdc-rich-dashboard__panel-title">{panel.title}</h4>
                  ) : null}
                  <div className="mdc-rich-dashboard__panel-body">
                    {renderAuxChartPanel(panel.presentation, onDrillDown, onOpenCanvas)}
                  </div>
                </section>
              ) : null,
            )}
          </div>
        ) : null}

        {tablePanels.map((panel) => {
          if (panel.presentation.type !== "table") {
            return null;
          }

          const chart =
            panel.chartPresentation ??
            fallbackItemsChart ??
            null;

          return (
            <ChatDashboardDataPanel
              key={panel.id}
              title={panel.title}
              table={panel.presentation}
              chart={chart}
              onDrillDown={onDrillDown}
              onOpenCanvas={onOpenCanvas}
            />
          );
        })}
      </div>
    </div>
  );
}
