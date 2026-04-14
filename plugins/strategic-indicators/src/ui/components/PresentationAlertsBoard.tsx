import type { ExecutiveAlertViewItem } from "../../data/types/alerts";
import { getSeverityLabel } from "../../ui/presentation/labels";

type PresentationAlertsBoardProps = {
  alerts: ExecutiveAlertViewItem[];
};

function getSeverityVariant(severity: ExecutiveAlertViewItem["severity"]) {
  if (severity === "high") return "warning";
  if (severity === "medium") return "neutral";
  return "success";
}

export function PresentationAlertsBoard({
  alerts,
}: PresentationAlertsBoardProps) {
  const topAlerts = alerts.slice(0, 3);
  const criticalCount = alerts.filter((alert) => alert.severity === "high").length;

  return (
    <section className="si-presentation-board">
      <div className="si-presentation-board__header">
        <h2 className="si-presentation-board__title">Prioridades executivas</h2>
        <span className="si-presentation-board__subtitle">
          foco imediato para tomada de decisão
        </span>
      </div>

      <div className="si-presentation-board__summary-grid">
        <article className="si-presentation-board__summary-card">
          <span>Total de alertas destacados</span>
          <strong>{topAlerts.length}</strong>
          <p>Alertas executivos priorizados para a apresentação.</p>
        </article>

        <article className="si-presentation-board__summary-card">
          <span>Alertas de alta severidade</span>
          <strong>{criticalCount}</strong>
          <p>Itens que exigem acompanhamento mais próximo da liderança.</p>
        </article>
      </div>

      <div className="si-presentation-alert-list">
        {topAlerts.map((alert) => (
          <article
            key={alert.id}
            className="si-presentation-alert-card"
            data-variant={getSeverityVariant(alert.severity)}
          >
            <h3>{alert.title}</h3>

            <p>
              <strong>Severidade:</strong> {getSeverityLabel(alert.severity)}
            </p>

            <p>{alert.impact}</p>

            <div className="si-presentation-alert-card__recommendation">
              <strong>Recomendação</strong>
              <p>{alert.recommendation}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}