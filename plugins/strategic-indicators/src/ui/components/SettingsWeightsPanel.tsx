import type { SettingsDashboardWeightItem } from "../../data/types/settingsDashboard";
import "./SettingsWeightsPanel.css";

type SettingsWeightsPanelProps = {
  items: SettingsDashboardWeightItem[];
};

export function SettingsWeightsPanel({
  items,
}: SettingsWeightsPanelProps) {
  return (
    <section className="si-settings-panel">
      <div className="si-settings-panel__header">
        <h3 className="si-settings-panel__title">Pesos oficiais do IGD</h3>
        <span className="si-settings-panel__subtitle">
          composição governada do índice global
        </span>
      </div>

      <div className="si-settings-list">
        {items.map((item) => (
          <article key={item.id} className="si-settings-item">
            <div className="si-settings-item__top">
              <h4 className="si-settings-item__title">{item.departmentName}</h4>
              <strong className="si-settings-item__badge">
                {item.weightPct}%
              </strong>
            </div>

            <p className="si-settings-item__text">{item.note}</p>
          </article>
        ))}
      </div>
    </section>
  );
}