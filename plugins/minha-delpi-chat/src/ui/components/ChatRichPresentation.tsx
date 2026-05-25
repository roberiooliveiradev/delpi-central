import { useState } from "react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import { getPresentationPairFromToolCalls } from "./chatPresentation";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import "./ChatRichKpi.css";

type ViewMode = "primary" | "table";

export function ChatRichPresentation({
  toolCalls,
}: {
  toolCalls: ChatToolCall[];
}) {
  const { primary, table } = getPresentationPairFromToolCalls(toolCalls);
  const [viewMode, setViewMode] = useState<ViewMode>("primary");

  if (!primary) {
    return null;
  }

  if (primary.type === "kpi") {
    return <ChatRichKpi presentation={primary} />;
  }

  const hasToggle = primary.type === "chart" && table?.type === "table";
  const current = viewMode === "table" && table ? table : primary;

  return (
    <div className="mdc-rich-presentation">
      {hasToggle && (
        <div className="mdc-rich-presentation__toggle">
          <button
            className={`mdc-rich-chart__toggle-btn ${viewMode === "primary" ? "mdc-rich-chart__toggle-btn--active" : ""}`}
            onClick={() => setViewMode("primary")}
          >
            📊 Gráfico
          </button>
          <button
            className={`mdc-rich-chart__toggle-btn ${viewMode === "table" ? "mdc-rich-chart__toggle-btn--active" : ""}`}
            onClick={() => setViewMode("table")}
          >
            📋 Tabela
          </button>
        </div>
      )}

      {current.type === "chart" && (
        <ChatRichChart presentation={current} />
      )}
      {current.type === "table" && (
        <ChatRichTable presentation={current} />
      )}
    </div>
  );
}
