import type { DepartmentAlertViewItem } from "../../data/types/alerts";
import { StatusBadge } from "./StatusBadge";

type CriticalDepartmentListProps = {
  alerts: DepartmentAlertViewItem[];
};

function getVariant(severity: DepartmentAlertViewItem["severity"]) {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "neutral";
}

function getLabel(severity: DepartmentAlertViewItem["severity"]) {
  if (severity === "high") return "Alta criticidade";
  if (severity === "medium") return "Média criticidade";
  return "Baixa criticidade";
}

export function CriticalDepartmentList({
  alerts,
}: CriticalDepartmentListProps) {
  if (!alerts.length) {
    return (
      <div className="si-critical-list si-critical-list--empty">
        Nenhum departamento crítico encontrado no recorte atual.
      </div>
    );
  }

  return (
    <div className="si-critical-list">
      {alerts.map((alert) => (
        <article key={alert.id} className="si-critical-item">
          <div className="si-critical-item__top">
            <div>
              <h3 className="si-critical-item__title">{alert.departmentName}</h3>
              <p className="si-critical-item__subtitle">{alert.reason}</p>
            </div>

            <StatusBadge
              label={getLabel(alert.severity)}
              variant={getVariant(alert.severity)}
            />
          </div>

          <div className="si-critical-item__metrics">
            <span>Atual: {alert.currentScore.toFixed(1)}</span>
            <span>Anterior: {alert.previousScore.toFixed(1)}</span>
          </div>

          <p className="si-critical-item__recommendation">
            {alert.recommendation}
          </p>
        </article>
      ))}
    </div>
  );
}