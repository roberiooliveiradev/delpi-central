import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { HelpTooltip } from "./HelpTooltip";
import type { HistoryGanttLayout } from "../utils/historyFormatting";

type HistoryEventGanttProps = {
  layout: HistoryGanttLayout;
  isOpen?: boolean;
  isLate?: boolean;
};

export function HistoryEventGantt({ layout, isOpen = false, isLate = false }: HistoryEventGanttProps) {
  const barLeft = Math.min(layout.startPercent, layout.endPercent);
  const barWidth = Math.max(2, Math.abs(layout.endPercent - layout.startPercent));

  return (
    <div
      className="lmps-history-gantt"
      aria-label="Faixa temporal do evento"
      role="img"
    >
      <div className="lmps-history-gantt__track">
        <span
          className={[
            "lmps-history-gantt__bar",
            isOpen ? "lmps-history-gantt__bar--open" : "",
            isLate ? "lmps-history-gantt__bar--late" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          style={{
            left: `${barLeft}%`,
            width: `${barWidth}%`,
          }}
        />
        {layout.limitPercent != null ? (
          <span
            className="lmps-history-gantt__limit"
            style={{ left: `${layout.limitPercent}%` }}
            aria-hidden="true"
          />
        ) : null}
      </div>
      <div className="lmps-history-gantt__legend">
        <span>Início</span>
        <span>Limite</span>
        <HelpTooltip
          content={LMPS_HELP_TOOLTIPS.detail.historyGantt}
          ariaLabel="Ajuda: faixa temporal"
          className="lmps-history-gantt__help"
        />
      </div>
    </div>
  );
}
