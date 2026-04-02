import type { IndicatorAlert } from "../../data/mocks/alertsMock";
import { StatusBadge } from "./StatusBadge";

type CriticalIndicatorListProps = {
  alerts: IndicatorAlert[];
};

function getVariant(severity: IndicatorAlert["severity"]) {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "neutral";
}

function getLabel(severity: IndicatorAlert["severity"]) {
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
            <span>Meta 2026: {alert.goal2026}</span>
          </div>

          <p className="si-critical-item__recommendation">
            {alert.recommendation}
          </p>
        </article>
      ))}
    </div>
  );
}