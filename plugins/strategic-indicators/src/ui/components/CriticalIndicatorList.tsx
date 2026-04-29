import type { IndicatorAlertViewItem } from "../../data/types/alerts";
import { StatusBadge } from "./StatusBadge";
import "./CriticalIndicatorList.css";

type CriticalIndicatorListProps = {
  alerts: IndicatorAlertViewItem[];
};

function getVariant(severity: IndicatorAlertViewItem["severity"]) {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "neutral";
}

function getLabel(severity: IndicatorAlertViewItem["severity"]) {
  if (severity === "high") return "Alta criticidade";
  if (severity === "medium") return "Média criticidade";
  return "Baixa criticidade";
}

export function CriticalIndicatorList({
  alerts,
}: CriticalIndicatorListProps) {
  if (!alerts.length) {
    return (
      <div className="si-critical-list si-critical-list--empty">
        Nenhum indicador crítico encontrado no recorte atual.
      </div>
    );
  }

  return (
    <div className="si-critical-list">
      {alerts.map((alert) => (
        <article key={alert.id} className="si-critical-item">
          <div className="si-critical-item__top">
            <div>
              <h3 className="si-critical-item__title">{alert.indicatorName}</h3>
              <p className="si-critical-item__subtitle">
                {alert.departmentName} · {alert.reason}
              </p>
            </div>

            <StatusBadge
              label={getLabel(alert.severity)}
              variant={getVariant(alert.severity)}
            />
          </div>

          <div className="si-critical-item__metrics">
            <span>Nota: {alert.simulatedScore.toFixed(1)}</span>
            <span>Meta: {alert.goalLabel}</span>
          </div>

          <p className="si-critical-item__recommendation">
            {alert.recommendation}
          </p>
        </article>
      ))}
    </div>
  );
}