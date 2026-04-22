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
  const criticalCount = alerts.filter((alert) => alert.severity === "high").length;

  return (
    <section className="si-presentation-board si-presentation-alerts-board-panel">
      <div className="si-presentation-board__header">
        <h2 className="si-presentation-board__title">Prioridades executivas</h2>
        <span className="si-presentation-board__subtitle">
          {alerts.length} alertas priorizados para apresentação
        </span>
      </div>

      <div className="si-presentation-board__summary-grid">
        <article className="si-presentation-board__summary-card">
          <span>Alertas executivos</span>
          <strong>{alerts.length}</strong>
          <p>Itens priorizados para leitura direta da diretoria.</p>
        </article>

        <article className="si-presentation-board__summary-card">
          <span>Alertas de alta severidade</span>
          <strong>{criticalCount}</strong>
          <p>Entre os alertas executivos priorizados.</p>
        </article>
      </div>

      <div className="si-presentation-alert-list si-presentation-alert-list--scrollable">
        {alerts.map((alert, index) => (
          <article
            key={alert.id}
            className="si-presentation-alert-card"
            data-variant={getSeverityVariant(alert.severity)}
          >
            <div className="si-presentation-alert-card__header">
              <div className="si-presentation-alert-card__header-main">
                <span className="si-presentation-alert-card__index">
                  Alerta {String(index + 1).padStart(2, "0")}
                </span>
                <h3>{alert.title}</h3>
              </div>

              <span className="si-presentation-alert-card__severity-pill">
                {getSeverityLabel(alert.severity)}
              </span>
            </div>

            <div className="si-presentation-alert-card__body">
              <div className="si-presentation-alert-card__block">
                <span>Impacto</span>
                <p>{alert.impact}</p>
              </div>

              <div className="si-presentation-alert-card__block si-presentation-alert-card__recommendation">
                <span>Recomendação</span>
                <p>{alert.recommendation}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}