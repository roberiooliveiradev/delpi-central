import type { ExecutiveAlert } from "../../data/mocks/alertsMock";
import { StatusBadge } from "./StatusBadge";

type TopAlertHighlightProps = {
  alert: ExecutiveAlert | null;
};

function getVariant(severity: ExecutiveAlert["severity"]) {
  if (severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "neutral";
}

function getLabel(severity: ExecutiveAlert["severity"]) {
  if (severity === "high") return "Alta criticidade";
  if (severity === "medium") return "Média criticidade";
  return "Baixa criticidade";
}

export function TopAlertHighlight({
  alert,
}: TopAlertHighlightProps) {
  if (!alert) {
    return (
      <div className="si-top-alert-highlight si-top-alert-highlight--empty">
        Nenhum alerta principal disponível.
      </div>
    );
  }

  return (
    <article className="si-top-alert-highlight">
      <div className="si-top-alert-highlight__top">
        <span className="si-top-alert-highlight__label">
          Alerta principal do recorte
        </span>
        <StatusBadge
          label={getLabel(alert.severity)}
          variant={getVariant(alert.severity)}
        />
      </div>

      <h3 className="si-top-alert-highlight__title">{alert.title}</h3>
      <p className="si-top-alert-highlight__impact">{alert.impact}</p>
      <p className="si-top-alert-highlight__recommendation">
        {alert.recommendation}
      </p>
    </article>
  );
}