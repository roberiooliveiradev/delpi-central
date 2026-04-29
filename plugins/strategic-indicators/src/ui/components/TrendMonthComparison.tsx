import { StatusBadge } from "./StatusBadge";
import "./TrendMonthComparison.css";

type TrendMonthComparisonProps = {
  currentPeriod: string;
  previousPeriod: string;
  currentIgd: number;
  previousIgd: number;
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

function getDirectionLabel(value: number) {
  if (value > 0.09) return "Melhora";
  if (value < -0.09) return "Queda";
  return "Estável";
}

function getDirectionVariant(value: number): "success" | "warning" | "neutral" {
  if (value > 0.09) return "success";
  if (value < -0.09) return "warning";
  return "neutral";
}

function getPercentVariation(current: number, previous: number) {
  if (!previous) return 0;
  return ((current - previous) / previous) * 100;
}

export function TrendMonthComparison({
  currentPeriod,
  previousPeriod,
  currentIgd,
  previousIgd,
}: TrendMonthComparisonProps) {
  const variation = currentIgd - previousIgd;
  const percentVariation = getPercentVariation(currentIgd, previousIgd);

  return (
    <section
      className={`si-trend-month-comparison si-trend-month-comparison--${getDirectionVariant(
        variation,
      )}`}
    >
      <div className="si-trend-month-comparison__header">
        <div>
          <p className="si-trend-month-comparison__eyebrow">
            Último fechamento
          </p>
          <h3 className="si-trend-month-comparison__title">
            Comparação direta do mês
          </h3>
        </div>

        <StatusBadge
          label={getDirectionLabel(variation)}
          variant={getDirectionVariant(variation)}
        />
      </div>

      <div className="si-trend-month-comparison__flow">
        <article className="si-trend-month-comparison__period-card">
          <span className="si-trend-month-comparison__label">
            Período anterior
          </span>
          <strong className="si-trend-month-comparison__period">
            {previousPeriod}
          </strong>
          <strong className="si-trend-month-comparison__value">
            {formatScore(previousIgd)}
          </strong>
        </article>

        <div className="si-trend-month-comparison__bridge">
          <span className="si-trend-month-comparison__arrow">→</span>

          <div className="si-trend-month-comparison__variation-card">
            <span>Variação</span>
            <strong>{formatVariation(variation)}</strong>
            <small>
              {formatVariation(percentVariation)}% no período
            </small>
          </div>
        </div>

        <article className="si-trend-month-comparison__period-card si-trend-month-comparison__period-card--current">
          <span className="si-trend-month-comparison__label">
            Período atual
          </span>
          <strong className="si-trend-month-comparison__period">
            {currentPeriod}
          </strong>
          <strong className="si-trend-month-comparison__value">
            {formatScore(currentIgd)}
          </strong>
        </article>
      </div>
    </section>
  );
}