import { ZoomIn, ZoomOut } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { DaySegment } from "../../utils/dayTimeline";
import { endOfLocalDayMs, presentDayEvent } from "../../utils/dayTimeline";

const ZOOM_HOURS = [2, 4, 8, 12, 24];
const DEFAULT_VISIBLE_HOURS = 4;
const FALLBACK_PX_PER_HOUR = 140;

const SEGMENT_CLASS: Record<string, string> = {
  producing: "producing",
  stopped: "stopped",
  inactive: "inactive",
};

function segmentClass(state: string): string {
  return SEGMENT_CLASS[state] ?? "other";
}

function tickStep(visibleHours: number): number {
  if (visibleHours <= 4) return 1;
  if (visibleHours <= 8) return 2;
  return 4;
}

export function DayTimelineBar({ segments, fromIso, nowMs }: { segments: DaySegment[]; fromIso: string; nowMs: number }) {
  const [visibleHours, setVisibleHours] = useState(DEFAULT_VISIBLE_HOURS);
  const viewportRef = useRef<HTMLDivElement>(null);
  const [viewportWidth, setViewportWidth] = useState(0);
  const initialized = useRef(false);
  const drag = useRef<{ x: number; scrollLeft: number } | null>(null);

  const dayStart = Date.parse(fromIso);
  const dayEnd = Number.isFinite(dayStart) ? endOfLocalDayMs(dayStart) : dayStart;
  const span = Math.max(1, dayEnd - dayStart);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => setViewportWidth(entries[0].contentRect.width));
    observer.observe(viewport);
    return () => observer.disconnect();
  }, []);

  const pxPerHour = viewportWidth > 0 ? viewportWidth / visibleHours : FALLBACK_PX_PER_HOUR;
  const trackWidth = pxPerHour * 24;
  const toPx = (ms: number) => Math.max(0, Math.min(trackWidth, ((ms - dayStart) / span) * trackWidth));

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!initialized.current && viewport && viewportWidth > 0) {
      viewport.scrollLeft = Math.max(0, trackWidth - viewportWidth);
      initialized.current = true;
    }
  }, [viewportWidth, trackWidth]);

  const zoom = (hours: number) => {
    const viewport = viewportRef.current;
    const anchorMs = viewport
      ? dayStart + (((viewport.scrollLeft + viewport.clientWidth / 2) / Math.max(1, trackWidth)) * span)
      : dayEnd;
    setVisibleHours(hours);
    requestAnimationFrame(() => {
      const el = viewportRef.current;
      if (!el) return;
      const newPxPerHour = el.clientWidth / hours;
      el.scrollLeft = ((anchorMs - dayStart) / span) * (newPxPerHour * 24) - el.clientWidth / 2;
    });
  };

  const zoomIndex = ZOOM_HOURS.indexOf(visibleHours);

  if (!Number.isFinite(dayStart)) return null;

  const stops = segments.filter((segment) => segment.state === "stopped" && segment.item);
  const showNow = nowMs >= dayStart && nowMs <= dayEnd;
  const step = tickStep(visibleHours);

  return (
    <div className="delpi-mes-daybar">
      <div className="delpi-mes-daybar__controls">
        <span aria-live="polite">Janela de {visibleHours}h</span>
        <button type="button" onClick={() => zoom(ZOOM_HOURS[Math.min(ZOOM_HOURS.length - 1, zoomIndex + 1)])} disabled={zoomIndex >= ZOOM_HOURS.length - 1} aria-label="Reduzir zoom da linha do tempo">
          <ZoomOut aria-hidden="true" />
        </button>
        <button type="button" onClick={() => zoom(ZOOM_HOURS[Math.max(0, zoomIndex - 1)])} disabled={zoomIndex <= 0} aria-label="Aumentar zoom da linha do tempo">
          <ZoomIn aria-hidden="true" />
        </button>
      </div>
      <div
        ref={viewportRef}
        className="delpi-mes-daybar__viewport"
        role="group"
        aria-label="Linha do tempo do dia — arraste ou role horizontalmente para navegar"
        tabIndex={0}
        onPointerDown={(event) => {
          const viewport = viewportRef.current;
          if (!viewport) return;
          drag.current = { x: event.clientX, scrollLeft: viewport.scrollLeft };
          viewport.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          const viewport = viewportRef.current;
          if (!viewport || !drag.current) return;
          viewport.scrollLeft = drag.current.scrollLeft - (event.clientX - drag.current.x);
        }}
        onPointerUp={() => { drag.current = null; }}
        onPointerCancel={() => { drag.current = null; }}
      >
        <div className="delpi-mes-daybar__canvas" style={{ width: `${trackWidth}px` }}>
          <div className="delpi-mes-daybar__ticks" aria-hidden="true">
            {Array.from({ length: 24 / step + 1 }, (_, i) => i * step).map((hour) => (
              <span key={hour} style={{ left: `${(hour / 24) * trackWidth}px` }}>{String(hour).padStart(2, "0")}h</span>
            ))}
          </div>
          <div className="delpi-mes-daybar__track" aria-hidden="true">
            {segments.map((segment, index) => (
              <span
                key={segment.item?.stateEventId ?? `gap-${index}`}
                className={`delpi-mes-daybar__segment delpi-mes-daybar__segment--${segmentClass(segment.state)}`}
                style={{ left: `${toPx(segment.startMs)}px`, width: `${Math.max(2, toPx(segment.endMs) - toPx(segment.startMs))}px` }}
                title={segment.item ? presentDayEvent(segment.item).label : "Sem atividade"}
              />
            ))}
            {showNow ? (
              <span className="delpi-mes-daybar__now" style={{ left: `${toPx(nowMs)}px` }}>
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
                  style={{ left: `${toPx(mid)}px` }}
                  data-lane={index % 2}
                >
                  {reason}
                </span>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
