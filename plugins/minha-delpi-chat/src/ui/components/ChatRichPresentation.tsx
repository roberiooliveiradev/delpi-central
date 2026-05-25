import { useState } from "react";
import type { ChatToolCall } from "../../data/api/chatTypes";
import { getPresentationPairFromToolCalls } from "./chatPresentation";
import { ChatRichTable } from "./ChatRichTable";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ExpandButton } from "./ChatExpandModal";
import "./ChatRichKpi.css";
import "./ChatExpandModal.css";

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
    return (
      <div className="mdc-rich-presentation">
        <div className="mdc-rich-presentation__actions">
          <ExpandButton presentation={primary} />
        </div>
        <ChatRichKpi presentation={primary} />
      </div>
    );
  }

  const hasToggle = primary.type === "chart" && table?.type === "table";
  const current = viewMode === "table" && table ? table : primary;

  return (
    <div className="mdc-rich-presentation">
      <div className="mdc-rich-presentation__actions">
        {hasToggle && (
          <>
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
          </>
        )}
        <ExpandButton presentation={current} />
      </div>

      {current.type === "chart" && (
        <ChatRichChart presentation={current} />
      )}
      {current.type === "table" && (
        <ChatRichTable presentation={current} />
      )}
    </div>
  );
}
