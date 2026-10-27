import {
  BarSeriesChart,
  ChartCard,
  HelpTooltip,
  HorizontalValueBars,
  LoadingState,
  MetricKpiCard,
  chartCardBemClasses,
  horizontalValueBarsBemClasses,
  loadingStatePanelBemClasses,
  metricKpiCardBemClasses,
} from "@delpi/plugin-ui/index";
import {
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Hourglass,
  OctagonAlert,
  Tag,
  Timer,
} from "lucide-react";
import { useMemo, useState } from "react";

import { DELPI_MES_COPY } from "../../content/copy";
import type { useDowntimeAnalytics } from "../../hooks/useDowntimeAnalytics";
import type { DowntimeAnalyticsReasonGroup } from "../../types/mes";
import { formatHoursMinutes } from "../../utils/dayTimeline";
import {
  buildHeatmapRows,
  dayKeyLabel,
  daySeriesPoints,
  type AnalyticsMetric,
} from "../../utils/downtimeAnalyticsPresentation";

const loadingClasses = loadingStatePanelBemClasses("delpi-mes");
const kpiClasses = metricKpiCardBemClasses("delpi-mes");
const cardClasses = chartCardBemClasses("delpi-mes", { headerLayout: "titleRow" });
const barsClasses = horizontalValueBarsBemClasses("delpi-mes");

function describeReason(group: DowntimeAnalyticsReasonGroup): string {
  return group.reasonCode ? group.reasonCode + " — " + group.label : group.label;
}

/** Seção analítica da aba Paradas (Etapa 2): indicadores, Pareto de
 * motivos, ranking de CTs, evolução diária e mapa de calor. Todos os
 * agregados vêm do backend — o MFE só projeta, nunca recalcula. */
