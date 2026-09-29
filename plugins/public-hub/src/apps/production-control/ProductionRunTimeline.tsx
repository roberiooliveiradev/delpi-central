import { useEffect, useState } from "react";
import type { RunTimeline } from "./api";
import {
  formatDurationHms,
  formatTimeHm,
  liveDurationSeconds,
  liveSummary,
  stateLabel,
} from "./runTimeline";

type Props = {
  timeline: RunTimeline;
  serverNow: () => number;
  /** Chamado ao clicar numa parada ainda sem motivo (classificação por id). */
  onSelectDowntime?: (item: RunTimeline["items"][number]) => void;
};

function itemDescription(item: RunTimeline["items"][number], seconds: number): string {
  const base = `${stateLabel(item.state)} · ${formatTimeHm(item.startedAt)}`;
  const dt = item.downtime;
  if (item.state === "stopped") {
    const reason = dt?.reasonLabel ?? (dt ? "Motivo não informado" : "Motivo não disponível");
    return `${base} · ${reason} · ${formatDurationHms(seconds)}`;
  }
  return `${base} · ${formatDurationHms(seconds)}`;
}

/**
 * Timeline do run: faixa proporcional compacta + histórico legível.
 * O trecho aberto continua evoluindo localmente com o relógio do servidor.
 */
export function ProductionRunTimeline({ timeline, serverNow, onSelectDowntime }: Props) {
  const [now, setNow] = useState(() => serverNow());

  useEffect(() => {
    setNow(serverNow());
    const timer = window.setInterval(() => setNow(serverNow()), 1000);
    return () => window.clearInterval(timer);
  }, [serverNow, timeline.referenceAt]);

  if (timeline.items.length === 0) {
    return <p className="pcp-pub__run-note">Sem eventos de produção registrados.</p>;
  }

  const durations = timeline.items.map((item) => liveDurationSeconds(item, now));
  const summary = liveSummary(timeline.items, now);
  const total = Math.max(
    1,
    durations.reduce((acc, v) => acc + v, 0),
  );

  return (
    <div className="pcp-pub-timeline">
      <div
        className="pcp-pub-timeline__band"
        role="img"
        aria-label={timeline.items
          .map((item, i) => itemDescription(item, durations[i]))
          .join(" → ")}
      >
        {timeline.items.map((item, i) => (
          <span
            key={item.id}
            className={`pcp-pub-timeline__seg pcp-pub-timeline__seg--${item.state}`}
            style={{ flexGrow: Math.max(1, durations[i]) }}
            title={itemDescription(item, durations[i])}
          />
        ))}
      </div>
      <ol className="pcp-pub-timeline__list">
        {timeline.items.map((item, i) => {
          const unclassified =
            item.state === "stopped" &&
            Boolean(item.downtime) &&
            !item.downtime?.confirmed;
          const body = (
            <>
              <strong>
                {item.state === "stopped" ? "Parada" : stateLabel(item.state)}
                {item.state === "producing" && i > 0 ? " retomada" : ""}
                {item.endedAt == null ? " · em curso" : ""}
              </strong>
              {item.state === "stopped" ? (
                <span className="pcp-pub-timeline__reason">
                  {item.downtime?.reasonLabel ??
                    (item.downtime ? "Motivo não informado" : "Motivo não disponível")}
                  {unclassified ? " · pendente" : ""}
                </span>
              ) : null}
              {item.downtime?.note ? (
                <span className="pcp-pub-timeline__note">{item.downtime.note}</span>
              ) : null}
              <span className="pcp-pub-timeline__duration">
                {formatDurationHms(durations[i])}
              </span>
            </>
          );
          return (
            <li key={item.id} className="pcp-pub-timeline__entry">
              <span className="pcp-pub-timeline__time">{formatTimeHm(item.startedAt)}</span>
              {unclassified && onSelectDowntime ? (
                <button
                  type="button"
                  className="pcp-pub-timeline__body pcp-pub-timeline__body--action"
                  onClick={() => onSelectDowntime(item)}
                >
                  {body}
                  <span className="pcp-pub-timeline__cta">Informar motivo</span>
                </button>
              ) : (
                <span className="pcp-pub-timeline__body">{body}</span>
              )}
            </li>
          );
        })}
      </ol>
      <p className="pcp-pub-timeline__summary">
        Produzindo {formatDurationHms(summary.producingSeconds)} · Parado{" "}
        {formatDurationHms(summary.stoppedSeconds)} ·{" "}
        {summary.stopCount}{" "}
        {summary.stopCount === 1 ? "parada" : "paradas"}
      </p>
    </div>
  );
}
