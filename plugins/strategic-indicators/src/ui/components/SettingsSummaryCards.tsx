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

  return (
    <div className="si-settings-summary-grid">
      <article className="si-settings-summary-card">
        <span className="si-settings-summary-card__label">Peso total do IGD</span>
        <strong className="si-settings-summary-card__value">
          {totalWeight}%
        </strong>
        <p className="si-settings-summary-card__text">
          Soma consolidada dos pesos oficiais dos departamentos no índice global.
        </p>
      </article>

      <article className="si-settings-summary-card">
        <span className="si-settings-summary-card__label">Metas resumidas</span>
        <strong className="si-settings-summary-card__value">
          {totalGoals}
        </strong>
        <p className="si-settings-summary-card__text">
          Quantidade de áreas com meta executiva sintetizada nesta fase.
        </p>
      </article>

      <article className="si-settings-summary-card">
        <span className="si-settings-summary-card__label">Governança ativa</span>
        <div className="si-settings-summary-card__badges">
          <StatusBadge label={`${totalGovernanceItems} parâmetros`} variant="neutral" />
          <StatusBadge label="Modo administrativo" variant="info" />
        </div>
        <p className="si-settings-summary-card__text">
          Leitura rápida do estado administrativo atual do módulo.
        </p>
      </article>
    </div>
  );
}