import type { DaySegment } from "../../utils/dayTimeline";
import { endOfLocalDayMs, presentDayEvent } from "../../utils/dayTimeline";

const SEGMENT_CLASS: Record<string, string> = {
  producing: "producing",
  stopped: "stopped",
  inactive: "inactive",
};

function segmentClass(state: string): string {
  return SEGMENT_CLASS[state] ?? "other";
}

export function DayTimelineBar({ segments, fromIso, nowMs }: { segments: DaySegment[]; fromIso: string; nowMs: number }) {
  const dayStart = Date.parse(fromIso);
  if (!Number.isFinite(dayStart)) return null;
  const dayEnd = endOfLocalDayMs(dayStart);
  const span = Math.max(1, dayEnd - dayStart);
  const pct = (ms: number) => Math.max(0, Math.min(100, ((ms - dayStart) / span) * 100));
  const left = (ms: number) => `${pct(ms)}%`;
  const width = (segment: DaySegment) => `${Math.max(0.25, pct(segment.endMs) - pct(segment.startMs))}%`;
  const stops = segments.filter((segment) => segment.state === "stopped" && segment.item);
  const showNow = nowMs >= dayStart && nowMs <= dayEnd;

  return (
    <div className="delpi-mes-daybar" role="img" aria-label="Linha do tempo do dia com períodos de produção, parada e sem atividade">
      <div className="delpi-mes-daybar__ticks" aria-hidden="true">
        {Array.from({ length: 13 }, (_, i) => i * 2).map((hour) => (
          <span key={hour} style={{ left: `${(hour / 24) * 100}%` }}>{String(hour).padStart(2, "0")}h</span>
        ))}
      </div>
      <div className="delpi-mes-daybar__track" aria-hidden="true">
        {segments.map((segment, index) => (
          <span
            key={segment.item?.stateEventId ?? `gap-${index}`}
            className={`delpi-mes-daybar__segment delpi-mes-daybar__segment--${segmentClass(segment.state)}`}
            style={{ left: left(segment.startMs), width: width(segment) }}
            title={segment.item ? presentDayEvent(segment.item).label : "Sem atividade"}
          />
        ))}
        {showNow ? (
          <span className="delpi-mes-daybar__now" style={{ left: left(nowMs) }}>
            <span className="delpi-mes-daybar__now-label">Agora</span>
          </span>
        ) : null}
      </div>
      <div className="delpi-mes-daybar__marks" aria-hidden="true">
        {stops.map((segment, index) => {
          const mid = segment.startMs + (segment.endMs - segment.startMs) / 2;
          const reason = segment.item?.downtime?.reasonLabel ?? "Sem motivo informado";
          return (
            <span
              key={segment.item?.stateEventId ?? index}
              className="delpi-mes-daybar__mark"
              style={{ left: left(mid) }}
              data-lane={index % 2}
            >
              {reason}
            </span>
          );
        })}
      </div>
    </div>
  );
}
