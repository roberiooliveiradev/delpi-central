import type { SettingsDashboardData } from "../../data/types/settingsDashboard";
import { StatusBadge } from "./StatusBadge";

type SettingsSummaryCardsProps = {
  data: SettingsDashboardData;
};

function getTotalWeight(data: SettingsDashboardData) {
  return data.weights.reduce((sum, item) => sum + item.weightPct, 0);
}

export function SettingsSummaryCards({
  data,
}: SettingsSummaryCardsProps) {
  const totalWeight = getTotalWeight(data);
  const totalGoals = data.goals.length;
  const totalGovernanceItems = data.governance.length;
  const totalParameters = data.parameters.length;

  return (
    <div className="si-settings-summary-grid">
      <article className="si-settings-summary-card">
        <span className="si-settings-summary-card__label">
          Estrutura executiva
        </span>
        <strong className="si-settings-summary-card__value">
          {data.weights.length}
        </strong>
        <p className="si-settings-summary-card__text">
          Departamentos atualmente refletidos na visão administrativa do módulo.
        </p>
      </article>

      <article className="si-settings-summary-card">
        <span className="si-settings-summary-card__label">
          Cobertura estratégica
        </span>
        <div className="si-settings-summary-card__badges">
          <StatusBadge label={`${totalGoals} metas`} variant="info" />
          <StatusBadge label={`${totalWeight}% IGD`} variant="neutral" />
        </div>
        <p className="si-settings-summary-card__text">
          Leitura rápida da distribuição executiva disponível na camada de painel.
        </p>
      </article>

      <article className="si-settings-summary-card">
        <span className="si-settings-summary-card__label">
          Configuração global
        </span>
        <div className="si-settings-summary-card__badges">
          <StatusBadge label={`${totalParameters} parâmetros`} variant="neutral" />
          <StatusBadge label={`${totalGovernanceItems} itens de governança`} variant="success" />
        </div>
        <p className="si-settings-summary-card__text">
          Itens globais atualmente administráveis no backend do módulo.
        </p>
      </article>
    </div>
  );
}