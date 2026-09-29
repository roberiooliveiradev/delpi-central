import type { StatCardItem } from "../../utils/statItems";

function sparkline(seed: number): string {
  const points: string[] = [];
  for (let i = 0; i <= 6; i += 1) {
    const y = 22 - ((seed * (i + 3)) % 14) - (i * seed) % 6;
    points.push(`${i * 12},${Math.max(4, Math.min(26, y))}`);
  }
  return points.join(" ");
}

export function MonitoringStatCards({ items, ariaLabel }: { items: StatCardItem[]; ariaLabel: string }) {
  return (
    <div className="delpi-mes-stats" role="group" aria-label={ariaLabel}>
      {items.map((card, index) => {
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
            <svg className="delpi-mes-stat__spark" viewBox="0 0 72 28" aria-hidden="true" focusable="false">
              <polyline points={sparkline(index + 1)} fill="none" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            {card.description ? <span className="delpi-mes-stat__desc">{card.description}</span> : null}
          </div>
        );
      })}
    </div>
  );
}
