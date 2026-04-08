import type { ExecutiveAlertViewItem } from "../../data/types/alerts";
import { StatusBadge } from "./StatusBadge";

type ExecutiveAlertsListProps = {
  alerts: ExecutiveAlertViewItem[];
};

function getVariant(severity: ExecutiveAlertViewItem["severity"]) {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "neutral";
}

function getLabel(severity: ExecutiveAlertViewItem["severity"]) {
  if (severity === "high") return "Alta criticidade";
  if (severity === "medium") return "Média criticidade";
  return "Baixa criticidade";
}

export function ExecutiveAlertsList({
  alerts,
}: ExecutiveAlertsListProps) {
  if (!alerts.length) {
    return (
      <div className="si-critical-list si-critical-list--empty">
        Nenhum alerta executivo encontrado no recorte atual.
      </div>
    );
  }

  return (
    <div className="si-critical-list">
      {alerts.map((alert) => (
        <article key={alert.id} className="si-critical-item">
          <div className="si-critical-item__top">
            <div>
              <h3 className="si-critical-item__title">{alert.title}</h3>
              <p className="si-critical-item__subtitle">{alert.impact}</p>
            </div>

            <StatusBadge
              label={getLabel(alert.severity)}
              variant={getVariant(alert.severity)}
            />
          </div>

          <p className="si-critical-item__recommendation">
            {alert.recommendation}
          </p>
        </article>
      ))}
    </div>
  );
}