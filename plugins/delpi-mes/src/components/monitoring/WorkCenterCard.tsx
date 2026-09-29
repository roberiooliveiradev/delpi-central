import { InlineMeter, StatusBadge, inlineMeterBemClasses, statusBadgeBemClasses } from "@delpi/plugin-ui/index";
import type { MonitoringItem } from "../../types/mes";
import { elapsedSeconds, formatDuration } from "../../utils/duration";
import { isPendingReason, presentMonitoringState, progressPercent } from "../../utils/monitoringPresentation";

const meterClasses = inlineMeterBemClasses("delpi-mes");
const badgeClasses = statusBadgeBemClasses("delpi-mes");

export function WorkCenterCard({ item, nowMs, onOpen }: { item: MonitoringItem; nowMs: number; onOpen: () => void }) {
  const state = presentMonitoringState(item);
  const progress = progressPercent(item);
  const variant = state.tone === "neutral" ? "neutral" : state.tone;
  return (
    <button className={`delpi-mes-work-center-card delpi-mes-work-center-card--${state.tone}`} onClick={onOpen} aria-label={`Abrir detalhes do centro ${item.workCenter}`}>
      <span className="delpi-mes-work-center-card__head"><strong>{item.workCenter}</strong><StatusBadge label={state.label} variant={variant} classNames={badgeClasses} /></span>
      <span className="delpi-mes-work-center-card__duration">{state.actionLabel} há {formatDuration(elapsedSeconds(item.stateStartedAt, nowMs))}</span>
      {state.secondary ? <span className="delpi-mes-work-center-card__secondary">{state.secondary}</span> : null}
      <span className="delpi-mes-work-center-card__line">OP {item.productionOrder || "não informada"} · Op. {item.operationCode || "—"}</span>
      <span className="delpi-mes-work-center-card__line">{item.operatorName || "Operador não identificado"}</span>
      <span className="delpi-mes-work-center-card__count">{item.targetPieces ? `${item.piecesTotal} / ${item.targetPieces} peças` : `${item.piecesTotal} peças`}</span>
      {progress !== null ? <InlineMeter classNames={meterClasses} value={progress} max={100} tone="success" label={`${progress}%`} aria-label={`Progresso ${progress}%`} /> : <span className="delpi-mes-work-center-card__secondary">Meta não disponível</span>}
      {item.downtime ? <span className="delpi-mes-work-center-card__downtime">{isPendingReason(item) ? "Motivo pendente" : item.downtime.reasonLabel || "Parada sem motivo informado"}</span> : item.operationalState === "stopped" ? <span className="delpi-mes-work-center-card__secondary">Parada sem evento associado</span> : null}
    </button>
  );
}
