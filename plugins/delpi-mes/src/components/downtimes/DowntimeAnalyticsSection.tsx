import {
  AnchoredPanelPortal,
  AreaSeriesChart,
  ChartCard,
  HelpTooltip,
  HorizontalValueBars,
  LoadingState,
  MetricKpiCard,
  SegmentToggle,
  chartCardBemClasses,
  horizontalValueBarsBemClasses,
  loadingStatePanelBemClasses,
  metricKpiCardBemClasses,
  type SeriesChartPartRef,
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
import { useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";

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
import { usePortalColorScheme } from "../../utils/portalColorScheme";

const RANKING_VISIBLE_COUNT = 8;

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
  selectedDayKey,
}: {
  analytics: ReturnType<typeof useDowntimeAnalytics>;
  onSelectReasonGroup: (group: DowntimeAnalyticsReasonGroup) => void;
  onSelectWorkCenter: (workCenter: string) => void;
  onSelectDay: (dayKey: string) => void;
  selectedDayKey?: string | null;
}) {
  const [open, setOpen] = useState(true);
  const [metric, setMetric] = useState<AnalyticsMetric>("seconds");
  const [expandedReasons, setExpandedReasons] = useState(false);
  const [expandedCenters, setExpandedCenters] = useState(false);
  const [hoveredDayIndex, setHoveredDayIndex] = useState<number | null>(null);
  const trendAnchorRef = useRef<HTMLElement | null>(null);
  const trendTooltipRef = useRef<HTMLDivElement | null>(null);
  const colorScheme = usePortalColorScheme();
  const data = analytics.data;
  const heatmap = useMemo(
    () => buildHeatmapRows(data?.byWeekdayHour ?? []),
    [data],
  );
  const selectedDayIndex = useMemo(
    () =>
      selectedDayKey
        ? (data?.byDay.findIndex((day) => day.date === selectedDayKey) ?? -1)
        : -1,
    [data, selectedDayKey],
  );

  const handleTrendPointerOver = (event: ReactPointerEvent<HTMLDivElement>) => {
    const part = (event.target as HTMLElement).closest?.("[data-chart-part]");
    const match = /^marker:\d+:(\d+)$/.exec(
      part?.getAttribute("data-chart-part") ?? "",
    );
    if (!part || !match) {
      setHoveredDayIndex(null);
      return;
    }
    trendAnchorRef.current = part as HTMLElement;
    setHoveredDayIndex(Number(match[1]));
  };

  const handleTrendPartPointerDown = (ref: SeriesChartPartRef) => {
    if (ref.kind !== "marker" || ref.pointIndex == null) return;
    const day = data?.byDay[ref.pointIndex];
    if (day) onSelectDay(day.date);
  };

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
              className="delpi-mes-analytics__card--pareto"
            >
              <HorizontalValueBars
                prefix="delpi-mes"
                classNames={barsClasses}
                layout="stacked"
                aria-label="Motivos ordenados por tempo de parada"
                emptyMessage="Nenhuma parada no período."
                formatValue={formatHoursMinutes}
                items={(expandedReasons
                  ? data.byReason
                  : data.byReason.slice(0, RANKING_VISIBLE_COUNT)
                ).map((group) => ({
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
              {data.byReason.length > RANKING_VISIBLE_COUNT ? (
                <button
                  type="button"
                  className="delpi-mes-analytics__more"
                  aria-expanded={expandedReasons}
                  onClick={() => setExpandedReasons((value) => !value)}
                >
                  {expandedReasons
                    ? "Mostrar menos"
                    : "Ver todos os " +
                      data.byReason.length.toLocaleString("pt-BR") +
                      " motivos"}
                </button>
              ) : null}
            </ChartCard>

            <ChartCard
              title="Centros de trabalho"
              titleHint={DELPI_MES_COPY.help.downtimesAnalyticsCenters}
              classNames={cardClasses}
              className="delpi-mes-analytics__card--centers"
            >
              <HorizontalValueBars
                prefix="delpi-mes"
                classNames={barsClasses}
                layout="stacked"
                aria-label="Centros de trabalho ordenados por tempo de parada"
                emptyMessage="Nenhuma parada no período."
                formatValue={formatHoursMinutes}
                items={(expandedCenters
                  ? data.byWorkCenter
                  : data.byWorkCenter.slice(0, RANKING_VISIBLE_COUNT)
                ).map((entry) => ({
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
              {data.byWorkCenter.length > RANKING_VISIBLE_COUNT ? (
                <button
                  type="button"
                  className="delpi-mes-analytics__more"
                  aria-expanded={expandedCenters}
                  onClick={() => setExpandedCenters((value) => !value)}
                >
                  {expandedCenters
                    ? "Mostrar menos"
                    : "Ver todos os " +
                      data.byWorkCenter.length.toLocaleString("pt-BR") +
                      " centros"}
                </button>
              ) : null}
            </ChartCard>

            <ChartCard
              title="Evolução diária"
              titleHint={DELPI_MES_COPY.help.downtimesAnalyticsDaily}
              classNames={cardClasses}
              className="delpi-mes-analytics__card--wide"
              headerActions={
                <SegmentToggle
                  ariaLabel="Métrica da evolução diária"
                  size="sm"
                  widthMode="content"
                  value={metric}
                  onChange={(value) => setMetric(value)}
                  options={[
                    { value: "seconds", label: "Tempo parado" },
                    { value: "occurrences", label: "Ocorrências" },
                  ]}
                />
              }
            >
              <div
                className="delpi-mes-analytics__trend"
                onPointerOver={handleTrendPointerOver}
                onPointerLeave={() => setHoveredDayIndex(null)}
              >
                <AreaSeriesChart
                  points={daySeriesPoints(data.byDay, metric)}
                  emptyMessage="Nenhuma parada no período."
                  options={{
                    theme: colorScheme,
                    backgroundColor: "transparent",
                    seriesColor:
                      colorScheme === "dark" ? "#4fc3f7" : "#00a6de",
                    smoothLines: true,
                    areaFillGradient: true,
                    markerMode: "all",
                    decimalPlaces: 0,
                  }}
                  interaction={{
                    selectedPart:
                      selectedDayIndex >= 0
                        ? {
                            kind: "marker",
                            seriesIndex: 0,
                            pointIndex: selectedDayIndex,
                          }
                        : null,
                    onPartPointerDown: handleTrendPartPointerDown,
                  }}
                />
                {hoveredDayIndex != null && data.byDay[hoveredDayIndex] ? (
                  <AnchoredPanelPortal
                    open
                    anchorRef={trendAnchorRef}
                    panelRef={trendTooltipRef}
                    variant="bare"
                    role="tooltip"
                    className="delpi-mes-analytics__trend-tooltip"
                    preferredPlacement="top"
                  >
                    <strong>{dayKeyLabel(data.byDay[hoveredDayIndex].date)}</strong>
                    <span>
                      {formatHoursMinutes(data.byDay[hoveredDayIndex].seconds)}
                      {" · "}
                      {data.byDay[hoveredDayIndex].occurrencesCount.toLocaleString(
                        "pt-BR",
                      )}{" "}
                      ocorr.
                    </span>
                  </AnchoredPanelPortal>
                ) : null}
              </div>
              <label className="delpi-mes-analytics__day-select">
                Filtrar a lista por dia
                <select
                  value={selectedDayKey ?? ""}
                  onChange={(event) => {
                    if (event.target.value) onSelectDay(event.target.value);
                  }}
                >
                  <option value="">Escolher dia…</option>
                  {data.byDay
                    .filter((day) => day.occurrencesCount > 0)
                    .map((day) => (
                      <option key={day.date} value={day.date}>
                        {dayKeyLabel(day.date) +
                          " · " +
                          day.occurrencesCount.toLocaleString("pt-BR") +
                          " ocorr."}
                      </option>
                    ))}
                </select>
              </label>
            </ChartCard>

            <ChartCard
              title="Concentração por dia da semana e hora"
              titleHint={DELPI_MES_COPY.help.downtimesAnalyticsHeatmap}
              classNames={cardClasses}
              className="delpi-mes-analytics__card--wide"
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
                            tabIndex={0}
                            data-level={
                              cell.seconds === 0 || heatmap.maxSeconds === 0
                                ? 0
                                : Math.min(4, 1 + Math.floor((cell.seconds / heatmap.maxSeconds) * 4))
                            }
                            aria-label={
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
                  <span className="delpi-mes-heatmap__legend-scale" aria-hidden="true">
                    {[0, 1, 2, 3, 4].map((level) => (
                      <i key={level} data-level={level} />
                    ))}
                  </span>
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
