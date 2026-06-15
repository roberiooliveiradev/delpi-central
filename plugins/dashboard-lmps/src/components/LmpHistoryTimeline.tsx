import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { HistoryEventGantt } from "./HistoryEventGantt";
import type { LmpHistoryEvent } from "../types/lmp";
import {
  buildHistoryGanttLayout,
  formatHistoryDateTime,
  formatProcessStageLabel,
  groupHistoryByRevision,
  isHistoryEngineeringFlow,
  resolveHistoryDuration,
  resolveHistoryStatus,
} from "../utils/historyFormatting";

type LmpHistoryTimelineProps = {
  events: LmpHistoryEvent[];
  emptyMessage?: string;
};

function renderTimelineBadge(label: string, className: string) {
  return <span className={`lmps-history-timeline__badge ${className}`}>{label}</span>;
}

function renderEventBadges(event: LmpHistoryEvent) {
  const badges = [];

  if (event.is_current) {
    badges.push(renderTimelineBadge("Atual", "lmps-history-timeline__badge--current"));
  }

  if (event.is_open) {
    badges.push(renderTimelineBadge("Em andamento", "lmps-history-timeline__badge--open"));
  } else {
    badges.push(renderTimelineBadge("Concluído", "lmps-history-timeline__badge--done"));
  }

  if (event.is_late) {
    badges.push(renderTimelineBadge("Atrasado", "lmps-history-timeline__badge--late"));
  }

  if (isHistoryEngineeringFlow(event)) {
    badges.push(renderTimelineBadge("Engenharia", "lmps-history-timeline__badge--engineering"));
  }

  return badges;
}

export function LmpHistoryTimeline({
  events,
  emptyMessage = "Nenhum evento registrado no histórico da OV.",
}: LmpHistoryTimelineProps) {
  if (events.length === 0) {
    return <p className="lmps-detail__empty">{emptyMessage}</p>;
  }

  const groups = groupHistoryByRevision(events);

  return (
    <div className="lmps-history-timeline" aria-label="Linha do tempo da OV">
      {groups.map((group) => (
        <section
          key={group.revision}
          className="lmps-history-timeline__revision"
          aria-label={`Revisão ${group.revision}`}
        >
          <header className="lmps-history-timeline__revision-header">
            <span className="lmps-history-timeline__revision-label">Revisão</span>
            <strong>{group.revision}</strong>
            <span className="lmps-history-timeline__revision-meta">
              {group.events.length} evento(s)
            </span>
          </header>

          <ol className="lmps-history-timeline__list">
            {group.events.map((event, index) => {
              const stageTitle = formatProcessStageLabel(
                event.stage_code,
                event.stage_label,
              );
              const processTitle = formatProcessStageLabel(
                event.process_code,
                event.process_label,
              );
              const startLabel = formatHistoryDateTime(
                event.start_date,
                event.start_time,
              );
              const endLabel = event.is_open
                ? "Em andamento"
                : formatHistoryDateTime(event.end_date, event.end_time);
              const limitLabel = formatHistoryDateTime(
                event.limit_date,
                event.limit_time,
              );
              const statusLabel = resolveHistoryStatus(event);
              const ganttLayout = buildHistoryGanttLayout(event, group.events);

              return (
                <li
                  key={`${group.revision}-${index}-${event.stage_code}-${event.start_date}`}
                  className={[
                    "lmps-history-timeline__item",
                    event.is_current ? "lmps-history-timeline__item--current" : "",
                    event.is_late ? "lmps-history-timeline__item--late" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <div className="lmps-history-timeline__marker" aria-hidden="true">
                    <span className="lmps-history-timeline__dot" />
                  </div>

                  <div className="lmps-history-timeline__content">
                    <div className="lmps-history-timeline__title-row">
                      <h4>{stageTitle}</h4>
                      <div className="lmps-history-timeline__badges">{renderEventBadges(event)}</div>
                    </div>

                    <p className="lmps-history-timeline__process">
                      Processo: {processTitle}
                    </p>

                    {ganttLayout ? (
                      <HistoryEventGantt
                        layout={ganttLayout}
                        isOpen={Boolean(event.is_open)}
                        isLate={Boolean(event.is_late)}
                      />
                    ) : null}

                    <dl className="lmps-history-timeline__meta">
                      <div>
                        <dt>Início</dt>
                        <dd>{startLabel}</dd>
                      </div>
                      <div>
                        <dt>Limite</dt>
                        <dd>{limitLabel}</dd>
                      </div>
                      <div>
                        <dt>Encerramento</dt>
                        <dd>{endLabel}</dd>
                      </div>
                      <div>
                        <dt>Duração</dt>
                        <dd>{resolveHistoryDuration(event)}</dd>
                      </div>
                      <div>
                        <dt>Status</dt>
                        <dd>{statusLabel}</dd>
                      </div>
                    </dl>
                  </div>
                </li>
              );
            })}
          </ol>
        </section>
      ))}

      <p className="lmps-history-timeline__footnote">
        {LMPS_HELP_TOOLTIPS.detail.historyTimelineFootnote}
      </p>
    </div>
  );
}
