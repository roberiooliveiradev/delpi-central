import type { SettingsDashboardData } from "../../data/types/settingsDashboard";
import { StatusBadge } from "./StatusBadge";

type SettingsExecutiveHighlightProps = {
  data: SettingsDashboardData;
};

function getTotalWeight(data: SettingsDashboardData) {
  return data.weights.reduce((sum, item) => sum + item.weightPct, 0);
}

export function SettingsExecutiveHighlight({
  data,
}: SettingsExecutiveHighlightProps) {
  const totalWeight = getTotalWeight(data);
  const mainParameter = data.parameters[0];
  const readinessReady = data.readiness.filter((item) => item.status === "ready").length;

  return (
    <section className="si-settings-executive-highlight">
      <div className="si-settings-executive-highlight__header">
        <div>
          <p className="si-settings-executive-highlight__eyebrow">
            Direcionamento administrativo
          </p>
          <h3 className="si-settings-executive-highlight__title">
            Governança estrutural dos Indicadores Estratégicos
          </h3>
        </div>

        <StatusBadge label="Módulo governado" variant="info" />
      </div>

      <p className="si-settings-executive-highlight__description">
        Nesta fase, a tela de configurações consolida os pesos oficiais do IGD,
        as metas executivas resumidas e a base administrativa necessária para
        futura persistência real.
      </p>

      <div className="si-settings-executive-highlight__grid">
        <div className="si-settings-executive-highlight__item">
          <span>Peso total governado</span>
          <strong>{totalWeight}%</strong>
        </div>

        <div className="si-settings-executive-highlight__item">
          <span>Parâmetro principal</span>
          <strong>{mainParameter?.value ?? "—"}</strong>
        </div>

        <div className="si-settings-executive-highlight__item">
          <span>Itens já prontos</span>
          <strong>{readinessReady}</strong>
        </div>
      </div>
    </section>
  );
}