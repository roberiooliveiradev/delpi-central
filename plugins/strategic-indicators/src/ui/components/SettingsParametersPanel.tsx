import type { SettingsParameterItem } from "../../data/mocks/settingsMock";

type SettingsParametersPanelProps = {
  items: SettingsParameterItem[];
};

export function SettingsParametersPanel({
  items,
}: SettingsParametersPanelProps) {
  return (
    <section className="si-settings-panel">
      <div className="si-settings-panel__header">
        <h3 className="si-settings-panel__title">Parâmetros globais</h3>
        <span className="si-settings-panel__subtitle">
          leitura estrutural do módulo
        </span>
      </div>

      <div className="si-settings-governance-grid">
        {items.map((item) => (
          <article key={item.id} className="si-settings-governance-card">
            <span className="si-settings-governance-card__label">
              {item.label}
            </span>
            <strong className="si-settings-governance-card__value">
              {item.value}
            </strong>
            <p className="si-settings-governance-card__text">
              {item.observation}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}