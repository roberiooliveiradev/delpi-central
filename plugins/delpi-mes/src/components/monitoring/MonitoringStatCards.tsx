import type { StatCardItem } from "../../utils/statItems";

export function MonitoringStatCards({ items, ariaLabel }: { items: StatCardItem[]; ariaLabel: string }) {
  return (
    <div className="delpi-mes-stats" role="group" aria-label={ariaLabel}>
      {items.map((card) => {
        const Icon = card.icon;
        return (
          <div key={card.id} className={`delpi-mes-stat delpi-mes-stat--${card.tone}`}>
            <div className="delpi-mes-stat__main">
              <span className="delpi-mes-stat__icon" aria-hidden="true"><Icon /></span>
              <div>
                <span className="delpi-mes-stat__label">{card.label}</span>
                <strong className="delpi-mes-stat__value">{card.value}</strong>
              </div>
            </div>
            {card.description ? <span className="delpi-mes-stat__desc">{card.description}</span> : null}
          </div>
        );
      })}
    </div>
  );
}
