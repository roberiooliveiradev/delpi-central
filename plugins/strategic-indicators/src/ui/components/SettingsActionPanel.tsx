import type { SettingsDashboardData } from "../../data/types/settingsDashboard";

type SettingsActionPanelProps = {
  data: SettingsDashboardData;
};

export function SettingsActionPanel({
  data,
}: SettingsActionPanelProps) {
  const topGovernance = data.governance[0];
  const topReadiness = data.readiness.find((item) => item.status === "planned");
  const topGoal = data.goals[0];

  return (
    <section className="si-settings-action-panel">
      <div className="si-settings-action-panel__header">
        <h3 className="si-settings-action-panel__title">
          Próxima ação administrativa
        </h3>
        <span className="si-settings-action-panel__subtitle">
          fechamento do MVP de governança
        </span>
      </div>

      <div className="si-settings-action-panel__content">
        <article className="si-settings-action-panel__card">
          <span className="si-settings-action-panel__label">
            Governança atual
          </span>
          <strong className="si-settings-action-panel__value">
            {topGovernance?.value ?? "—"}
          </strong>
          <p className="si-settings-action-panel__text">
            {topGovernance?.observation ?? "Sem observação disponível."}
          </p>
        </article>

        <article className="si-settings-action-panel__card">
          <span className="si-settings-action-panel__label">
            Próxima evolução
          </span>
          <strong className="si-settings-action-panel__value">
            {topReadiness?.title ?? "—"}
          </strong>
          <p className="si-settings-action-panel__text">
            {topReadiness?.description ?? "Sem evolução planejada no recorte atual."}
          </p>
        </article>

        <article className="si-settings-action-panel__card">
          <span className="si-settings-action-panel__label">
            Referência de meta
          </span>
          <strong className="si-settings-action-panel__value">
            {topGoal?.headlineGoal ?? "—"}
          </strong>
          <p className="si-settings-action-panel__text">
            {topGoal?.supportingFocus ?? "Sem meta resumida disponível."}
          </p>
        </article>
      </div>
    </section>
  );
}