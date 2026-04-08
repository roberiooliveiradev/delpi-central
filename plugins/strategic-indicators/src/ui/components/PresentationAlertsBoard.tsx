import type { ExecutiveAlertViewItem } from "../../data/types/alerts";

type PresentationAlertsBoardProps = {
  alerts: ExecutiveAlertViewItem[];
};

export function PresentationAlertsBoard({
  alerts,
}: PresentationAlertsBoardProps) {
  const topAlerts = alerts.slice(0, 3);

  return (
    <section className="si-presentation-board">
      <div className="si-presentation-board__header">
        <h2 className="si-presentation-board__title">Prioridades</h2>
        <span className="si-presentation-board__subtitle">
          foco executivo imediato
        </span>
      </div>

      <div className="si-presentation-alert-list">
        {topAlerts.map((alert) => (
          <article key={alert.id} className="si-presentation-alert-card">
            <h3>{alert.title}</h3>
            <p>{alert.impact}</p>
            <strong>{alert.recommendation}</strong>
          </article>
        ))}
      </div>
    </section>
  );
}