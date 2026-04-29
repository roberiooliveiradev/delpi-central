import type { DepartmentAlertViewItem } from "../../data/types/alerts";
import { StatusBadge } from "./StatusBadge";
import "./CriticalDepartmentList.css";

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

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatVariation(value: number) {
  const formatted = Math.abs(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  if (value > 0) return `+${formatted}`;
  if (value < 0) return `-${formatted}`;
  return "0,0";
}

function getVariationLabel(value: number) {
  if (value > 0) return "Melhora";
  if (value < 0) return "Queda";
  return "Estável";
}

function getVariationClassName(value: number) {
  if (value > 0) return "si-critical-item__variation si-critical-item__variation--up";
  if (value < 0) return "si-critical-item__variation si-critical-item__variation--down";
  return "si-critical-item__variation si-critical-item__variation--stable";
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
            <span>Atual: {formatScore(alert.currentScore)}</span>
            <span>Anterior: {formatScore(alert.previousScore)}</span>
            <span className={getVariationClassName(alert.variation)}>
              Variação: {formatVariation(alert.variation)} (
              {getVariationLabel(alert.variation)})
            </span>
          </div>

          <p className="si-critical-item__recommendation">
            {alert.recommendation}
          </p>
        </article>
      ))}
    </div>
  );
}