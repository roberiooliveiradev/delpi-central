import { useMemo, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { ArrowLeft } from "lucide-react";
// MF: import estático nomeado. lazy+dynamic do Index devolvia undefined → React #306.
import { ConfigurableSeriesChart } from "@delpi/plugin-ui/index";
import type {
  MesWorkCenterPeriodMes,
  PublicWorkCenterPerformance,
  WorkCenterDowntimeSource,
} from "./api";
import {
  BrandBar,
  EFFICIENCY_GOAL_PCT,
  efficiencyTone,
  formatDate,
  formatDateShort,
  formatHours,
  formatPercent,
  formatQty,
  formatUnit,
} from "./cockpitShared";
import { useOperatorSession } from "./OperatorSessionContext";
import { formatDurationHms } from "./runTimeline";
import { useMesWorkCenterPeriod } from "./useMesWorkCenterPeriod";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";

type ChartPoint = { label: string; value: number | null };

type Props = {
  token: string;
  branch: string;
  workCenter: string;
  workCenterName: string;
  /** Fonte oficial de paradas do posto (Etapa 1) — decide o painel. */
  source: WorkCenterDowntimeSource["source"] | null;
  sourceLoading: boolean;
  sourceError: string | null;
  onRetrySource: () => void;
  performance: PublicWorkCenterPerformance | null;
  loading: boolean;
  error: string | null;
  runRealtimeEvent: MachineLoadRealtimeEvent | null;
  realtimeConnected: boolean;
  onOpenActivity: () => void;
  onBack: () => void;
};

export function WorkCenterPerformancePage({
  token,
  branch,
  workCenter,
  workCenterName,
  source,
  sourceLoading,
  sourceError,
  onRetrySource,
  performance,
  loading,
  error,
  runRealtimeEvent,
  realtimeConnected,
  onOpenActivity,
  onBack,
}: Props) {
  return (
    <section className="pcp-pub pcp-pub--performance">
      <BrandBar
        eyebrow={`Desempenho do posto · Filial ${branch}`}
        title={workCenterName || workCenter}
        code={workCenter}
        stats={
          source === "mes" ? (
            <span className="pcp-pub__chip">
              Eficiência do ERP · paradas medidas pelo sensor (MES)
            </span>
          ) : performance?.shift ? (
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
      {source === "mes" ? (
        <>
          <TotvsPerformancePanel
            performance={performance}
            loading={loading}
            error={error}
            includeDowntime={false}
          />
          <MesPeriodPanel
            token={token}
            branch={branch}
            workCenter={workCenter}
            runRealtimeEvent={runRealtimeEvent}
            realtimeConnected={realtimeConnected}
            onOpenActivity={onOpenActivity}
          />
        </>
      ) : source === "totvs" ? (
        <TotvsPerformancePanel
          performance={performance}
          loading={loading}
          error={error}
        />
      ) : (
        <div className="pcp-pub__wrap">
          <p className="pcp-pub__empty">
            {sourceLoading
              ? "Resolvendo a fonte de dados do posto…"
              : sourceError ??
                "Fonte de dados do posto indisponível — sem indicadores no momento."}
          </p>
          {!sourceLoading && sourceError ? (
            <button
              type="button"
              className="pcp-pub__btn pcp-pub__btn--ghost"
              onClick={onRetrySource}
            >
              Tentar novamente
            </button>
          ) : null}
        </div>
      )}
    </section>
  );
}

/**
 * Painel TOTVS — CT sem sensoriamento: comportamento legado preservado.
 * Com includeDowntime={false} (posto MES), eficiência e apontamentos
 * continuam do ERP, mas o bloco de paradas é suprimido — paradas MES
 * vêm do MesPeriodPanel logo abaixo.
 */
function TotvsPerformancePanel({
  performance,
  loading,
  error,
  includeDowntime = true,
}: {
  performance: PublicWorkCenterPerformance | null;
  loading: boolean;
  error: string | null;
  includeDowntime?: boolean;
}) {
  const efficiency = performance?.efficiency;
  const downtime = performance?.downtime;

  const efficiencyPoints = useMemo(
    () =>
      efficiency?.available
        ? efficiency.series.map((point) => ({
            label: formatDateShort(point.date),
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
            label: formatDateShort(point.date),
            value: point.hours,
          }))
        : [],
    [downtime],
  );

  return (
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
                    label="Produzido no turno"
                    value={
                      efficiency.shift_produced_qty == null
                        ? "—"
                        : `${formatQty(efficiency.shift_produced_qty)} ${formatUnit(
                            null,
                            efficiency.shift_produced_qty,
                          )}`
                    }
                    note="Soma dos apontamentos do turno"
                  />
                  {includeDowntime && downtime?.available ? (
                    <Kpi
                      label="Horas de paradas hoje"
                      value={formatHours(downtime.today_hours)}
                      note={`${downtime.today_appointment_count ?? 0} apontamento(s)`}
                    />
                  ) : null}
                  <Kpi
                    label="Média do período"
                    value={formatPercent(efficiency.period_avg_pct)}
                    tone={efficiencyTone(efficiency.period_avg_pct)}
                    note={`${performance.days} dias · só o turno atual`}
                  />
                </div>

                <ChartCard
                  title="Eficiência por dia"
                  subtitle={`Só o turno atual em cada dia — meta ${EFFICIENCY_GOAL_PCT}% (verde ao atingir)`}
                  chartType="bar"
                  variant="efficiency"
                  points={efficiencyPoints}
                  yAxisTitle="Eficiência (%)"
                  emptyMessage="Sem apontamentos no período."
                />
              </>
            ) : (
              <Unavailable message={blockMessage(efficiency)} />
            )}

            {includeDowntime ? (
              <h2 className="pcp-pub__detail-section">Paradas</h2>
            ) : null}
            {includeDowntime && downtime?.available ? (
              <>
                <div className="pcp-pub__kpis">
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
                  variant="reasons"
                  points={downtimeByReasonPoints}
                  yAxisTitle="Horas"
                  emptyMessage="Nenhuma parada apontada no período."
                />
                <ChartCard
                  title="Horas paradas por dia"
                  subtitle="Total de horas paradas em cada dia"
                  chartType="bar"
                  variant="downtime-day"
                  points={downtimeByDayPoints}
                  yAxisTitle="Horas"
                  emptyMessage="Nenhuma parada apontada no período."
                />
              </>
            ) : includeDowntime ? (
              <Unavailable message={blockMessage(downtime)} />
            ) : null}

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
  );
}

/**
 * Seção de paradas MES (Etapa 4): agregados oficiais do contrato de
 * período — produzindo/parado/paradas/pendentes, paradas por motivo e
 * tempo parado por dia. Na página de desempenho ela acompanha o painel
 * TOTVS sem o bloco de paradas: eficiência/apontamentos são do ERP,
 * paradas são do sensor. Não exibe eficiência nem OEE (sem denominador
 * governado).
 */
function MesPeriodPanel({
  token,
  branch,
  workCenter,
  runRealtimeEvent,
  realtimeConnected,
  onOpenActivity,
}: {
  token: string;
  branch: string;
  workCenter: string;
  runRealtimeEvent: MachineLoadRealtimeEvent | null;
  realtimeConnected: boolean;
  onOpenActivity: () => void;
}) {
  const { session, status, invalidate, openIdentify } = useOperatorSession();
  const [days, setDays] = useState(7);
  const period = useMesWorkCenterPeriod({
    token,
    sessionToken: session?.sessionToken ?? null,
    branch,
    workCenter,
    days,
    runRealtimeEvent,
    realtimeConnected,
    onAuthError: invalidate,
  });
  const data = period.data?.source === "mes" ? period.data : null;

  const dayPoints = useMemo<ChartPoint[]>(
    () =>
      (data?.days ?? []).map((day) => ({
        label: formatDateShort(day.date),
        value: day.stoppedSeconds / 3600,
      })),
    [data],
  );

  const reasonPoints = useMemo<ChartPoint[]>(
    () =>
      (data?.reasons ?? []).map((reason) => ({
        label:
          reason.count > 0
            ? `${reason.label} · ${reason.count}×`
            : reason.label,
        value: reason.seconds / 3600,
      })),
    [data],
  );

  if (!session) {
    return (
      <div className="pcp-pub__wrap">
        <p className="pcp-pub__notice">
          Identifique-se no posto para ver o desempenho medido pelo sensor
          (MES). Números de turno do ERP não são exibidos neste posto.
        </p>
        <button
          type="button"
          className="pcp-pub__btn pcp-pub__btn--ghost"
          onClick={openIdentify}
          disabled={status === "restoring"}
        >
          Identificar operador
        </button>
      </div>
    );
  }

  const mesData: MesWorkCenterPeriodMes | null = data;

  return (
    <div className="pcp-pub__wrap">
      <div className="pcp-pub__period-tabs" role="group" aria-label="Período consultado">
        {[7, 14, 30].map((option) => (
          <button
            key={option}
            type="button"
            className={`pcp-pub__btn pcp-pub__btn--ghost${
              days === option ? " pcp-pub__btn--active" : ""
            }`}
            aria-pressed={days === option}
            onClick={() => setDays(option)}
          >
            {option} dias
          </button>
        ))}
        <button
          type="button"
          className="pcp-pub__btn pcp-pub__btn--ghost"
          onClick={onOpenActivity}
        >
          Atividade do posto (hoje)
        </button>
      </div>

      {period.loading && !mesData ? (
        <p className="pcp-pub__empty">Carregando desempenho do posto…</p>
      ) : null}
      {period.error ? (
        <>
          <p className="pcp-pub__error">{period.error.message}</p>
          {period.error.retryable ? (
            <button
              type="button"
              className="pcp-pub__btn pcp-pub__btn--ghost"
              onClick={() => void period.refresh()}
            >
              Tentar novamente
            </button>
          ) : null}
        </>
      ) : null}
      {period.data?.source === "totvs" ? (
        <p className="pcp-pub__notice">
          Este posto não é sensorizado — o desempenho MES não se aplica.
        </p>
      ) : null}

      {mesData ? (
        <>
          <p className="pcp-pub__notice">
            Tempos medidos pelo sensor do posto (MES) entre{" "}
            {formatDate(mesData.from)} e {formatDate(mesData.to)}, dias civis
            em horário de São Paulo. Não é a eficiência de turno do ERP.
          </p>

          <h2 className="pcp-pub__detail-section">Atividade no período</h2>
          <div className="pcp-pub__kpis">
            <Kpi
              label="Produzindo"
              value={formatDurationHms(mesData.totals.producingSeconds)}
              note="tempo medido pelo sensor"
            />
            <Kpi
              label="Parado"
              value={formatDurationHms(mesData.totals.stoppedSeconds)}
              note={`${mesData.totals.stopCount} parada(s)`}
            />
            <Kpi
              label="Motivos pendentes"
              value={String(mesData.totals.pendingReasonCount)}
              note={
                mesData.totals.pendingReasonCount > 0
                  ? "classifique na Atividade do posto"
                  : "todos os motivos informados"
              }
              tone={mesData.totals.pendingReasonCount > 0 ? "warn" : "none"}
            />
          </div>

          <ChartCard
            title="Paradas por motivo"
            subtitle="Tempo parado no período agrupado por motivo classificado"
            chartType="horizontal_bar"
            variant="reasons"
            points={reasonPoints}
            yAxisTitle="Horas"
            emptyMessage="Nenhuma parada registrada no período."
          />
          <ChartCard
            title="Tempo parado por dia"
            subtitle="Horas paradas medidas pelo sensor em cada dia civil"
            chartType="bar"
            variant="downtime-day"
            points={dayPoints}
            yAxisTitle="Horas"
            emptyMessage="Nenhuma parada registrada no período."
          />
          {mesData.quality.stopOverlapSeconds > 0 ? (
            <p className="pcp-pub__notice">
              Há {formatDurationHms(mesData.quality.stopOverlapSeconds)} de
              paradas sobrepostas no período — a soma por motivo pode exceder o
              total real.
            </p>
          ) : null}
        </>
      ) : null}
    </div>
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
  variant,
  points,
  yAxisTitle,
  emptyMessage,
}: {
  title: string;
  subtitle?: string;
  chartType: "bar" | "horizontal_bar";
  variant: "efficiency" | "reasons" | "downtime-day";
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

  const isReasons = variant === "reasons";
  const isEfficiency = variant === "efficiency";
  const plotHeightPx = isReasons
    ? Math.min(720, Math.max(280, points.length * 42 + 48))
    : isEfficiency
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
            showGrid: false,
            showVerticalGrid: false,
            showMarkers: false,
            yAxisTitle,
            xAxisTitle: "",
            showXAxisTitle: false,
            showYAxisTitle: true,
            valueFormat: "number",
            decimalPlaces: 1,
            seriesColor: isEfficiency ? "#15803d" : "#089bdb",
            showDataLabels: true,
            dataLabels: {
              showValue: true,
              showCategoryName: false,
              position: "outsideEnd",
            },
            categoryLabelOverflow: isReasons ? "wrap" : "truncate",
            categoryLabelRotation: chartType === "bar" ? "auto" : 0,
            categoryPaddingPercent: 2,
            ...(isEfficiency
              ? {
                  showGoalLine: true,
                  goalLineValue: EFFICIENCY_GOAL_PCT,
                  colorScale: {
                    mode: "by_goal" as const,
                    polarity: "high_is_good" as const,
                  },
                }
              : {}),
          }}
        />
      </div>
    </figure>
  );
}
