import { ClipboardList, Gauge, MonitorCog, Package, Target, User } from "lucide-react";
import type { MonitoringItem } from "../../types/mes";
import { workCenterImageUrl } from "../../utils/assets";
import { elapsedSeconds, formatDuration } from "../../utils/duration";
import { downtimeReasonDisplay, isPendingReason, presentMonitoringState, progressPercent } from "../../utils/monitoringPresentation";

export function WorkCenterCard({ item, nowMs, onOpen }: { item: MonitoringItem; nowMs: number; onOpen: () => void }) {
  const state = presentMonitoringState(item);
  const progress = progressPercent(item);
  const imageUrl = workCenterImageUrl(item.workCenter);
  const durationLabel = `${state.actionLabel} há ${formatDuration(elapsedSeconds(item.stateStartedAt, nowMs))}`;

  return (
    <button
      type="button"
      className={`delpi-mes-work-center-card delpi-mes-work-center-card--${state.tone}`}
      onClick={onOpen}
      aria-label={`Abrir detalhes do centro ${item.workCenter}`}
    >
      <div className="delpi-mes-work-center-card__identity">
        <span className="delpi-mes-work-center-card__icon" aria-hidden="true"><MonitorCog /></span>
        <div className="delpi-mes-work-center-card__info">
          <strong>{item.workCenter}</strong>
          <span className={`delpi-mes-work-center-card__status delpi-mes-work-center-card__status--${state.tone}`}>
            <span className="delpi-mes-status-dot" aria-hidden="true" />
            {durationLabel}
          </span>
          {state.secondary ? <span className="delpi-mes-work-center-card__secondary">{state.secondary}</span> : null}
          <span className="delpi-mes-work-center-card__line">
            <ClipboardList aria-hidden="true" />
            OP {item.productionOrder || "não informada"} · Op. {item.operationCode || "—"}
          </span>
          <span className="delpi-mes-work-center-card__line">
            <User aria-hidden="true" />
            {item.operatorName || "Operador não identificado"}
          </span>
          {item.downtime ? (
            <span className="delpi-mes-work-center-card__downtime">
              {isPendingReason(item) ? "Motivo pendente" : downtimeReasonDisplay(item.downtime) || "Parada sem motivo informado"}
            </span>
          ) : item.operationalState === "stopped" ? (
            <span className="delpi-mes-work-center-card__secondary">Parada sem evento associado</span>
          ) : null}
        </div>
      </div>

      <div className="delpi-mes-work-center-card__production">
        <span className="delpi-mes-work-center-card__prod-label">Produção</span>
        <span className="delpi-mes-work-center-card__prod-value">
          {item.piecesTotal}
          <small> /{item.targetPieces ? `${item.targetPieces} peças` : " peças"}</small>
          {progress !== null ? <em>{progress}%</em> : null}
        </span>
        <span className="delpi-mes-work-center-card__bar" role="presentation">
          <span style={{ width: `${progress !== null ? Math.min(progress, 100) : 0}%` }} />
        </span>
        <div className="delpi-mes-work-center-card__tiles">
          <span><Target aria-hidden="true" />Meta<strong>{item.targetPieces ? `${item.targetPieces} peças` : "—"}</strong></span>
          <span><Package aria-hidden="true" />Produzidas<strong>{item.piecesTotal} peças</strong></span>
          <span><Gauge aria-hidden="true" />Performance<strong>{progress !== null ? `${progress}%` : "—"}</strong></span>
        </div>
      </div>

      <div className="delpi-mes-work-center-card__media">
        {imageUrl ? (
          <img src={imageUrl} alt="" aria-hidden="true" loading="lazy" />
        ) : (
          <span className="delpi-mes-work-center-card__media-placeholder" aria-hidden="true"><MonitorCog /></span>
        )}
        <span className={`delpi-mes-work-center-card__badge delpi-mes-work-center-card__badge--${state.tone}`}>
          <span className="delpi-mes-status-dot" aria-hidden="true" />
          {state.label}
        </span>
      </div>
    </button>
  );
}
