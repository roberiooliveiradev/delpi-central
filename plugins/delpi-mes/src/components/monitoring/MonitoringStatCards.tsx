import { Activity, Coffee, Pause, Play, TriangleAlert } from "lucide-react";
import type { MonitoringSummary } from "../../types/mes";

type StatCard = {
  id: string;
  label: string;
  value: number;
  tone: "info" | "success" | "warning" | "danger";
  icon: typeof Activity;
  description?: string;
};

function sparkline(seed: number): string {
  const points: string[] = [];
  for (let i = 0; i <= 6; i += 1) {
    const y = 22 - ((seed * (i + 3)) % 14) - (i * seed) % 6;
    points.push(`${i * 12},${Math.max(4, Math.min(26, y))}`);
  }
  return points.join(" ");
}

export function MonitoringStatCards({ summary }: { summary: MonitoringSummary }) {
  const cards: StatCard[] = [
    { id: "active", label: "Runs ativos", value: summary.activeRuns, tone: "info", icon: Activity },
    { id: "producing", label: "Produzindo", value: summary.producing, tone: "success", icon: Play },
    { id: "stopped", label: "Estado parado", value: summary.stopped, tone: "warning", icon: Pause, description: "inclui pausas manuais" },
    { id: "paused", label: "Pausas manuais", value: summary.paused, tone: "warning", icon: Coffee },
    { id: "pending", label: "Motivos pendentes", value: summary.unclassifiedDowntimes, tone: "danger", icon: TriangleAlert },
  ];

  return (
    <div className="delpi-mes-stats" role="group" aria-label="Resumo dos runs ativos">
      {cards.map((card, index) => {
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
              <polyline points={sparkline(index + card.value + 1)} fill="none" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            {card.description ? <span className="delpi-mes-stat__desc">{card.description}</span> : null}
          </div>
        );
      })}
    </div>
  );
}