export function DowntimeAnalyticsSection({
  analytics,
  onSelectReasonGroup,
  onSelectWorkCenter,
  onSelectDay,
}: {
  analytics: ReturnType<typeof useDowntimeAnalytics>;
  onSelectReasonGroup: (group: DowntimeAnalyticsReasonGroup) => void;
  onSelectWorkCenter: (workCenter: string) => void;
  onSelectDay: (dayKey: string) => void;
}) {
  const [open, setOpen] = useState(true);
  const [metric, setMetric] = useState<AnalyticsMetric>("seconds");
  const data = analytics.data;
  const heatmap = useMemo(
    () => buildHeatmapRows(data?.byWeekdayHour ?? []),
    [data],
  );

  return (
    <section
      className="delpi-mes-analytics"
      aria-labelledby="downtimes-analytics-title"
      aria-busy={analytics.loading || analytics.refreshing}
    >
      <div className="delpi-mes-analytics__head">
        <h3 id="downtimes-analytics-title">
          Indicadores do período
          <HelpTooltip
            content={DELPI_MES_COPY.help.downtimesAnalytics}
            ariaLabel="Ajuda: indicadores de paradas"
          />
        </h3>
        <button
          type="button"
          className="delpi-mes-analytics__toggle"
          aria-expanded={open}
          aria-controls="downtimes-analytics-body"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <ChevronUp aria-hidden="true" /> : <ChevronDown aria-hidden="true" />}
          {open ? "Recolher análise" : "Expandir análise"}
        </button>
      </div>

      {!open ? null : analytics.loading && !data ? (
        <LoadingState
          classNames={loadingClasses}
          defaultMessage="Calculando os indicadores do período…"
        />
      ) : analytics.error && !data ? (
        <div className="delpi-mes-analytics__error" role="alert">
          <p>Não foi possível calcular os indicadores: {analytics.error}</p>
          <button type="button" onClick={() => void analytics.refresh()}>
            Tentar novamente
          </button>
        </div>
      ) : !data ? (
        <p className="delpi-mes-analytics__hint" role="status">
          Defina o início do período para ver a análise gerencial.
        </p>
      ) : (
        <div id="downtimes-analytics-body" className="delpi-mes-analytics__body">
          {analytics.refreshing ? (
            <p className="delpi-mes-downtimes__stale" role="status">
              Atualizando indicadores…
            </p>
          ) : null}
          {analytics.error && data ? (
            <p className="delpi-mes-downtimes__stale" role="status">
              Últimos indicadores mantidos. A atualização falhou: {analytics.error}
            </p>
          ) : null}
          {data.quality.partial ? (
            <p className="delpi-mes-analytics__warning" role="alert">
              {DELPI_MES_COPY.help.downtimesAnalyticsPartial}
            </p>
          ) : null}
          {data.quality.overlapDetected ? (
            <p className="delpi-mes-analytics__note" role="note">
              O histórico contém paradas sobrepostas (
              {formatHoursMinutes(data.quality.overlapSeconds)} em comum).
              O tempo total usa a união temporal por centro de trabalho; a soma
              atribuída às ocorrências ({formatHoursMinutes(data.summary.attributedSeconds)})
              pode superar o total físico ({formatHoursMinutes(data.summary.totalStoppedSeconds)}).
            </p>
          ) : null}

          <div
            className="delpi-mes-analytics__kpis"
            role="group"
            aria-label="Indicadores de paradas do período"
          >
            <MetricKpiCard
              classNames={kpiClasses}
              className="delpi-mes-analytics__kpi--featured"
              label="Tempo total parado"
              value={formatHoursMinutes(data.summary.totalStoppedSeconds)}
              hint="União temporal deduplicada por centro de trabalho"
              icon={<Timer aria-hidden="true" />}
            />
            <MetricKpiCard
              classNames={kpiClasses}
              label="Ocorrências"
              value={data.summary.occurrencesCount.toLocaleString("pt-BR")}
              hint="Eventos de parada com tempo dentro do período"
              icon={<ClipboardList aria-hidden="true" />}
            />
            <MetricKpiCard
              classNames={kpiClasses}
              label="Duração média"
              value={formatHoursMinutes(data.summary.averageOccurrenceSeconds)}
              hint="Tempo atribuído dividido pelas ocorrências"
              icon={<Hourglass aria-hidden="true" />}
            />
            <MetricKpiCard
              classNames={kpiClasses}
              label="Pendentes de classificação"
              value={data.summary.pendingCount.toLocaleString("pt-BR")}
              hint="Ocorrências sem motivo confirmado"
              icon={<Tag aria-hidden="true" />}
              tone={data.summary.pendingCount > 0 ? "warning" : "default"}
            />
            <MetricKpiCard
              classNames={kpiClasses}
              label="Em aberto agora"
              value={data.summary.openCount.toLocaleString("pt-BR")}
              hint="Paradas ainda abertas no instante da consulta"
              icon={<OctagonAlert aria-hidden="true" />}
              tone={data.summary.openCount > 0 ? "negative" : "default"}
            />
          </div>

          <div className="delpi-mes-analytics__grid">
            <ChartCard
              title="Pareto de motivos"
              titleHint={DELPI_MES_COPY.help.downtimesAnalyticsPareto}
              classNames={cardClasses}
            >
              <HorizontalValueBars
                prefix="delpi-mes"
                classNames={barsClasses}
                aria-label="Motivos ordenados por tempo de parada"
                emptyMessage="Nenhuma parada no período."
                formatValue={formatHoursMinutes}
                items={data.byReason.map((group) => ({
                  id: group.key,
                  label: describeReason(group),
                  value: group.seconds,
                  meta:
                    group.percentOfAttributed.toLocaleString("pt-BR") +
                    "% · " +
                    group.occurrencesCount.toLocaleString("pt-BR") +
                    " ocorr. · acum. " +
                    group.cumulativePercent.toLocaleString("pt-BR") +
                    "%",
                }))}
                onItemClick={(item) => {
                  const group = data.byReason.find((entry) => entry.key === item.id);
                  if (group) onSelectReasonGroup(group);
                }}
              />
            </ChartCard>

            <ChartCard
              title="Centros de trabalho"
              titleHint={DELPI_MES_COPY.help.downtimesAnalyticsCenters}
              classNames={cardClasses}
            >
              <HorizontalValueBars
                prefix="delpi-mes"
                classNames={barsClasses}
                aria-label="Centros de trabalho ordenados por tempo de parada"
                emptyMessage="Nenhuma parada no período."
                formatValue={formatHoursMinutes}
                items={data.byWorkCenter.map((entry) => ({
                  id: entry.workCenter,
                  label: entry.workCenter,
                  value: entry.seconds,
                  meta:
                    entry.occurrencesCount.toLocaleString("pt-BR") +
                    " ocorr. · média " +
                    formatHoursMinutes(entry.averageSeconds) +
                    " · " +
                    entry.percentOfTotal.toLocaleString("pt-BR") +
                    "%",
                }))}
                onItemClick={(item) => onSelectWorkCenter(item.id)}
              />
            </ChartCard>

            <ChartCard
              title="Evolução diária"
              titleHint={DELPI_MES_COPY.help.downtimesAnalyticsDaily}
              classNames={cardClasses}
              headerActions={
                <label className="delpi-mes-analytics__metric">
                  Métrica
                  <select
                    value={metric}
                    onChange={(event) =>
                      setMetric(event.target.value as AnalyticsMetric)
                    }
                  >
                    <option value="seconds">Tempo parado</option>
                    <option value="occurrences">Ocorrências</option>
                  </select>
                </label>
              }
            >
              <BarSeriesChart
                points={daySeriesPoints(data.byDay, metric)}
                emptyMessage="Nenhuma parada no período."
                className="delpi-mes-analytics__daily-chart"
              />
              {data.byDay.some((day) => day.occurrencesCount > 0) ? (
                <div
                  className="delpi-mes-analytics__day-chips"
                  aria-label="Filtrar a lista por dia"
                >
                  {data.byDay
                    .filter((day) => day.occurrencesCount > 0)
                    .map((day) => (
                      <button
                        key={day.date}
                        type="button"
                        onClick={() => onSelectDay(day.date)}
                        title={
                          "Ver " +
                          day.occurrencesCount.toLocaleString("pt-BR") +
                          " ocorrência(s) de " +
                          dayKeyLabel(day.date)
                        }
                      >
                        {dayKeyLabel(day.date)}
                      </button>
                    ))}
                </div>
              ) : null}
            </ChartCard>

            <ChartCard
              title="Concentração por dia da semana e hora"
              titleHint={DELPI_MES_COPY.help.downtimesAnalyticsHeatmap}
              classNames={cardClasses}
            >
              <div className="delpi-mes-heatmap" role="region" aria-label="Mapa de calor de paradas">
                <table>
                  <thead>
                    <tr>
                      <th scope="col"><span className="delpi-mes-sr-only">Dia da semana</span></th>
                      {Array.from({ length: 24 }, (_, hour) => (
                        <th key={hour} scope="col">{hour}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {heatmap.rows.map((row) => (
                      <tr key={row.weekday}>
                        <th scope="row">{row.weekdayLabel}</th>
                        {row.hours.map((cell) => (
                          <td
                            key={cell.hour}
                            className="delpi-mes-heatmap__cell"
                            data-level={
                              cell.seconds === 0 || heatmap.maxSeconds === 0
                                ? 0
                                : Math.min(4, 1 + Math.floor((cell.seconds / heatmap.maxSeconds) * 4))
                            }
                            title={
                              row.weekdayLabel +
                              " " +
                              String(cell.hour).padStart(2, "0") +
                              "h–" +
                              String((cell.hour + 1) % 24).padStart(2, "0") +
                              "h · " +
                              formatHoursMinutes(cell.seconds) +
                              " · " +
                              cell.occurrencesCount.toLocaleString("pt-BR") +
                              " ocorr."
                            }
                          >
                            <span className="delpi-mes-sr-only">
                              {formatHoursMinutes(cell.seconds)}
                            </span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="delpi-mes-heatmap__legend">
                  Intensidade = tempo parado na célula (0 a{" "}
                  {formatHoursMinutes(heatmap.maxSeconds)})
                </p>
              </div>
            </ChartCard>
          </div>
        </div>
      )}
    </section>
  );
}
