import type { DepartmentTrendItem } from "../../data/types/trends";
import { StatusBadge } from "./StatusBadge";
import "./TrendSummaryCards.css";

type TrendSummaryCardsProps = {
  currentIgd: number;
  previousIgd: number;
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

function getAverageDepartmentScore(departments: DepartmentTrendItem[]) {
  if (!departments.length) return 0;

  const total = departments.reduce(
    (sum, department) => sum + department.current,
    0,
  );

  return total / departments.length;
}

function getVariationDirection(value: number) {
  if (value > 0.09) return "Melhora";
  if (value < -0.09) return "Queda";
  return "Estável";
}

function getVariationVariant(value: number): "success" | "warning" | "neutral" {
  if (value > 0.09) return "success";
  if (value < -0.09) return "warning";
  return "neutral";
}

function getPercent(value: number, total: number) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
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
  const total = departments.length;

  const improvedPct = getPercent(improved, total);
  const stablePct = getPercent(stable, total);
  const declinedPct = getPercent(declined, total);

  const averageDepartmentScore = getAverageDepartmentScore(departments);

  const bestRecovery = [...departments].sort(
    (a, b) => b.netVariation - a.netVariation,
  )[0];

  const mainPressure = [...departments].sort(
    (a, b) => a.netVariation - b.netVariation,
  )[0];

  return (
    <div className="si-trend-summary-panel">
      <article
        className={`si-trend-summary-card si-trend-summary-card--${getVariationVariant(
          variation,
        )}`}
      >
        <div className="si-trend-summary-card__top">
          <span className="si-trend-summary-card__label">Variação do IGD</span>
          <StatusBadge
            label={getVariationDirection(variation)}
            variant={getVariationVariant(variation)}
          />
        </div>

        <strong className="si-trend-summary-card__value">
          {formatVariation(variation)}
        </strong>

        <p className="si-trend-summary-card__text">
          Comparação direta entre o período atual e o anterior.
        </p>
      </article>

      <article className="si-trend-summary-card si-trend-summary-card--featured">
        <span className="si-trend-summary-card__label">Média das áreas</span>

        <strong className="si-trend-summary-card__value">
          {formatScore(averageDepartmentScore)}
        </strong>

        <p className="si-trend-summary-card__text">
          Média atual das notas departamentais no recorte temporal.
        </p>
      </article>

      <article className="si-trend-summary-card si-trend-summary-card--distribution">
        <div className="si-trend-summary-card__top">
          <span className="si-trend-summary-card__label">Direção das áreas</span>
        </div>

        <div className="si-trend-distribution">
          <div className="si-trend-distribution__bar">
            <span
              className="si-trend-distribution__segment si-trend-distribution__segment--up"
              style={{ width: `${improvedPct}%` }}
            />
            <span
              className="si-trend-distribution__segment si-trend-distribution__segment--stable"
              style={{ width: `${stablePct}%` }}
            />
            <span
              className="si-trend-distribution__segment si-trend-distribution__segment--down"
              style={{ width: `${declinedPct}%` }}
            />
          </div>

          <div className="si-trend-distribution__legend">
            <span>{improved} em melhora</span>
            <span>{stable} estáveis</span>
            <span>{declined} em queda</span>
          </div>
        </div>

        <p className="si-trend-summary-card__text">
          {total > 0
            ? `${improved} áreas melhoraram, ${stable} permaneceram estáveis e ${declined} recuaram no período.`
            : "Nenhum departamento disponível no recorte temporal."}
        </p>
      </article>

      <article className="si-trend-summary-narrative">
        <span className="si-trend-summary-card__label">Leitura executiva</span>

        <p>
          IGD em <strong>{getVariationDirection(variation).toLowerCase()}</strong>{" "}
          de <strong>{formatVariation(variation)}</strong> ponto no período.
          {mainPressure ? (
            <>
              {" "}
              A maior pressão vem de <strong>{mainPressure.name}</strong>, com{" "}
              <strong>{formatVariation(mainPressure.netVariation)}</strong>.
            </>
          ) : null}
          {bestRecovery ? (
            <>
              {" "}
              A melhor recuperação vem de <strong>{bestRecovery.name}</strong>,
              com <strong>{formatVariation(bestRecovery.netVariation)}</strong>.
            </>
          ) : null}
        </p>
      </article>
    </div>
  );
}