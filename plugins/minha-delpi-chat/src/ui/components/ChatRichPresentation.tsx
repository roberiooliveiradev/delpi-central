import { useState } from "react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import { getPresentationPairFromToolCalls } from "./chatPresentation";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ExpandButton } from "./ChatExpandModal";
import "./ChatRichKpi.css";
import "./ChatExpandModal.css";

type ViewMode = "chart" | "table" | "text";

function getAvailableFormats(toolCalls: ChatToolCall[]): string[] {
  for (const tc of toolCalls) {
    const formats = (tc.metadata as Record<string, unknown>)?.availableFormats;
    if (Array.isArray(formats)) {
      return formats as string[];
    }
  }
  return [];
}

export function ChatRichPresentation({
  toolCalls,
  onDrillDown,
}: {
  toolCalls: ChatToolCall[];
  onDrillDown?: (query: string) => void;
}) {
  const { primary, table } = getPresentationPairFromToolCalls(toolCalls);
  const availableFormats = getAvailableFormats(toolCalls);

  const defaultMode: ViewMode = primary?.type === "chart"
    ? "chart"
    : primary?.type === "table"
      ? "table"
      : "text";

  const [viewMode, setViewMode] = useState<ViewMode>(defaultMode);

  if (!primary) {
    return null;
  }

  if (primary.type === "kpi") {
    return (
      <div className="mdc-rich-presentation">
        <div className="mdc-rich-presentation__actions">
          <ExpandButton presentation={primary} />
        </div>
        <ChatRichKpi presentation={primary} />
      </div>
    );
  }

  const hasChart = primary.type === "chart" || availableFormats.includes("chart");
  const hasTable = primary.type === "table" || !!table || availableFormats.includes("table");
  const showToggle = (hasChart && hasTable) || (hasChart || hasTable);

  const currentPresentation = viewMode === "chart"
    ? (primary.type === "chart" ? primary : null)
    : viewMode === "table"
      ? (table?.type === "table" ? table : primary.type === "table" ? primary : null)
      : null;

  if (viewMode === "text") {
    return showToggle ? (
      <div className="mdc-rich-presentation">
        <div className="mdc-rich-presentation__actions">
          {hasChart && (
            <button
              className="mdc-rich-chart__toggle-btn"
              onClick={() => setViewMode("chart")}
            >
              📊 Gráfico
            </button>
          )}
          {hasTable && (
            <button
              className="mdc-rich-chart__toggle-btn"
              onClick={() => setViewMode("table")}
            >
              📋 Tabela
            </button>
          )}
        </div>
      </div>
    ) : null;
  }

  return (
    <div className="mdc-rich-presentation">
      <div className="mdc-rich-presentation__actions">
        {showToggle && (
          <>
            {hasChart && (
              <button
                className={`mdc-rich-chart__toggle-btn ${viewMode === "chart" ? "mdc-rich-chart__toggle-btn--active" : ""}`}
                onClick={() => setViewMode("chart")}
              >
                📊 Gráfico
              </button>
            )}
            {hasTable && (
              <button
                className={`mdc-rich-chart__toggle-btn ${viewMode === "table" ? "mdc-rich-chart__toggle-btn--active" : ""}`}
                onClick={() => setViewMode("table")}
              >
                📋 Tabela
              </button>
            )}
            <button
              className="mdc-rich-chart__toggle-btn"
              onClick={() => setViewMode("text")}
            >
              📝 Texto
            </button>
          </>
        )}
        {currentPresentation && <ExpandButton presentation={currentPresentation} />}
      </div>

      {viewMode === "chart" && currentPresentation?.type === "chart" && (
        <ChatRichChart presentation={currentPresentation} />
      )}
      {viewMode === "table" && currentPresentation?.type === "table" && (
        <ChatRichTable presentation={currentPresentation} onDrillDown={onDrillDown} />
      )}
    </div>
  );
}
