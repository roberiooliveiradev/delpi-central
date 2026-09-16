import { useMemo } from "react";
import type { CSSProperties, ReactNode } from "react";
import { ArrowLeft } from "lucide-react";
// MF: import estático nomeado. lazy+dynamic do Index devolvia undefined → React #306.
import { ConfigurableSeriesChart } from "@delpi/plugin-ui/index";
import type { PublicWorkCenterPerformance } from "./api";
import {
  BrandBar,
  efficiencyTone,
  formatDate,
  formatHours,
  formatPercent,
  formatQty,
} from "./cockpitShared";

type ChartPoint = { label: string; value: number | null };

type Props = {
  branch: string;
  workCenter: string;
  workCenterName: string;
  performance: PublicWorkCenterPerformance | null;
  loading: boolean;
  error: string | null;
  onBack: () => void;
};

export function WorkCenterPerformancePage({
  branch,
  workCenter,
  workCenterName,
  performance,
  loading,
  error,
  onBack,
}: Props) {
  const efficiency = performance?.efficiency;
  const downtime = performance?.downtime;

  const efficiencyPoints = useMemo(
    () =>
      efficiency?.available
        ? efficiency.series.map((point) => ({
            label: formatDate(point.date),
            value: point.efficiency_pct,
          }))
        : [],
    [efficiency],
  );

  const downtimeByReasonPoints = useMemo(() => {
    if (!downtime?.available) return [];
    return [...downtime.by_reason]
      .sort((a, b) => (b.hours ?? 0) - (a.hours ?? 0))
      .map((row) => {
        const reason = row.stop_reason_description?.trim() || row.stop_reason?.trim() || "Sem motivo";
        const count = row.appointment_count ?? 0;
        return {
          label: count > 0 ? `${reason} · ${count}×` : reason,
          value: row.hours,
        };
      });
  }, [downtime]);

  const downtimeByDayPoints = useMemo(
    () =>
      downtime?.available
        ? downtime.series.map((point) => ({
            label: formatDate(point.date),
            value: point.hours,
          }))
        : [],
    [downtime],
  );

  return (
    <section className="pcp-pub pcp-pub--performance">
      <BrandBar
        eyebrow={`Desempenho do posto · Filial ${branch}`}
        title={workCenterName || workCenter}
        code={workCenter}
        stats={
          performance?.shift ? (
            <span className="pcp-pub__chip">{performance.shift.label} em andamento</span>
          ) : null
        }
        lead={
          <button
            type="button"
            className="pcp-pub__back pcp-pub__back--icon"
            onClick={onBack}
            aria-label="Voltar para a fila"
            title="Voltar para a fila"
          >
            <ArrowLeft size={22} strokeWidth={2.4} aria-hidden="true" />
          </button>
        }
      />

      <div className="pcp-pub__wrap">
        {loading && !performance ? (
          <p className="pcp-pub__empty">Carregando desempenho…</p>
        ) : null}
        {error ? <p className="pcp-pub__error">{error}</p> : null}

        {performance ? (
          <>
            <p className="pcp-pub__notice">
              Números do posto no turno e no período. Período de{" "}
              {formatDate(performance.period.start_date)} a{" "}
              {formatDate(performance.period.end_date)}. Sem login do operador e
              sem valores em R$.
            </p>

            <h2 className="pcp-pub__detail-section">Eficiência</h2>
            {efficiency?.available ? (
              <>
                <div className="pcp-pub__kpis">
                  <Kpi
                    label="Turno atual"
                    value={formatPercent(efficiency.shift_pct)}
                    tone={efficiencyTone(efficiency.shift_pct)}
                    note={`${efficiency.shift_appointment_count ?? 0} apontamento(s)`}
                  />
                  <Kpi
                    label="Hoje"
                    value={formatPercent(efficiency.day_pct)}
                    tone={efficiencyTone(efficiency.day_pct)}
                    note={`${efficiency.day_appointment_count ?? 0} apontamento(s)`}
                  />
                  <Kpi
                    label="Média do período"
                    value={formatPercent(efficiency.period_avg_pct)}
                    tone={efficiencyTone(efficiency.period_avg_pct)}
                    note={`${performance.days} dias`}
                  />
                </div>

                <ChartCard
                  title="Eficiência por dia"
                  subtitle="Percentual em cada dia do período — valor marcado no ponto"
                  chartType="area"
                  points={efficiencyPoints}
                  yAxisTitle="Eficiência (%)"
                  emptyMessage="Sem apontamentos no período."
                />
              </>
            ) : (
              <Unavailable message={blockMessage(efficiency)} />
            )}

            <h2 className="pcp-pub__detail-section">Paradas</h2>
            {downtime?.available ? (
              <>
                <div className="pcp-pub__kpis">
                  <Kpi
                    label="Horas paradas hoje"
                    value={formatHours(downtime.today_hours)}
                    note={`${downtime.today_appointment_count ?? 0} apontamento(s)`}
                  />
                  <Kpi
                    label="Horas no período"
                    value={formatHours(downtime.period_hours)}
                    note={`${downtime.period_appointment_count} apontamento(s)`}
                  />
                </div>

                <ChartCard
                  title="Horas paradas por motivo"
                  subtitle="Todos os motivos apontados no período, ordenados do maior para o menor"
                  chartType="horizontal_bar"
                  points={downtimeByReasonPoints}
                  yAxisTitle="Horas"
                  emptyMessage="Nenhuma parada apontada no período."
                />
                <ChartCard
                  title="Horas paradas por dia"
                  subtitle="Total de horas paradas em cada dia"
                  chartType="bar"
                  points={downtimeByDayPoints}
                  yAxisTitle="Horas"
                  emptyMessage="Nenhuma parada apontada no período."
                />
              </>
            ) : (
              <Unavailable message={blockMessage(downtime)} />
            )}

            <h2 className="pcp-pub__detail-section">Apontamentos do turno</h2>
            {efficiency?.available && efficiency.appointments.length > 0 ? (
              <div className="pcp-pub__table-wrap">
                <table className="pcp-pub__table">
                  <thead>
                    <tr>
                      <th scope="col">PA</th>
                      <th scope="col">OP</th>
                      <th scope="col">Operação</th>
                      <th scope="col">Operador</th>
                      <th scope="col">Quantidade</th>
                      <th scope="col">Previsto</th>
                      <th scope="col">Real</th>
                      <th scope="col">Eficiência</th>
                    </tr>
                  </thead>
                  <tbody>
                    {efficiency.appointments.map((row, index) => (
                      <tr key={`${row.production_order}::${row.operation}::${index}`}>
                        <td className="pcp-pub__num">
                          <strong className="pcp-pub__product-code--pa">
                            {row.pa_product_code?.trim() || row.product_code || "—"}
                          </strong>
                        </td>
                        <td className="pcp-pub__num">{row.production_order || "—"}</td>
                        <td>
                          {row.operation}
                          {row.operation_description ? ` · ${row.operation_description}` : ""}
                        </td>
                        <td>{row.operator_name?.trim() || "—"}</td>
                        <td className="pcp-pub__num">{formatQty(row.quantity)}</td>
                        <td className="pcp-pub__num">{formatHours(row.planned_hours)}</td>
                        <td className="pcp-pub__num">{formatHours(row.real_hours)}</td>
                        <td
                          className={`pcp-pub__num pcp-pub__pct pcp-pub__pct--${efficiencyTone(
                            row.efficiency_pct,
                          )}`}
                        >
                          {formatPercent(row.efficiency_pct)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="pcp-pub__empty">
                {efficiency?.available
                  ? "Nenhum apontamento registrado neste turno."
                  : blockMessage(efficiency)}
              </p>
            )}
          </>
        ) : null}
      </div>
    </section>
  );
}

function blockMessage(block: { available: boolean; message?: string } | undefined): string {
  if (!block) return "Indicador indisponível no momento.";
  return block.message || "Indicador indisponível no momento.";
}

function Unavailable({ message }: { message: string }) {
  return <p className="pcp-pub__empty pcp-pub__empty--soft">{message}</p>;
}

function Kpi({
  label,
  value,
  note,
  tone = "none",
}: {
  label: string;
  value: string;
  note?: string;
  tone?: "good" | "warn" | "bad" | "none";
}) {
  return (
    <div className={`pcp-pub__kpi pcp-pub__kpi--${tone}`}>
      <span className="pcp-pub__kpi-label">{label}</span>
      <strong className="pcp-pub__kpi-value">{value}</strong>
      {note ? <span className="pcp-pub__kpi-note">{note}</span> : null}
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  chartType,
  points,
  yAxisTitle,
  emptyMessage,
}: {
  title: string;
  subtitle?: string;
  chartType: "area" | "bar" | "horizontal_bar";
  points: ChartPoint[];
  yAxisTitle: string;
  emptyMessage: string;
}): ReactNode {
  if (points.length === 0) {
    return (
      <figure className="pcp-pub__chart">
        <figcaption>
          <span className="pcp-pub__chart-title">{title}</span>
          {subtitle ? <span className="pcp-pub__chart-subtitle">{subtitle}</span> : null}
        </figcaption>
        <p className="pcp-pub__empty pcp-pub__empty--soft">{emptyMessage}</p>
      </figure>
    );
  }

  const isReasons = chartType === "horizontal_bar";
  const isTrend = chartType === "area";
  const plotHeightPx = isReasons
    ? Math.min(720, Math.max(280, points.length * 42 + 48))
    : isTrend
      ? 340
      : 300;

  const plotStyle = {
    "--delpi-ui-series-chart-plot-height": `${plotHeightPx}px`,
  } as CSSProperties;

  return (
    <figure className={`pcp-pub__chart ${isReasons ? "pcp-pub__chart--reasons" : ""}`}>
      <figcaption>
        <span className="pcp-pub__chart-title">{title}</span>
        {subtitle ? <span className="pcp-pub__chart-subtitle">{subtitle}</span> : null}
      </figcaption>
      <div
        className={`delpi-ui-series-chart-plot pcp-pub__chart-plot pcp-pub__chart-plot--${chartType}`}
        style={plotStyle}
      >
        <ConfigurableSeriesChart
          chartType={chartType}
          points={points}
          emptyMessage={emptyMessage}
          options={{
            showTitle: false,
            showLegend: false,
            showGrid: true,
            showVerticalGrid: isTrend,
            showMarkers: isTrend,
            markerMode: "all",
            smoothLines: isTrend,
            areaFillGradient: isTrend,
            yAxisTitle,
            xAxisTitle: "",
            showXAxisTitle: false,
            showYAxisTitle: true,
            valueFormat: "number",
            decimalPlaces: 1,
            seriesColor: "#089bdb",
            showDataLabels: true,
            dataLabels: {
              showValue: true,
              showCategoryName: false,
              position: "outsideEnd",
            },
            // Motivos: nunca pular rótulos do eixo — o operador precisa ler todos.
            categoryLabelOverflow: isReasons ? "wrap" : chartType === "bar" ? "truncate" : "skip",
            categoryLabelRotation: chartType === "bar" ? "auto" : 0,
            categoryPaddingPercent: isTrend ? 4 : 2,
          }}
        />
      </div>
    </figure>
  );
}
