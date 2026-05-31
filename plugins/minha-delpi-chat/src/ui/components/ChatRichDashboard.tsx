import { LayoutPanelLeft } from "lucide-react";
import type { ChatCanvasOpenPayload, ChatPresentation } from "../../data/api/chatTypes";
import { presentationToCanvasPayload } from "./chartCanvasMarkdown";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTable } from "./ChatRichTable";
import "./ChatRichDashboard.css";

type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;

type PanelPresentation = DashboardPresentation["panels"][number]["presentation"];

function renderPanel(
  presentation: PanelPresentation,
  onDrillDown?: (query: string) => void,
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void,
) {
  switch (presentation.type) {
    case "kpi":
      return <ChatRichKpi presentation={presentation} />;
    case "chart":
      return (
        <ChatRichChart
          presentation={presentation}
          hideTitle
          onDrillDown={onDrillDown}
          onOpenCanvas={onOpenCanvas}
        />
      );
    case "table":
      return (
        <ChatRichTable
          presentation={presentation}
          hideTitle
          onDrillDown={onDrillDown}
        />
      );
    default:
      return null;
  }
}

export function ChatRichDashboard({
  presentation,
  onDrillDown,
  onOpenCanvas,
}: {
  presentation: DashboardPresentation;
  onDrillDown?: (query: string) => void;
  onOpenCanvas?: (payload: ChatCanvasOpenPayload) => void;
}) {
  const { title, panels } = presentation;

  return (
    <div className="mdc-rich-dashboard">
      <div className="mdc-rich-dashboard__header">
        {title ? <div className="mdc-rich-dashboard__title">{title}</div> : <span />}
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
      <div className="mdc-rich-dashboard__grid">
        {panels.map((panel) => (
          <section key={panel.id} className="mdc-rich-dashboard__panel">
            {panel.title ? (
              <h4 className="mdc-rich-dashboard__panel-title">{panel.title}</h4>
            ) : null}
            <div className="mdc-rich-dashboard__panel-body">
              {renderPanel(panel.presentation, onDrillDown, onOpenCanvas)}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
