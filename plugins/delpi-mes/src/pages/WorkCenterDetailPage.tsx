import { LoadingState, loadingStatePanelBemClasses } from "@delpi/plugin-ui/index";
import {
  ArrowLeft, ClipboardList, Cog, Gauge, OctagonPause,
  PauseCircle, PlayCircle, User, Zap,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { BranchCode } from "../constants/routes";
import { useMonitoringData } from "../hooks/useMonitoringData";
import { useServerClock } from "../hooks/useServerClock";
import { useWorkCenterTimeline } from "../hooks/useWorkCenterTimeline";
import { workCenterImageUrl } from "../utils/assets";
import {
  buildDaySegments, downtimeReasonTotals, formatDayClock, formatHoursMinutes,
  localDayKey, presentDayEvent, presentDayState, summarizeDay,
} from "../utils/dayTimeline";
import { downtimeReasonDisplay, presentMonitoringState, runStateSignature } from "../utils/monitoringPresentation";
import { DayTimelineBar } from "../components/monitoring/DayTimelineBar";
import { MonitoringStatCards } from "../components/monitoring/MonitoringStatCards";
import type { StatCardItem } from "../utils/statItems";

const loadingClasses = loadingStatePanelBemClasses("delpi-mes");
const DATE_FORMAT = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });
const STATE_ROW_CLASS: Record<string, string> = {
  producing: "success", stopped: "danger", inactive: "inactive", setup: "warning", planned_stop: "info", idle: "info",
};

