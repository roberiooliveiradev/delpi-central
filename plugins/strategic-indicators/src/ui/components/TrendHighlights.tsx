import type { DepartmentTrendItem } from "../../data/mocks/trendsMock";
import { StatusBadge } from "./StatusBadge";

type TrendHighlightsProps = {
  departments: DepartmentTrendItem[];
};

function getDelta(department: DepartmentTrendItem) {
  return department.current - department.previous;
}

export function TrendHighlights({
  departments,
}: TrendHighlightsProps) {
  const sorted = [...departments].sort(
    (a, b) => getDelta(b) - getDelta(a)
  );

  const best = sorted[0] ?? null;
  const worst = [...departments].sort(
    (a, b) => getDelta(a) - getDelta(b)
  )[0] ?? null;

  return (
    <div className="si-trend-highlights">
      <article className="si-trend-highlight-card">
        <div className="si-trend-highlight-card__top">
          <span className="si-trend-highlight-card__label">Maior melhora</span>
          <StatusBadge label="Destaque positivo" variant="success" />
        </div>

        {best ? (
          <>
            <h3 className="si-trend-highlight-card__title">{best.name}</h3>
            <p className="si-trend-highlight-card__value">
              {best.previous.toFixed(1)} → {best.current.toFixed(1)}
            </p>
            <p className="si-trend-highlight-card__delta">
              +{getDelta(best).toFixed(1)} no período
            </p>
          </>
        ) : null}
      </article>

      <article className="si-trend-highlight-card">
        <div className="si-trend-highlight-card__top">
          <span className="si-trend-highlight-card__label">Maior queda</span>
          <StatusBadge label="Acompanhar" variant="warning" />
        </div>

        {worst ? (
          <>
            <h3 className="si-trend-highlight-card__title">{worst.name}</h3>
            <p className="si-trend-highlight-card__value">
              {worst.previous.toFixed(1)} → {worst.current.toFixed(1)}
            </p>
            <p className="si-trend-highlight-card__delta">
              {getDelta(worst).toFixed(1)} no período
            </p>
          </>
        ) : null}
      </article>
    </div>
  );
}