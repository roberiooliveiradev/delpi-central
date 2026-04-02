import type { SettingsGoalItem } from "../../data/mocks/settingsMock";

type SettingsGoalsPanelProps = {
  items: SettingsGoalItem[];
};

export function SettingsGoalsPanel({
  items,
}: SettingsGoalsPanelProps) {
  return (
    <section className="si-settings-panel">
      <div className="si-settings-panel__header">
        <h3 className="si-settings-panel__title">Metas executivas resumidas</h3>
        <span className="si-settings-panel__subtitle">
          referência de metas 2026 por área
        </span>
      </div>

      <div className="si-settings-list">
        {items.map((item) => (
          <article key={item.id} className="si-settings-item">
            <div className="si-settings-item__top">
              <h4 className="si-settings-item__title">{item.departmentName}</h4>
              <strong className="si-settings-item__goal">
                {item.headlineGoal}
              </strong>
            </div>

            <p className="si-settings-item__text">{item.supportingFocus}</p>
          </article>
        ))}
      </div>
    </section>
  );
}