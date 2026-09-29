import { DrawerShell, Timeline, drawerShellBemClasses, timelineBemClasses } from "@delpi/plugin-ui/index";
import type { BranchCode } from "../../constants/routes";
import type { MonitoringItem } from "../../types/mes";
import { useWorkCenterTimeline } from "../../hooks/useWorkCenterTimeline";
import { elapsedSeconds, formatDuration } from "../../utils/duration";
import { presentMonitoringState, runStateSignature } from "../../utils/monitoringPresentation";
import { dayEventContext, dayEventDurationSeconds, dayEventReason, formatDayEventRange, presentDayEvent } from "../../utils/dayTimeline";

const drawerClasses = drawerShellBemClasses("delpi-mes");
const timelineClasses = timelineBemClasses("delpi-mes");

export function RunDetailDrawer({ item, branch, nowMs, canViewHistory, onClose }: { item: MonitoringItem | null; branch: BranchCode; nowMs: number; canViewHistory: boolean; onClose: () => void }) {
  const signature = item ? runStateSignature(item) : null;
  const history = useWorkCenterTimeline(branch, item?.workCenter ?? null, signature, canViewHistory && Boolean(item));
  const state = item ? presentMonitoringState(item) : null;
  const timeline = history.data;
  const dayItems = timeline?.items.map((entry) => {
    const presentation = presentDayEvent(entry);
    const range = formatDayEventRange(entry, timeline.from, timeline.to, nowMs);
    const duration = formatDuration(dayEventDurationSeconds(entry, timeline.from, timeline.to, nowMs));
    return {
      id: entry.stateEventId,
      title: presentation.label,
      occurredAt: entry.startedAt,
      timeLabel: `${range} · ${duration}`,
      detail: dayEventReason(entry, presentation) ?? undefined,
      meta: dayEventContext(entry) || undefined,
      tone: presentation.tone,
    };
  }) ?? [];
  return <DrawerShell open={Boolean(item)} title={item ? `${item.workCenter} · Run atual` : "Run atual"} description={state?.label} onClose={onClose} classNames={drawerClasses} portalScopeClassName="delpi-mes-shell" closeOnBackdropClick>
    {item ? <div className="delpi-mes-detail">
      <dl><div><dt>Estado atual</dt><dd>{state?.actionLabel} há {formatDuration(elapsedSeconds(item.stateStartedAt, nowMs))}</dd></div><div><dt>OP / operação</dt><dd>{item.productionOrder || "—"} / {item.operationCode || "—"}</dd></div><div><dt>Operador</dt><dd>{item.operatorName || "Operador não identificado"}</dd></div><div><dt>Peças</dt><dd>{item.piecesTotal}{item.targetPieces ? ` / ${item.targetPieces}` : ""}</dd></div><div><dt>Parada atual</dt><dd>{item.downtime?.reasonLabel || (item.downtime ? "Motivo pendente" : "Não registrada")}</dd></div><div><dt>Integridade</dt><dd>{item.integrityStatus === "complete" ? "Completa" : "Dados incompletos"}</dd></div></dl>
      {canViewHistory ? <section><h3>Histórico do dia</h3>{history.error ? <p role="alert">{history.error} <button type="button" onClick={history.retry}>Tentar novamente</button></p> : null}<Timeline items={dayItems} loading={history.loading} emptyMessage="Nenhum evento registrado hoje." classNames={timelineClasses} prefix="delpi-mes" aria-label={`Histórico do dia de ${item.workCenter}`} /></section> : <p className="delpi-mes-detail__history-disabled">Histórico não disponível para o seu perfil.</p>}
    </div> : null}
  </DrawerShell>;
}
