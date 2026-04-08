import type { AlertsDashboardViewData } from "../../data/types/alerts";
import { StatusBadge } from "./StatusBadge";

type AlertsPriorityHighlightsProps = {
  data: AlertsDashboardViewData;
};

export function AlertsPriorityHighlights({
  data,
}: AlertsPriorityHighlightsProps) {
  const topDepartment = data.departmentAlerts[0] ?? null;
  const topIndicator = data.indicatorAlerts[0] ?? null;

  return (
    <div className="si-alert-highlights">
      <article className="si-alert-highlight-card">
        <div className="si-alert-highlight-card__top">
          <span className="si-alert-highlight-card__label">
            Área mais prioritária
          </span>
          <StatusBadge label="Foco executivo" variant="warning" />
        </div>

        {topDepartment ? (
          <>
            <h3 className="si-alert-highlight-card__title">
              {topDepartment.departmentName}
            </h3>
            <p className="si-alert-highlight-card__text">{topDepartment.reason}</p>
            <p className="si-alert-highlight-card__meta">
              Atual: {topDepartment.currentScore.toFixed(1)} · Anterior:{" "}
              {topDepartment.previousScore.toFixed(1)}
            </p>
          </>
        ) : null}
      </article>

      <article className="si-alert-highlight-card">
        <div className="si-alert-highlight-card__top">
          <span className="si-alert-highlight-card__label">
            Indicador mais crítico
          </span>
          <StatusBadge label="Ação prioritária" variant="danger" />
        </div>

        {topIndicator ? (
          <>
            <h3 className="si-alert-highlight-card__title">
              {topIndicator.indicatorName}
            </h3>
            <p className="si-alert-highlight-card__text">
              {topIndicator.departmentName} · {topIndicator.reason}
            </p>
            <p className="si-alert-highlight-card__meta">
              Nota: {topIndicator.simulatedScore.toFixed(1)} · Meta:{" "}
              {topIndicator.goalLabel}
            </p>
          </>
        ) : null}
      </article>
    </div>
  );
}