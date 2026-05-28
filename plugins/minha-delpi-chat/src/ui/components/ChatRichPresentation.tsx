import { useEffect, useMemo, useState } from "react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import {
  getAvailableFormatsFromToolCalls,
  getPreferredFormatFromToolCalls,
  getPresentationPairFromToolCalls,
  resolveRichTextContent,
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
  const availableFormats = useMemo(
    () => getAvailableFormatsFromToolCalls(toolCalls),
    [toolCalls],
  );
  const resolvedText = useMemo(
    () => resolveRichTextContent(textContent, toolCalls),
    [textContent, toolCalls],
  );

  const hasChart =
    primary?.type === "chart" || availableFormats.includes("chart");
  const hasTable =
    primary?.type === "table" ||
    table?.type === "table" ||
    availableFormats.includes("table");
  const hasText = availableFormats.includes("text") || Boolean(resolvedText);

  const formatCount = [hasText, hasChart, hasTable].filter(Boolean).length;
  const showToggle = formatCount >= 2;

  const defaultMode = resolveDefaultViewMode(
    toolCalls,
    hasText,
    hasChart,
    hasTable,
  );

  const [viewMode, setViewMode] = useState<ViewFormat>(defaultMode);

  useEffect(() => {
    setViewMode(defaultMode);
  }, [defaultMode, toolCalls]);

  if (!primary && !table && !resolvedText) {
    return null;
  }

  if (primary?.type === "kpi") {
    return (
      <div className="mdc-rich-presentation mdc-rich-presentation--enter">
        <div className="mdc-rich-presentation__actions">
          <ExpandButton presentation={primary} />
        </div>
        <ChatRichKpi presentation={primary} />
      </div>
    );
  }

  const chartPresentation =
    primary?.type === "chart" ? primary : null;
  const tablePresentation =
    table?.type === "table"
      ? table
      : primary?.type === "table"
        ? primary
        : null;

  const expandTarget =
    viewMode === "chart"
      ? chartPresentation
      : viewMode === "table"
        ? tablePresentation
        : null;

  return (
    <div className="mdc-rich-presentation mdc-rich-presentation--enter">
      {showToggle ? (
        <div className="mdc-rich-presentation__actions">
          {hasText ? (
            <FormatToggle
              active={viewMode === "text"}
              label="Texto"
              onClick={() => setViewMode("text")}
            />
          ) : null}
          {hasChart ? (
            <FormatToggle
              active={viewMode === "chart"}
              label="Gráfico"
              onClick={() => setViewMode("chart")}
            />
          ) : null}
          {hasTable ? (
            <FormatToggle
              active={viewMode === "table"}
              label="Tabela"
              onClick={() => setViewMode("table")}
            />
          ) : null}
          {expandTarget ? <ExpandButton presentation={expandTarget} /> : null}
        </div>
      ) : expandTarget ? (
        <div className="mdc-rich-presentation__actions">
          <ExpandButton presentation={expandTarget} />
        </div>
      ) : null}

      {viewMode === "text" && hasText ? (
        <div className="mdc-rich-presentation__text">
          <ChatMarkdown content={resolvedText} />
        </div>
      ) : null}

      {viewMode === "chart" && chartPresentation ? (
        <ChatRichChart presentation={chartPresentation} />
      ) : null}

      {viewMode === "table" && tablePresentation ? (
        <ChatRichTable presentation={tablePresentation} onDrillDown={onDrillDown} />
      ) : null}
    </div>
  );
}
