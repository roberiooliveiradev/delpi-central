import { useMemo } from "react";
import type { ReactNode } from "react";
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

  const downtimeByReasonPoints = useMemo(
    () =>
      downtime?.available
        ? downtime.by_reason.map((row) => ({
            label: row.stop_reason_description || row.stop_reason || "—",
            value: row.hours,
          }))
        : [],
    [downtime],
  );

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
          <button type="button" className="pcp-pub__back" onClick={onBack}>
            <span aria-hidden="true">←</span> Voltar para a fila
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
              Números do posto inteiro, sem identificação individual. Período de{" "}
              {formatDate(performance.period.start_date)} a{" "}
              {formatDate(performance.period.end_date)}.
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
                  chartType="line"
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
                  chartType="horizontal_bar"
                  points={downtimeByReasonPoints}
                  yAxisTitle="Horas"
                  emptyMessage="Nenhuma parada apontada no período."
                />
                <ChartCard
                  title="Horas paradas por dia"
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
                      <th scope="col">OP</th>
                      <th scope="col">Operação</th>
                      <th scope="col">Quantidade</th>
                      <th scope="col">Previsto</th>
                      <th scope="col">Real</th>
                      <th scope="col">Eficiência</th>
                    </tr>
                  </thead>
                  <tbody>
                    {efficiency.appointments.map((row, index) => (
                      <tr key={`${row.production_order}::${row.operation}::${index}`}>
                        <td>{row.production_order || "—"}</td>
                        <td>
                          {row.operation}
                          {row.operation_description ? ` · ${row.operation_description}` : ""}
                        </td>
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
  chartType,
  points,
  yAxisTitle,
  emptyMessage,
}: {
  title: string;
  chartType: "line" | "bar" | "horizontal_bar";
  points: Array<{ label: string; value: number | null }>;
  yAxisTitle: string;
  emptyMessage: string;
}): ReactNode {
  if (points.length === 0) {
    return (
      <figure className="pcp-pub__chart">
        <figcaption>{title}</figcaption>
        <p className="pcp-pub__empty pcp-pub__empty--soft">{emptyMessage}</p>
      </figure>
    );
  }
  return (
    <figure className="pcp-pub__chart">
      <figcaption>{title}</figcaption>
      <div className="delpi-ui-series-chart-plot pcp-pub__chart-plot">
        <ConfigurableSeriesChart
          chartType={chartType}
          points={points}
          emptyMessage={emptyMessage}
          options={{
            showTitle: false,
            showLegend: false,
            yAxisTitle,
            xAxisTitle: "",
            showXAxisTitle: false,
            valueFormat: "number",
            decimalPlaces: 1,
          }}
        />
      </div>
    </figure>
  );
}
