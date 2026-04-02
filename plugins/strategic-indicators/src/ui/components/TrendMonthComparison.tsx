type TrendMonthComparisonProps = {
  currentPeriod: string;
  previousPeriod: string;
  currentIgd: number;
  previousIgd: number;
};

export function TrendMonthComparison({
  currentPeriod,
  previousPeriod,
  currentIgd,
  previousIgd,
}: TrendMonthComparisonProps) {
  const variation = currentIgd - previousIgd;

  return (
    <section className="si-trend-month-comparison">
      <div className="si-trend-month-comparison__header">
        <h3 className="si-trend-month-comparison__title">
          Comparação do mês
        </h3>
        <span className="si-trend-month-comparison__subtitle">
          leitura direta do último fechamento
        </span>
      </div>

      <div className="si-trend-month-comparison__grid">
        <div className="si-trend-month-comparison__card">
          <span className="si-trend-month-comparison__label">
            {previousPeriod}
          </span>
          <strong className="si-trend-month-comparison__value">
            {previousIgd.toFixed(1)}
          </strong>
        </div>

        <div className="si-trend-month-comparison__card">
          <span className="si-trend-month-comparison__label">
            {currentPeriod}
          </span>
          <strong className="si-trend-month-comparison__value">
            {currentIgd.toFixed(1)}
          </strong>
        </div>

        <div className="si-trend-month-comparison__card">
          <span className="si-trend-month-comparison__label">Variação</span>
          <strong className="si-trend-month-comparison__value">
            {variation > 0 ? "+" : ""}
            {variation.toFixed(1)}
          </strong>
        </div>
      </div>
    </section>
  );
}