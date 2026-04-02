import type { DepartmentTrendItem } from "../../data/mocks/trendsMock";
import { StatusBadge } from "./StatusBadge";

type TrendSummaryCardsProps = {
  currentIgd: number;
  previousIgd: number;
  departments: DepartmentTrendItem[];
};

function getAverageDepartmentScore(departments: DepartmentTrendItem[]) {
  if (!departments.length) return 0;

  const total = departments.reduce((sum, department) => sum + department.current, 0);
  return total / departments.length;
}

export function TrendSummaryCards({
  currentIgd,
  previousIgd,
  departments,
}: TrendSummaryCardsProps) {
  const variation = currentIgd - previousIgd;
  const improved = departments.filter((item) => item.direction === "up").length;
  const declined = departments.filter((item) => item.direction === "down").length;
  const stable = departments.filter((item) => item.direction === "stable").length;
  const averageDepartmentScore = getAverageDepartmentScore(departments);

  return (
    <div className="si-trend-summary-grid">
      <article className="si-trend-summary-card">
        <span className="si-trend-summary-card__label">Variação do IGD</span>
        <strong className="si-trend-summary-card__value">
          {variation > 0 ? "+" : ""}
          {variation.toFixed(1)}
        </strong>
        <p className="si-trend-summary-card__text">
          Comparação direta entre o período atual e o anterior.
        </p>
      </article>

      <article className="si-trend-summary-card">
        <span className="si-trend-summary-card__label">Média das áreas</span>
        <strong className="si-trend-summary-card__value">
          {averageDepartmentScore.toFixed(1)}
        </strong>
        <p className="si-trend-summary-card__text">
          Média atual das notas departamentais no recorte temporal.
        </p>
      </article>

      <article className="si-trend-summary-card">
        <span className="si-trend-summary-card__label">Direção das áreas</span>
        <div className="si-trend-summary-card__badges">
          <StatusBadge label={`${improved} em melhora`} variant="success" />
          <StatusBadge label={`${stable} estáveis`} variant="neutral" />
          <StatusBadge label={`${declined} em queda`} variant="warning" />
        </div>
        <p className="si-trend-summary-card__text">
          Distribuição rápida do comportamento recente dos departamentos.
        </p>
      </article>
    </div>
  );
}