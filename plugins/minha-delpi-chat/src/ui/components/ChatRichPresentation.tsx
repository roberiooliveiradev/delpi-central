import { useEffect, useMemo, useState } from "react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import {
  getPreferredFormatFromToolCalls,
  getPresentationPairFromToolCalls,
  getPresentationTitle,
  getTablePresentationFromPair,
  hasDisplayableRichText,
  resolveRichTextBody,
  type ViewFormat,
} from "./chatPresentation";
import { ChatMarkdown } from "./ChatMarkdown";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ExpandButton } from "./ChatExpandModal";
import "./ChatRichKpi.css";
import "./ChatExpandModal.css";

type ChatRichPresentationProps = {
  toolCalls: ChatToolCall[];
  textContent?: string | null;
  onDrillDown?: (query: string) => void;
};

function resolveDefaultViewMode(
  toolCalls: ChatToolCall[],
  hasText: boolean,
  hasChart: boolean,
  hasTable: boolean,
): ViewFormat {
  const preferred = getPreferredFormatFromToolCalls(toolCalls);

  if (preferred === "text" && hasText) {
    return "text";
  }

  if (preferred === "chart" && hasChart) {
    return "chart";
  }

  if (preferred === "table" && hasTable) {
    return "table";
  }

  if (hasText) {
    return "text";
  }

  if (hasChart) {
    return "chart";
  }

  if (hasTable) {
    return "table";
  }

  return "text";
}

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

export function ChatRichPresentation({
  toolCalls,
  textContent,
  onDrillDown,
}: ChatRichPresentationProps) {
  const { primary, table } = useMemo(
    () => getPresentationPairFromToolCalls(toolCalls),
    [toolCalls],
  );
  const presentationTitle = useMemo(
    () => getPresentationTitle(textContent, toolCalls),
    [textContent, toolCalls],
  );
  const textBody = useMemo(
    () => resolveRichTextBody(textContent, toolCalls),
    [textContent, toolCalls],
  );

  const chartPresentation =
    primary?.type === "chart" ? primary : null;
  const tablePresentation = useMemo(
    () => getTablePresentationFromPair({ primary, table }),
    [primary, table],
  );

  const hasText = hasDisplayableRichText(textBody) || Boolean(tablePresentation);
  const hasChartView = Boolean(chartPresentation);
  const hasTableView = Boolean(tablePresentation);

  const formatCount = [hasText, hasChartView, hasTableView].filter(Boolean).length;
  const showToggle = formatCount >= 2;

  const defaultMode = resolveDefaultViewMode(
    toolCalls,
    hasText,
    hasChartView,
    hasTableView,
  );

  const [viewMode, setViewMode] = useState<ViewFormat>(defaultMode);

  useEffect(() => {
    setViewMode(defaultMode);
  }, [defaultMode, toolCalls]);

  if (!primary && !table && !textBody && !presentationTitle) {
    return null;
  }

  if (primary?.type === "kpi") {
    return (
      <div className="mdc-rich-presentation mdc-rich-presentation--enter">
        <div className="mdc-rich-presentation__toolbar">
          <ExpandButton presentation={primary} />
        </div>
        <ChatRichKpi presentation={primary} />
      </div>
    );
  }

  const expandTarget =
    viewMode === "chart"
      ? chartPresentation
      : viewMode === "table"
        ? tablePresentation
        : null;

  const showSharedTitle = Boolean(presentationTitle);

  const formatToolbar =
    showToggle || expandTarget ? (
      <div className="mdc-rich-presentation__toolbar">
        {showToggle ? (
          <div className="mdc-rich-presentation__format-toggle" role="group" aria-label="Formato da resposta">
            {hasText ? (
              <FormatToggle
                active={viewMode === "text"}
                label="Texto"
                onClick={() => setViewMode("text")}
              />
            ) : null}
            {hasChartView ? (
              <FormatToggle
                active={viewMode === "chart"}
                label="Gráfico"
                onClick={() => setViewMode("chart")}
              />
            ) : null}
            {hasTableView ? (
              <FormatToggle
                active={viewMode === "table"}
                label="Tabela"
                onClick={() => setViewMode("table")}
              />
            ) : null}
          </div>
        ) : null}
        {expandTarget ? (
          <ExpandButton presentation={expandTarget} onDrillDown={onDrillDown} />
        ) : null}
      </div>
    ) : null;

  return (
    <div className="mdc-rich-presentation mdc-rich-presentation--enter">
      {formatToolbar}

      {showSharedTitle ? (
        <h3 className="mdc-rich-presentation__heading">{presentationTitle}</h3>
      ) : null}

      {viewMode === "text" && hasText && textBody ? (
        <div className="mdc-rich-presentation__text">
          <ChatMarkdown content={textBody} />
        </div>
      ) : null}

      {viewMode === "chart" && hasChartView && chartPresentation ? (
        <ChatRichChart presentation={chartPresentation} hideTitle={showSharedTitle} />
      ) : null}

      {viewMode === "table" && hasTableView && tablePresentation ? (
        <ChatRichTable
          presentation={tablePresentation}
          hideTitle={showSharedTitle}
          onDrillDown={onDrillDown}
        />
      ) : null}
    </div>
  );
}
