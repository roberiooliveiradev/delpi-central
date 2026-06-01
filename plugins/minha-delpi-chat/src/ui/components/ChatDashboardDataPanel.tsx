import { useCallback, useMemo, useState } from "react";
import type { ChatCanvasOpenPayload, ChatPresentation } from "../../data/api/chatTypes";
import { buildChartPresentationFromTable } from "./buildChartPresentationFromTable";
import {
  resolveRichFormatToggles,
  tablePresentationToMarkdown,
  type ViewFormat,
} from "./chatPresentation";
import { ChatMarkdown } from "./ChatMarkdown";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichTable } from "./ChatRichTable";
import { recordPresentationTelemetry } from "./presentationTelemetry";

type TablePresentation = Extract<ChatPresentation, { type: "table" }>;
type ChartPresentation = Extract<ChatPresentation, { type: "chart" }>;

function FormatToggle({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`mdc-rich-chart__toggle-btn ${active ? "mdc-rich-chart__toggle-btn--active" : ""}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

export function ChatDashboardDataPanel({
  title,
  table,
  chart,
  onDrillDown,
  onOpenCanvas,
}: {
  title?: string;
  table: TablePresentation;
  chart?: ChartPresentation | null;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
}) {
  const textBody = useMemo(
    () => tablePresentationToMarkdown(table, { includeTitle: false }),
    [table],
  );

  const resolvedChart = useMemo(
    () => chart ?? buildChartPresentationFromTable(table),
    [chart, table],
  );

  const hasText = Boolean(textBody.trim());
  const hasTable = Boolean(table.rows?.length || table.columns?.length);
  const hasChart = Boolean(resolvedChart?.data?.length);

  const formatToggles = resolveRichFormatToggles({
    hasText,
    hasChart,
    hasTable,
    hasTree: false,
    isCommentaryVisual: false,
  });

  const showFormatToggles =
    [formatToggles.showText, formatToggles.showTable, formatToggles.showChart].filter(
      Boolean,
    ).length >= 2;

  const [viewMode, setViewMode] = useState<ViewFormat>("table");

  const switchViewMode = useCallback((mode: ViewFormat) => {
    setViewMode((previous) => {
      if (previous !== mode) {
        recordPresentationTelemetry("presentation_view_switch", {
          from: previous,
          to: mode,
          context: "dashboard_items",
        });
      }

      return mode;
    });
  }, []);

  return (
    <section className="mdc-rich-dashboard__panel mdc-rich-dashboard__panel--data">
      <div className="mdc-rich-dashboard__data-header">
        {title ? <h4 className="mdc-rich-dashboard__panel-title">{title}</h4> : <span />}
        {showFormatToggles ? (
          <div
            className="mdc-rich-dashboard__data-toggle"
            role="group"
            aria-label="Formato dos itens do painel"
          >
            {formatToggles.showText ? (
              <FormatToggle
                active={viewMode === "text"}
                label="Texto"
                onClick={() => switchViewMode("text")}
              />
            ) : null}
            {formatToggles.showTable ? (
              <FormatToggle
                active={viewMode === "table"}
                label="Tabela"
                onClick={() => switchViewMode("table")}
              />
            ) : null}
            {formatToggles.showChart ? (
              <FormatToggle
                active={viewMode === "chart"}
                label="Gráfico"
                onClick={() => switchViewMode("chart")}
              />
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="mdc-rich-dashboard__panel-body">
        {viewMode === "text" && hasText ? (
          <div className="mdc-rich-presentation__text mdc-rich-dashboard__data-text">
            <ChatMarkdown content={textBody} />
          </div>
        ) : null}

        {viewMode === "table" && hasTable ? (
          <ChatRichTable
            presentation={table}
            hideTitle
            embeddedInDashboard
            onDrillDown={onDrillDown}
          />
        ) : null}

        {viewMode === "chart" && resolvedChart ? (
          <ChatRichChart
            presentation={resolvedChart}
            hideTitle
            chartExplanation={resolvedChart.chartExplanation}
            onDrillDown={onDrillDown}
            onOpenCanvas={onOpenCanvas}
          />
        ) : null}
      </div>
    </section>
  );
}
