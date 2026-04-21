import type { ExecutiveAlertViewItem } from "../../data/types/alerts";
import { getSeverityLabel } from "../presentation/labels";

type PresentationAlertsBoardProps = {
  alerts: ExecutiveAlertViewItem[];
};

function getSeverityVariant(severity: "high" | "medium" | "low") {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "neutral";
}

export function PresentationAlertsBoard({
  alerts,
}: PresentationAlertsBoardProps) {
  if (!alerts.length) {
    return (
      <section className="si-presentation-alerts-board si-presentation-scene-card">
        <div className="si-presentation-state">
          <h2>Sem alertas executivos</h2>
          <p>Não há alertas relevantes para exibição nesta competência.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="si-presentation-alerts-board">
      {alerts.map((alert, index) => (
        <article
          key={alert.id}
          className="si-presentation-alert-card si-presentation-scene-card"
        >
          <div className="si-presentation-alert-card__header">
            <div className="si-presentation-alert-card__header-main">
              <span className="si-presentation-alert-card__index">
                Alerta {String(index + 1).padStart(2, "0")}
              </span>

              <h3>{alert.title}</h3>
            </div>

            <span
              className={`si-status-badge si-status-badge--${getSeverityVariant(
                alert.severity,
              )}`}
            >
              {getSeverityLabel(alert.severity)}
            </span>
          </div>

          <div className="si-presentation-alert-card__body">
            <div className="si-presentation-alert-card__block">
              <span>Impacto</span>
              <p>{alert.impact}</p>
            </div>

            <div className="si-presentation-alert-card__block">
              <span>Recomendação</span>
              <p>{alert.recommendation}</p>
            </div>
          </div>
        </article>
      ))}
    </section>
  );
}