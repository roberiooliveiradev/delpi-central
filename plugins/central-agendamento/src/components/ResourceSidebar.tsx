import { Building2, Car, LayoutGrid, Presentation } from "lucide-react";

import type { SchedulingResource } from "../api/schedulingApi";
import {
  RESOURCE_TYPE_COLORS,
  RESOURCE_TYPES,
  type ResourceType,
} from "../constants/scheduling";

type Props = {
  resources: SchedulingResource[];
  bookingsCountToday: number;
  selectedTypes: ResourceType[];
  selectedResourceIds: string[];
  onToggleType: (type: ResourceType) => void;
  onToggleResource: (resourceId: string) => void;
  onClearFilters: () => void;
};

const TYPE_ICONS: Record<ResourceType, typeof Building2> = {
  meeting_room: Presentation,
  training_room: LayoutGrid,
  company_car: Car,
  other: Building2,
};

export function ResourceSidebar({
  resources,
  bookingsCountToday,
  selectedTypes,
  selectedResourceIds,
  onToggleType,
  onToggleResource,
  onClearFilters,
}: Props) {
  const hasFilters = selectedTypes.length > 0 || selectedResourceIds.length > 0;

  return (
    <aside className="ca-sidebar">
      <div className="ca-sidebar__stats">
        <div className="ca-stat-card">
          <span className="ca-stat-card__label">Recursos ativos</span>
          <strong className="ca-stat-card__value">{resources.length}</strong>
        </div>
        <div className="ca-stat-card">
          <span className="ca-stat-card__label">Reservas hoje</span>
          <strong className="ca-stat-card__value">{bookingsCountToday}</strong>
        </div>
      </div>

      <section className="ca-sidebar__section">
        <div className="ca-sidebar__section-head">
          <h2>Tipos</h2>
          {hasFilters ? (
            <button type="button" className="ca-link-btn" onClick={onClearFilters}>
              Limpar
            </button>
          ) : null}
        </div>
        <div className="ca-chip-row">
          {RESOURCE_TYPES.map((type) => {
            const Icon = TYPE_ICONS[type.value];
            const active = selectedTypes.includes(type.value);
            return (
              <button
                key={type.value}
                type="button"
                className={`ca-chip ${active ? "ca-chip--active" : ""}`}
                style={
                  active
                    ? { borderColor: RESOURCE_TYPE_COLORS[type.value] }
                    : undefined
                }
                onClick={() => onToggleType(type.value)}
              >
                <Icon size={14} />
                {type.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="ca-sidebar__section">
        <h2>Recursos</h2>
        {resources.length === 0 ? (
          <p className="ca-muted">Nenhum recurso cadastrado nesta filial.</p>
        ) : (
          <ul className="ca-resource-list">
            {resources.map((resource) => {
              const checked = selectedResourceIds.includes(resource.id);
              const color = RESOURCE_TYPE_COLORS[resource.resource_type];
              return (
                <li key={resource.id} className="ca-resource-list__item">
                  <label className="ca-resource-item">
                    <span className="ca-resource-item__leading">
                      <input
                        type="checkbox"
                        className="ca-resource-item__checkbox"
                        checked={checked}
                        onChange={() => onToggleResource(resource.id)}
                      />
                      <span
                        className="ca-resource-item__dot"
                        style={{ background: color }}
                        aria-hidden
                      />
                    </span>
                    <span className="ca-resource-item__body">
                      <span className="ca-resource-item__name">{resource.name}</span>
                      {resource.capacity ? (
                        <span className="ca-resource-item__meta">
                          Capacidade: {resource.capacity}
                        </span>
                      ) : null}
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </aside>
  );
}
