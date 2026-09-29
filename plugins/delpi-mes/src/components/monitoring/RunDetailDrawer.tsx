import { DrawerShell, Timeline, drawerShellBemClasses, timelineBemClasses } from "@delpi/plugin-ui/index";
import type { MonitoringItem } from "../../types/mes";
import { useRunTimeline } from "../../hooks/useRunTimeline";
import { elapsedSeconds, formatDuration } from "../../utils/duration";
import { presentMonitoringState, runStateSignature } from "../../utils/monitoringPresentation";
import { liveTimelineSummary } from "../../utils/timelineSummary";

const drawerClasses = drawerShellBemClasses("delpi-mes");
const timelineClasses = timelineBemClasses("delpi-mes");

export function RunDetailDrawer({ item, nowMs, canViewHistory, onClose }: { item: MonitoringItem | null; nowMs: number; canViewHistory: boolean; onClose: () => void }) {
  const signature = item ? runStateSignature(item) : null;
  const timeline = useRunTimeline(item?.runId ?? null, signature, canViewHistory);
  const state = item ? presentMonitoringState(item) : null;
  const timelineItems = timeline.data?.items.map((entry) => ({ id: entry.id, title: entry.state === "producing" ? "Produzindo" : "Parada", occurredAt: entry.startedAt, timeLabel: formatDuration(entry.durationSeconds + (entry.endedAt === null ? Math.max(0, Math.floor((nowMs - Date.parse(timeline.data!.referenceAt)) / 1000)) : 0)), detail: entry.downtime?.reasonLabel || (entry.state === "stopped" ? "Motivo não informado" : undefined), tone: entry.state === "producing" ? "success" as const : "warning" as const })) ?? [];
  const liveSummary = timeline.data ? liveTimelineSummary(timeline.data, nowMs) : null;
  return <DrawerShell open={Boolean(item)} title={item ? `${item.workCenter} · Run atual` : "Run atual"} description={state?.label} onClose={onClose} classNames={drawerClasses} portalScopeClassName="delpi-mes-shell" closeOnBackdropClick>
    {item ? <div className="delpi-mes-detail">
      <dl><div><dt>Estado atual</dt><dd>{state?.actionLabel} há {formatDuration(elapsedSeconds(item.stateStartedAt, nowMs))}</dd></div><div><dt>OP / operação</dt><dd>{item.productionOrder || "—"} / {item.operationCode || "—"}</dd></div><div><dt>Operador</dt><dd>{item.operatorName || "Operador não identificado"}</dd></div><div><dt>Peças</dt><dd>{item.piecesTotal}{item.targetPieces ? ` / ${item.targetPieces}` : ""}</dd></div><div><dt>Parada atual</dt><dd>{item.downtime?.reasonLabel || (item.downtime ? "Motivo pendente" : "Não registrada")}</dd></div><div><dt>Integridade</dt><dd>{item.integrityStatus === "complete" ? "Completa" : "Dados incompletos"}</dd></div></dl>
      {canViewHistory ? <section><h3>Timeline do run</h3>{timeline.error ? <p role="alert">{timeline.error}</p> : null}{liveSummary ? <div className="delpi-mes-detail__summary"><span>Decorrido <strong>{formatDuration(liveSummary.elapsedSeconds)}</strong></span><span>Produzindo <strong>{formatDuration(liveSummary.producingSeconds)}</strong></span><span>Parado <strong>{formatDuration(liveSummary.stoppedSeconds)}</strong></span><span>Paradas <strong>{liveSummary.stopCount}</strong></span></div> : null}<Timeline items={timelineItems} loading={timeline.loading} emptyMessage="Nenhum evento disponível." classNames={timelineClasses} prefix="delpi-mes" aria-label="Timeline do run" /></section> : <p className="delpi-mes-detail__history-disabled">Histórico não disponível para o seu perfil.</p>}
    </div> : null}
  </DrawerShell>;
}
