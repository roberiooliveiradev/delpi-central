import type { AlertsDashboardViewData } from "../../data/types/alerts";
import { StatusBadge } from "./StatusBadge";

type AlertsExecutiveActionProps = {
  data: AlertsDashboardViewData;
};

function getTopExecutiveAction(data: AlertsDashboardViewData) {
  const firstExecutive = data.executiveAlerts[0];
  const firstDepartment = data.departmentAlerts[0];
  const firstIndicator = data.indicatorAlerts[0];

  return {
    title: firstExecutive?.title ?? "Sem alerta principal",
    recommendation:
      firstExecutive?.recommendation ??
      "Nenhuma recomendação prioritária disponível.",
    department: firstDepartment?.departmentName ?? "—",
    indicator: firstIndicator?.indicatorName ?? "—",
  };
}

export function AlertsExecutiveAction({
  data,
}: AlertsExecutiveActionProps) {
  const action = getTopExecutiveAction(data);

  return (
    <section className="si-alert-executive-action">
      <div className="si-alert-executive-action__header">
        <div>
          <p className="si-alert-executive-action__eyebrow">
            Ação executiva recomendada
          </p>
          <h3 className="si-alert-executive-action__title">{action.title}</h3>
        </div>

        <StatusBadge label="Prioridade do painel" variant="warning" />
      </div>

      <p className="si-alert-executive-action__description">
        {action.recommendation}
      </p>

      <div className="si-alert-executive-action__meta">
        <div className="si-alert-executive-action__meta-item">
          <span>Área prioritária</span>
          <strong>{action.department}</strong>
        </div>

        <div className="si-alert-executive-action__meta-item">
          <span>Indicador crítico</span>
          <strong>{action.indicator}</strong>
        </div>
      </div>
    </section>
  );
}