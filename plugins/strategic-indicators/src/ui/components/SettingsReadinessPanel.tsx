import type { SettingsReadinessItem } from "../../data/types/settingsDashboard";
import { StatusBadge } from "./StatusBadge";

type SettingsReadinessPanelProps = {
  items: SettingsReadinessItem[];
};

function getVariant(status: SettingsReadinessItem["status"]) {
  if (status === "ready") return "success";
  if (status === "planned") return "info";
  return "neutral";
}

function getLabel(status: SettingsReadinessItem["status"]) {
  if (status === "ready") return "Pronto";
  if (status === "planned") return "Planejado";
  return "Simulado";
}

export function SettingsReadinessPanel({
  items,
}: SettingsReadinessPanelProps) {
  return (
    <section className="si-settings-panel">
      <div className="si-settings-panel__header">
        <h3 className="si-settings-panel__title">Prontidão administrativa</h3>
        <span className="si-settings-panel__subtitle">
          estado atual da governança do módulo
        </span>
      </div>

      <div className="si-settings-list">
        {items.map((item) => (
          <article key={item.id} className="si-settings-item">
            <div className="si-settings-item__top">
              <h4 className="si-settings-item__title">{item.title}</h4>
              <StatusBadge
                label={getLabel(item.status)}
                variant={getVariant(item.status)}
              />
            </div>

            <p className="si-settings-item__text">{item.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}