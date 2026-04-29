import type { DepartmentTrendItem } from "../../data/types/trends";
import { StatusBadge } from "./StatusBadge";

type TrendPriorityListProps = {
  departments: DepartmentTrendItem[];
};

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatVariation(value: number) {
  const formatted = Math.abs(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  if (value > 0) return `+${formatted}`;
  if (value < 0) return `-${formatted}`;
  return "0,0";
}

function getSeverityLabel(delta: number) {
  if (delta <= -3) return "Impacto crítico";
  if (delta <= -1) return "Queda relevante";
  return "Monitorar";
}

function getSeverityPercent(delta: number) {
  return Math.max(10, Math.min(100, Math.abs(delta) * 14));
}

export function TrendPriorityList({ departments }: TrendPriorityListProps) {
  const priorities = [...departments]
    .filter((department) => department.direction === "down")
    .sort((a, b) => a.netVariation - b.netVariation);

  if (!priorities.length) {
    return (
      <div className="si-trend-priority-list si-trend-priority-list--empty">
        Nenhuma área em queda no recorte temporal atual.
      </div>
    );
  }

  return (
    <div className="si-trend-priority-list si-trend-priority-list--ranked">
      {priorities.map((department, index) => {
        const delta = department.current - department.previous;

        return (
          <article key={department.id} className="si-trend-priority-item">
            <div className="si-trend-priority-item__rank">
              #{index + 1}
            </div>

            <div className="si-trend-priority-item__content">
              <div className="si-trend-priority-item__top">
                <div>
                  <h3 className="si-trend-priority-item__title">
                    {department.name}
                  </h3>
                  <p className="si-trend-priority-item__subtitle">
                    {getSeverityLabel(delta)}
                  </p>
                </div>

                <StatusBadge label="Acompanhar" variant="warning" />
              </div>

              <div className="si-trend-priority-item__metrics">
                <span>Atual: {formatScore(department.current)}</span>
                <span>Anterior: {formatScore(department.previous)}</span>
                <span>Variação: {formatVariation(delta)}</span>
              </div>

              <div className="si-trend-priority-item__severity-bar">
                <span style={{ width: `${getSeverityPercent(delta)}%` }} />
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}