import { useMemo } from "react";
import {
  ConfigurableSeriesChart,
  segmentToggleBemClasses,
  type SeriesChartPoint,
  type SeriesChartSeriesSpec,
} from "@delpi/plugin-ui/index";

import type {
  KaizenSavingsInvestmentSeries,
  KaizenSeriesGranularity,
} from "../types/kaizen";
import { formatCurrency, formatDate } from "../utils/format";

const SEGMENT = segmentToggleBemClasses("ds");

const SAVINGS_COLOR = "#22c55e";
const INVESTMENT_COLOR = "#ef4444";

const MONTH_FMT = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "numeric" });

const GRANULARITY_OPTIONS: Array<{ value: KaizenSeriesGranularity; label: string }> = [
  { value: "day", label: "Dia" },
  { value: "month", label: "Mês" },
];

type Props = {
  series: KaizenSavingsInvestmentSeries | null;
  granularity: KaizenSeriesGranularity;
  onGranularityChange: (value: KaizenSeriesGranularity) => void;
  loading?: boolean;
};

function periodLabel(periodo: string, granularity: KaizenSeriesGranularity): string {
  if (granularity === "day") {
    return formatDate(periodo) || periodo;
  }
  const [year, month] = periodo.split("-").map(Number);
  if (!year || !month) return periodo;
  return MONTH_FMT.format(new Date(year, month - 1, 1));
}

export function KaizenSavingsInvestmentChart({
  series,
  granularity,
  onGranularityChange,
  loading = false,
}: Props) {
  const rangeLabel = useMemo(() => {
    if (!series) return null;
    return `${formatDate(series.start_date)} — ${formatDate(series.end_date)}`;
  }, [series]);

  const seriesList = useMemo<SeriesChartSeriesSpec[]>(() => {
    if (!series?.points.length) return [];
    const savingsPoints: SeriesChartPoint[] = series.points.map((point) => ({
      label: periodLabel(point.periodo, series.granularity),
      value: point.savings,
    }));
    const investmentPoints: SeriesChartPoint[] = series.points.map((point) => ({
      label: periodLabel(point.periodo, series.granularity),
      value: point.investment,
    }));
    return [
      { name: "Ganhos financeiros", points: savingsPoints, color: SAVINGS_COLOR },
      { name: "Investimento", points: investmentPoints, color: INVESTMENT_COLOR },
    ];
  }, [series]);

  const empty =
    !loading &&
    (!series || series.points.every((point) => point.savings === 0 && point.investment === 0));

  return (
    <section className="kz-card kz-dash-panel kz-dash-panel--wide kz-dash-chart">
      <div className="kz-dash-chart__header">
        <div className="kz-dash-chart__titles">
          <h2 className="kz-dash-panel__title">Ganhos financeiros vs Investimento</h2>
          {rangeLabel ? (
            <p className="kz-dash-chart__subtitle">
              {rangeLabel}
              {granularity === "month" ? " · competências mensais no recorte" : " · dias no recorte"}
            </p>
          ) : null}
        </div>
        <div className={SEGMENT.root} role="group" aria-label="Granularidade do gráfico">
          {GRANULARITY_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={
                granularity === option.value ? SEGMENT.buttonActive : SEGMENT.button
              }
              onClick={() => onGranularityChange(option.value)}
              aria-pressed={granularity === option.value}
              disabled={loading}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {loading && !series ? (
        <p className="kz-dash-chart__empty">Carregando série…</p>
      ) : empty ? (
        <p className="kz-dash-chart__empty">Sem ganhos ou investimentos no período.</p>
      ) : (
        <>
          <div className="kz-dash-chart__canvas">
            <ConfigurableSeriesChart
              chartType="area"
              points={seriesList[0]?.points ?? []}
              seriesList={seriesList}
              options={{
                showTitle: false,
                showLegend: true,
                legendPosition: "bottom",
                showAxes: true,
                showXAxisLabels: true,
                showYAxisLabels: true,
                showXAxisTitle: false,
                showYAxisTitle: false,
                showGrid: true,
                showMarkers: false,
                smoothLines: true,
                valueFormat: "currency",
                theme: "dark",
              }}
            />
          </div>
          {series ? (
            <p className="kz-dash-chart__totals" role="status">
              Totais no recorte: ganhos {formatCurrency(series.total_savings)} · investimento{" "}
              {formatCurrency(series.total_investment)}
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}
