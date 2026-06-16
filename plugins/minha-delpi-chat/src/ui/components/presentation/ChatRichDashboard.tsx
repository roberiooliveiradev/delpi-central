import { useMemo, useState } from "react";
import { LayoutPanelLeft } from "lucide-react";
import type { ChatCanvasOpenPayload, ChatPresentation, ChatToolCall } from "../../../data/api/chatTypes";
import { presentationToCanvasPayload } from "../chartCanvasMarkdown";
import { ChatPresentationExportButtons } from "../ChatPresentationExportButtons";
import {
  getChartPresentationFromPair,
  getPresentationPairFromToolCalls,
} from "../chatPresentation";
import { ChatDashboardDataPanel } from "../ChatDashboardDataPanel";
import { ChatMarkdown } from "../ChatMarkdown";
import { ChatRichChart } from "./ChatRichChart";
import { ExpandButton } from "../ChatExpandModal";
import { ChatRichKpi } from "./ChatRichKpi";
import { getChartExplanationFromToolCalls } from "../chartExplain";
import "./ChatRichDashboard.css";

type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;
type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

function normalizePanelTitle(value: string | undefined): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

function shouldSuppressNestedKpiTitle(
  panelTitle: string | undefined,
  kpiTitle: string | undefined,
): boolean {
  const panel = normalizePanelTitle(panelTitle);
  const kpi = normalizePanelTitle(kpiTitle);

  return Boolean(panel && kpi && panel === kpi);
}

function renderAuxChartPanel(
  presentation: ChartPresentation,
  onDrillDown?: (query: string) => void,
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void,
) {
  const explanation =
    presentation.chartExplanation?.trim() || undefined;

  return (
    <ChatRichChart
      presentation={presentation}
      hideTitle
      chartExplanation={explanation}
      onDrillDown={onDrillDown}
      onOpenCanvas={onOpenCanvas}
    />
  );
}

export function ChatRichDashboard({
  presentation,
  toolCalls,
  dashboardExplanation,
  showDashboardExplanation = false,
  onShowDashboardExplanationChange,
  onDrillDown,
  onOpenCanvas,
  variant = "default",
}: {
  presentation: DashboardPresentation;
  toolCalls?: ChatToolCall[];
  dashboardExplanation?: string;
  showDashboardExplanation?: boolean;
  onShowDashboardExplanationChange?: (open: boolean) => void;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
  /** `admin` — toolbar legível e ações reduzidas no painel administrativo. */
  variant?: "default" | "admin";
}) {
  const { title, panels: rawPanels } = presentation;
  const panels = Array.isArray(rawPanels) ? rawPanels : [];
  const [localExplainOpen, setLocalExplainOpen] = useState(false);
  const explainOpen = showDashboardExplanation || localExplainOpen;
  const setExplainOpen = onShowDashboardExplanationChange ?? setLocalExplainOpen;
  const resolvedDashboardExplanation =
    dashboardExplanation?.trim() || undefined;

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

  const isAdminVariant = variant === "admin";

  return (
    <div
      className={[
        "mdc-rich-dashboard",
        isAdminVariant ? "mdc-rich-dashboard--admin" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {title || !isAdminVariant ? (
      <div className="mdc-rich-dashboard__header">
        {title ? <div className="mdc-rich-dashboard__title">{title}</div> : <span />}
        <div className="mdc-rich-dashboard__actions">
          {!isAdminVariant && resolvedDashboardExplanation ? (
            <button
              type="button"
              className={`mdc-rich-chart__btn${explainOpen ? " mdc-rich-chart__toggle-btn--active" : ""}`}
              onClick={() => setExplainOpen(!explainOpen)}
              title="Explicar como ler este painel"
              aria-expanded={explainOpen}
            >
              Explicar painel
            </button>
          ) : null}
          {!isAdminVariant ? (
            <ChatPresentationExportButtons
              presentation={presentation}
              buttonClassName="mdc-rich-chart__btn"
            />
          ) : null}
          {!isAdminVariant && onOpenCanvas ? (
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
          {!isAdminVariant ? (
            <ExpandButton presentation={presentation} onOpenCanvas={onOpenCanvas} />
          ) : null}
        </div>
      </div>
      ) : null}

      {explainOpen && resolvedDashboardExplanation ? (
        <div
          className="mdc-rich-chart__explanation mdc-rich-dashboard__explanation"
          role="region"
          aria-label="Explicação do painel"
        >
          <ChatMarkdown content={resolvedDashboardExplanation} />
        </div>
      ) : null}

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
                    <ChatRichKpi
                      presentation={panel.presentation}
                      suppressTitle={shouldSuppressNestedKpiTitle(
                        panel.title,
                        panel.presentation.title,
                      )}
                      hideToolbar
                    />
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

          const itemsChartExplanation =
            chart?.chartExplanation ||
            getChartExplanationFromToolCalls(toolCalls) ||
            undefined;

          return (
            <ChatDashboardDataPanel
              key={panel.id}
              title={panel.title}
              table={panel.presentation}
              chart={
                chart
                  ? {
                      ...chart,
                      chartExplanation:
                        chart.chartExplanation || itemsChartExplanation,
                    }
                  : null
              }
              onDrillDown={onDrillDown}
              onOpenCanvas={onOpenCanvas}
            />
          );
        })}
      </div>
    </div>
  );
}
