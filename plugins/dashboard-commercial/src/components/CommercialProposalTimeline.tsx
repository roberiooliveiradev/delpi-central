import type { CommercialProposalHistoryEvent } from "../types/commercial";
import {
  formatHistoryDateTime,
  formatProcessStageLabel,
  groupHistoryByRevision,
  isHistoryEngineeringFlow,
  resolveHistoryDuration,
  resolveHistoryFlowLabels,
  resolveHistoryStatus,
} from "../utils/proposalHistoryFormatting";

type CommercialProposalTimelineProps = {
  events: CommercialProposalHistoryEvent[];
  emptyMessage?: string;
};

function renderTimelineBadge(label: string, className: string) {
  return (
    <span className={`dc-history-timeline__badge ${className}`}>{label}</span>
  );
}

function renderEventBadges(event: CommercialProposalHistoryEvent) {
  const badges = [];

  if (event.is_current) {
    badges.push(
      renderTimelineBadge(
        event.is_open ? "Atual" : "Último evento",
        event.is_open
          ? "dc-history-timeline__badge--current"
          : "dc-history-timeline__badge--last"
      )
    );
  }

  if (event.is_open) {
    badges.push(
      renderTimelineBadge("Em andamento", "dc-history-timeline__badge--open")
    );
  } else {
    badges.push(
      renderTimelineBadge("Concluído", "dc-history-timeline__badge--done")
    );
  }

  if (event.is_late) {
    badges.push(
      renderTimelineBadge("Atrasado", "dc-history-timeline__badge--late")
    );
  }

  if (isHistoryEngineeringFlow(event)) {
    badges.push(
      renderTimelineBadge("Engenharia", "dc-history-timeline__badge--engineering")
    );
  }

  for (const label of resolveHistoryFlowLabels(event)) {
    const className =
      label.includes("retorno") || label.includes("Retorno")
        ? "dc-history-timeline__badge--flow-return"
        : label.includes("avanço") || label.includes("Saída")
          ? "dc-history-timeline__badge--flow-advance"
          : "dc-history-timeline__badge--flow-entry";
    badges.push(renderTimelineBadge(label, className));
  }

  return badges;
}

export function CommercialProposalTimeline({
  events,
  emptyMessage = "Nenhum evento registrado no histórico da OV.",
}: CommercialProposalTimelineProps) {
  if (events.length === 0) {
    return <p className="dc-detail__empty">{emptyMessage}</p>;
  }

  const groups = groupHistoryByRevision(events);

  return (
    <div className="dc-history-timeline" aria-label="Linha do tempo da OV">
      {groups.map((group) => (
        <section
          key={group.revision}
          className="dc-history-timeline__revision"
          aria-label={`Revisão ${group.revision}`}
        >
          <header className="dc-history-timeline__revision-header">
            <span className="dc-history-timeline__revision-label">Revisão</span>
            <strong>{group.revision}</strong>
            <span className="dc-history-timeline__revision-meta">
              {group.events.length} evento(s)
            </span>
          </header>

          <ol className="dc-history-timeline__list">
            {group.events.map((event, index) => {
              const stageTitle = formatProcessStageLabel(
                event.stage_code,
                event.stage_label
              );
              const processTitle = formatProcessStageLabel(
                event.process_code,
                event.process_label
              );
              const startLabel = formatHistoryDateTime(
                event.start_date,
                event.start_time
              );
              const endLabel = event.is_open
                ? "Em andamento"
                : formatHistoryDateTime(event.end_date, event.end_time);
              const limitLabel = formatHistoryDateTime(
                event.limit_date,
                event.limit_time
              );
              const statusLabel = resolveHistoryStatus(event);

              return (
                <li
                  key={`${group.revision}-${index}-${event.stage_code}-${event.start_date}`}
                  className={[
                    "dc-history-timeline__item",
                    event.is_current ? "dc-history-timeline__item--current" : "",
                    event.is_late ? "dc-history-timeline__item--late" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <div
                    className="dc-history-timeline__marker"
                    aria-hidden="true"
                  >
                    <span className="dc-history-timeline__dot" />
                  </div>

                  <div className="dc-history-timeline__content">
                    <div className="dc-history-timeline__title-row">
                      <h4>{stageTitle}</h4>
                      <div className="dc-history-timeline__badges">
                        {renderEventBadges(event)}
                      </div>
                    </div>

                    <p className="dc-history-timeline__process">
                      Processo: {processTitle}
                    </p>

                    <dl className="dc-history-timeline__meta">
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

      <p className="dc-history-timeline__footnote">
        Eventos do fluxo AIJ010 — datas e durações conforme registro no TOTVS.
      </p>
    </div>
  );
}