export function WorkCenterDetailPage({
  branch, workCenter, canViewHistory, onBack,
}: {
  branch: BranchCode; workCenter: string; canViewHistory: boolean; onBack: () => void;
}) {
  const monitoring = useMonitoringData(branch);
  const nowMs = useServerClock(monitoring.data?.referenceAt);
  const item = monitoring.data?.items.find((entry) => entry.workCenter === workCenter) ?? null;
  const signature = item ? runStateSignature(item) : null;
  const todayKey = localDayKey();
  const [dayKey, setDayKey] = useState(todayKey);
  const [eventStatus, setEventStatus] = useState("all");
  const history = useWorkCenterTimeline(branch, workCenter, signature, canViewHistory, dayKey);

  const timeline = history.data;
  const segments = useMemo(
    () => (timeline ? buildDaySegments(timeline.items, timeline.from, nowMs) : []),
    [timeline, nowMs],
  );
  const summary = useMemo(() => summarizeDay(segments, timeline?.from ?? "", nowMs), [segments, timeline, nowMs]);
  const reasons = useMemo(() => downtimeReasonTotals(segments), [segments]);
  const maxReasonSec = reasons[0]?.seconds ?? 0;
  const eventStates = useMemo(() => {
    const order = ["producing", "stopped", "setup", "planned_stop", "idle", "inactive"];
    const present = new Set(segments.map((segment) => segment.state));
    return order.filter((state) => present.has(state));
  }, [segments]);
  const visibleSegments = useMemo(
    () => (eventStatus === "all" ? segments : segments.filter((segment) => segment.state === eventStatus)),
    [segments, eventStatus],
  );

  const lastEvent = useMemo(() => {
    const events = segments.filter((segment) => segment.item);
    return events.length ? events[events.length - 1].item : null;
  }, [segments]);

  const state = item ? presentMonitoringState(item) : null;
  const statusLabel = state?.label ?? (lastEvent ? `${presentDayEvent(lastEvent).label} agora` : "Sem atividade");
  const statusTone = state?.tone ?? (lastEvent && lastEvent.state === "producing" ? "success" : lastEvent && lastEvent.state === "stopped" ? "danger" : "neutral");
  const productionOrder = item?.productionOrder ?? lastEvent?.productionOrder ?? null;
  const operationCode = item?.operationCode ?? lastEvent?.operationCode ?? null;
  const operatorName = item?.operatorName ?? null;
  const imageUrl = workCenterImageUrl(workCenter);

  const stats: StatCardItem[] = [
    { id: "producing-time", label: "Tempo produzindo", value: formatHoursMinutes(summary.producingSec), tone: "success", icon: PlayCircle },
    { id: "stopped-time", label: "Tempo parado", value: formatHoursMinutes(summary.stoppedSec), tone: "danger", icon: PauseCircle },
    { id: "stops", label: "Paradas no dia", value: summary.stops, tone: "warning", icon: OctagonPause },
    { id: "availability", label: "Disponibilidade do dia", value: summary.availabilityPct !== null ? `${summary.availabilityPct}%` : "—", tone: "info", icon: Gauge },
    { id: "current", label: "Status atual", value: statusLabel, tone: statusTone === "neutral" ? "info" : statusTone, icon: Zap },
  ];

  return (
    <section className="delpi-mes-wc" aria-labelledby="delpi-mes-wc-title">
      <nav className="delpi-mes-wc__breadcrumb" aria-label="Navegação">
        <a href="#" onClick={(event) => { event.preventDefault(); onBack(); }}>
          <ArrowLeft aria-hidden="true" /> Monitoramento
        </a>
        <span aria-hidden="true">/</span>
        <strong>{workCenter}</strong>
      </nav>

      <header className="delpi-mes-wc__head">
        <div className="delpi-mes-wc__identity">
          <h2 id="delpi-mes-wc-title">{workCenter}</h2>
          <span className={`delpi-mes-wc__status delpi-mes-wc__status--${statusTone}`}>
            <span className="delpi-mes-status-dot" aria-hidden="true" />
            {statusLabel}
          </span>
          <div className="delpi-mes-wc__meta">
            <span><ClipboardList aria-hidden="true" />OP {productionOrder || "—"}</span>
            <span><Cog aria-hidden="true" />Operação {operationCode || "—"}</span>
            <span><User aria-hidden="true" />{operatorName || "Operador não identificado"}</span>
          </div>
        </div>
        <div className="delpi-mes-wc__aside">
          <label className="delpi-mes-date-pill">
            <span className="delpi-mes-date-pill__text">
              <strong>{dayKey === todayKey ? "Hoje" : "Dia"}</strong>
              <em>{DATE_FORMAT.format(new Date(`${dayKey}T12:00:00`))}</em>
            </span>
            <input
              type="date"
              value={dayKey}
              max={todayKey}
              onChange={(event) => { if (event.target.value) setDayKey(event.target.value); }}
              aria-label="Selecionar dia do histórico"
            />
          </label>
          <div className="delpi-mes-wc__photo">
            {imageUrl ? <img src={imageUrl} alt="" aria-hidden="true" loading="lazy" /> : null}
            <span className={`delpi-mes-work-center-card__badge delpi-mes-work-center-card__badge--${statusTone}`}>
              <span className="delpi-mes-status-dot" aria-hidden="true" />
              {statusLabel}
            </span>
          </div>
        </div>
      </header>

      {!canViewHistory ? (
        <p className="delpi-mes-detail__history-disabled" role="status">Histórico diário não disponível para o seu perfil.</p>
      ) : history.loading && !timeline ? (
        <LoadingState classNames={loadingClasses} defaultMessage="Carregando histórico do dia…" />
      ) : history.error ? (
        <p className="delpi-mes-monitoring__stale" role="alert">
          {history.error} <button type="button" onClick={history.retry}>Tentar novamente</button>
        </p>
      ) : timeline ? (
        <>
          <MonitoringStatCards items={stats} ariaLabel={`Resumo do dia de ${workCenter}`} />

          <section className="delpi-mes-panel" aria-labelledby="delpi-mes-wc-daybar-title">
            <header className="delpi-mes-panel__head">
              <div>
                <h3 id="delpi-mes-wc-daybar-title">Linha do tempo do dia</h3>
                <p>Visualize os períodos de produção e parada da máquina ao longo do dia atual.</p>
              </div>
              <ul className="delpi-mes-daybar__legend" aria-hidden="true">
                <li><i className="delpi-mes-daybar__dot delpi-mes-daybar__dot--producing" />Produzindo</li>
                <li><i className="delpi-mes-daybar__dot delpi-mes-daybar__dot--stopped" />Parado</li>
                <li><i className="delpi-mes-daybar__dot delpi-mes-daybar__dot--inactive" />Sem atividade</li>
              </ul>
            </header>
            <DayTimelineBar segments={segments} fromIso={timeline.from} nowMs={nowMs} />
          </section>

          <div className="delpi-mes-wc__columns">
            <section className="delpi-mes-panel" aria-labelledby="delpi-mes-wc-reasons-title">
              <header className="delpi-mes-panel__head">
                <div>
                  <h3 id="delpi-mes-wc-reasons-title">Motivos de parada no dia</h3>
                  <p>Tempo total de parada por motivo.</p>
                </div>
              </header>
              {reasons.length === 0 ? (
                <p className="delpi-mes-panel__empty">Nenhuma parada registrada no período.</p>
              ) : (
                <ul className="delpi-mes-reasons">
                  {reasons.map((reason, index) => (
                    <li key={reason.label}>
                      <span className="delpi-mes-reasons__label">{reason.label}</span>
                      <span className="delpi-mes-reasons__bar">
                        <span
                          className={index === 0 ? "delpi-mes-reasons__fill delpi-mes-reasons__fill--danger" : "delpi-mes-reasons__fill"}
                          style={{ width: `${maxReasonSec > 0 ? Math.max(4, Math.round((reason.seconds / maxReasonSec) * 100)) : 0}%` }}
                        />
                      </span>
                      <strong>{formatHoursMinutes(reason.seconds)}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="delpi-mes-panel" aria-labelledby="delpi-mes-wc-events-title">
              <header className="delpi-mes-panel__head">
                <div>
                  <h3 id="delpi-mes-wc-events-title">Eventos do dia</h3>
                  <p>Todos os períodos de produção, parada e sem atividade.</p>
                </div>
                <label className="delpi-mes-events-filter">
                  Status
                  <select value={eventStatus} onChange={(event) => setEventStatus(event.target.value)} aria-label="Filtrar eventos por status">
                    <option value="all">Todos</option>
                    {eventStates.map((state) => (
                      <option key={state} value={state}>
                        {state === "inactive" ? "Sem atividade" : presentDayState(state).label}
                      </option>
                    ))}
                  </select>
                </label>
              </header>
              <div className="delpi-mes-events">
                <table>
                  <thead>
                    <tr><th>Início</th><th>Fim</th><th>Duração</th><th>Status</th><th>Motivo</th></tr>
                  </thead>
                  <tbody>
                    {visibleSegments.map((segment, index) => {
                      const presentation = segment.item ? presentDayEvent(segment.item) : null;
                      const label = presentation?.label ?? "Sem atividade";
                      const reason = segment.item
                        ? (presentation?.pendingReason ? "Motivo pendente" : downtimeReasonDisplay(segment.item.downtime) ?? (segment.state === "stopped" ? "Sem motivo informado" : "—"))
                        : "—";
                      return (
                        <tr key={segment.item?.stateEventId ?? `gap-${index}`}>
                          <td>{formatDayClock(segment.startMs)}</td>
                          <td>{segment.item && segment.item.endedAt === null && segment.endMs >= nowMs ? "agora" : formatDayClock(segment.endMs)}</td>
                          <td>{formatHoursMinutes((segment.endMs - segment.startMs) / 1000)}</td>
                          <td><span className={`delpi-mes-event-state delpi-mes-event-state--${STATE_ROW_CLASS[segment.state] ?? "info"}`}>{label}</span></td>
                          <td>{reason}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </>
      ) : null}
    </section>
  );
}
