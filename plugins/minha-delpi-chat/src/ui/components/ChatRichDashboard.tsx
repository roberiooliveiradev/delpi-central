import type { ChatPresentation } from "../../data/api/chatTypes";
import { ChatRichChart } from "./ChatRichChart";
import { ChatRichKpi } from "./ChatRichKpi";
import { ChatRichTable } from "./ChatRichTable";
import "./ChatRichDashboard.css";

type DashboardPresentation = Extract<ChatPresentation, { type: "dashboard" }>;

type PanelPresentation = DashboardPresentation["panels"][number]["presentation"];

function renderPanel(
  presentation: PanelPresentation,
  onDrillDown?: (query: string) => void,
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
}: {
  presentation: DashboardPresentation;
  onDrillDown?: (query: string) => void;
}) {
  const { title, panels } = presentation;

  return (
    <div className="mdc-rich-dashboard">
      {title ? <div className="mdc-rich-dashboard__title">{title}</div> : null}
      <div className="mdc-rich-dashboard__grid">
        {panels.map((panel) => (
          <section key={panel.id} className="mdc-rich-dashboard__panel">
            {panel.title ? (
              <h4 className="mdc-rich-dashboard__panel-title">{panel.title}</h4>
            ) : null}
            <div className="mdc-rich-dashboard__panel-body">
              {renderPanel(panel.presentation, onDrillDown)}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
