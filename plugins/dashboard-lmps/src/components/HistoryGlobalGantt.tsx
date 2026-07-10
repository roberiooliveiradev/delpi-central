import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import type { HistoryGlobalGanttLayout } from "../utils/historyGlobalGantt";

type HistoryGlobalGanttProps = {
  layout: HistoryGlobalGanttLayout;
};

export function HistoryGlobalGantt({ layout }: HistoryGlobalGanttProps) {
  return (
    <section className="lmps-history-global-gantt" aria-label="Visão global da linha do tempo">
      <div className="lmps-history-global-gantt__header">
        <h3>Visão global</h3>
        <HelpTooltip
          content={LMPS_HELP_TOOLTIPS.detail.historyGlobalGantt}
          ariaLabel="Ajuda: visão global da linha do tempo"
          className="lmps-history-global-gantt__help"
        />
      </div>

      <div className="lmps-history-global-gantt__track" role="img">
        {layout.segments.map((segment) => (
          <span
            key={segment.key}
            className={[
              "lmps-history-global-gantt__segment",
              segment.isCurrent ? "lmps-history-global-gantt__segment--current" : "",
              segment.isOpen ? "lmps-history-global-gantt__segment--open" : "",
              segment.isLate ? "lmps-history-global-gantt__segment--late" : "",
              segment.isEngineering ? "lmps-history-global-gantt__segment--engineering" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            style={{
              left: `${segment.leftPercent}%`,
              width: `${segment.widthPercent}%`,
            }}
            title={`Rev. ${segment.revision} · ${segment.label}`}
          />
        ))}
      </div>

      <div className="lmps-history-global-gantt__legend">
        <span>Rev. anterior</span>
        <span>Em aberto</span>
        <span>Atrasado</span>
        <span>Engenharia</span>
      </div>
    </section>
  );
}
