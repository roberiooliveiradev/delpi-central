import {
  ChartCard,
  HelpTooltip,
  HorizontalValueBars,
  LoadingState,
  MetricStrip,
  chartCardBemClasses,
  horizontalValueBarsBemClasses,
  loadingStatePanelBemClasses,
  metricStripBemClasses,
} from "@delpi/plugin-ui/index";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

import { DELPI_MES_COPY } from "../../content/copy";
import type { useDowntimeInsights } from "../../hooks/useDowntimeInsights";
import type { DowntimeInsightsDelta } from "../../types/mes";
import { formatHoursMinutes } from "../../utils/dayTimeline";
import { formatDateTime } from "../../utils/downtimesPresentation";

const loadingClasses = loadingStatePanelBemClasses("delpi-mes");
const metricClasses = metricStripBemClasses("delpi-mes");
const cardClasses = chartCardBemClasses("delpi-mes", { headerLayout: "titleRow" });
const barsClasses = horizontalValueBarsBemClasses("delpi-mes");

function deltaLabel(delta: DowntimeInsightsDelta | undefined, unit: "seconds" | "count"): string {
  if (!delta) return "—";
  const current =
    unit === "seconds"
      ? formatHoursMinutes(delta.current)
      : String(delta.current);
  if (delta.percent === null) return current + " (sem base anterior)";
  const sign = delta.percent > 0 ? "+" : "";
  return current + " (" + sign + String(delta.percent) + "% vs. período anterior)";
}

/** Painel de análise avançada de paradas (Etapa 6): comparação com o
 * período anterior equivalente, reincidência por CT+motivo, ocorrências
 * críticas por regras parametrizadas no owner, pendências gerenciais e
 * evidência antes/depois dos tratamentos concluídos. Render-only — todo
 * o cálculo e os parâmetros vêm do Production Control. */
export function DowntimeInsightsSection({
  insights,
  onSelectGroup,
}: {
  insights: ReturnType<typeof useDowntimeInsights>;
  onSelectGroup?: (workCenter: string, reasonCode: string | null) => void;
}) {
  const [open, setOpen] = useState(true);
  const data = insights.data;
  const deltas = data?.comparison.deltas ?? {};
  const rules = data?.critical.rules ?? {};
  const noCriticalRule = Object.values(rules).every(
    (rule) => !rule.configured,
  );

  return (
    <section
      className="delpi-mes-insights"
      aria-labelledby="downtimes-insights-title"
      aria-busy={insights.loading || insights.refreshing}
    >
      <div className="delpi-mes-insights__head">
        <h3 id="downtimes-insights-title">
          Análise avançada
          <HelpTooltip
            content={DELPI_MES_COPY.help.downtimesInsights}
            ariaLabel="Ajuda: análise avançada de paradas"
          />
        </h3>
        <button
          type="button"
          className="delpi-mes-insights__toggle"
          aria-expanded={open}
          aria-controls="downtimes-insights-body"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <ChevronUp aria-hidden="true" /> : <ChevronDown aria-hidden="true" />}
          {open ? "Recolher análise avançada" : "Expandir análise avançada"}
        </button>
      </div>

      {!open ? null : insights.loading && !data ? (
        <LoadingState
          classNames={loadingClasses}
          defaultMessage="Calculando a análise avançada…"
        />
      ) : insights.error && !data ? (
        <div className="delpi-mes-insights__error" role="alert">
          <p>Não foi possível calcular a análise avançada: {insights.error}</p>
          <button type="button" onClick={() => void insights.refresh()}>
            Tentar novamente
          </button>
        </div>
      ) : !data ? (
        <p className="delpi-mes-insights__hint" role="status">
          Defina o início do período para ver a análise avançada.
        </p>
      ) : (
        <div id="downtimes-insights-body" className="delpi-mes-insights__body">
          {insights.refreshing ? (
            <p className="delpi-mes-downtimes__stale" role="status">
              Atualizando análise avançada…
            </p>
          ) : null}
          {insights.error && data ? (
            <p className="delpi-mes-downtimes__stale" role="status">
              Última análise mantida. A atualização falhou: {insights.error}
            </p>
          ) : null}
          {(data.quality.telemetryGaps ?? []).length > 0 ? (
            <p className="delpi-mes-insights__warning" role="alert">
              {DELPI_MES_COPY.help.downtimesInsightsTelemetryGaps}
            </p>
          ) : null}

          <MetricStrip
            classNames={metricClasses}
            density="compact"
            aria-label="Comparação com o período anterior equivalente"
            items={[
              {
                id: "total",
                label: "Tempo parado",
                value: deltaLabel(deltas.totalStoppedSeconds, "seconds"),
                description:
                  "Janela anterior equivalente: " +
                  data.comparison.previous.from.slice(0, 10) +
                  " a " +
                  data.comparison.previous.to.slice(0, 10),
              },
              {
                id: "occurrences",
                label: "Ocorrências",
                value: deltaLabel(deltas.occurrencesCount, "count"),
              },
              {
                id: "average",
                label: "Duração média",
                value: deltaLabel(deltas.averageOccurrenceSeconds, "seconds"),
              },
              {
                id: "pending",
                label: "Pendentes de classificação",
                value: deltaLabel(deltas.pendingCount, "count"),
              },
            ]}
          />

          <MetricStrip
            classNames={metricClasses}
            density="compact"
            aria-label="Pendências gerenciais"
            items={[
              {
                id: "unclassified",
                label: "Sem classificação",
                value: String(data.pendencies.unclassifiedCount),
              },
              {
                id: "treatments",
                label: "Tratamentos em aberto",
                value: String(data.pendencies.openTreatmentsCount),
              },
              {
                id: "openStops",
                label: "Paradas em aberto",
                value: String(data.pendencies.openStopsCount),
              },
            ]}
          />

          <div className="delpi-mes-insights__grid">
            <ChartCard
              title="Reincidência por centro de trabalho e motivo"
              titleHint={DELPI_MES_COPY.help.downtimesInsightsRecurrence}
              classNames={cardClasses}
            >
              <HorizontalValueBars
                prefix="delpi-mes"
                classNames={barsClasses}
                aria-label="Reincidências ordenadas por tempo de parada"
                emptyMessage="Nenhuma reincidência no período."
                formatValue={formatHoursMinutes}
                items={data.recurrence.slice(0, 8).map((group) => ({
                  id: group.workCenter + "|" + (group.reasonCode ?? "none"),
                  label:
                    group.workCenter +
                    " · " +
                    (group.reasonLabel ?? "Não classificado"),
                  value: group.seconds,
                  meta:
                    group.occurrencesCount.toLocaleString("pt-BR") +
                    " ocorr." +
                    (group.lastOccurrenceAt
                      ? " · última " + formatDateTime(group.lastOccurrenceAt)
                      : ""),
                }))}
                onItemClick={
                  onSelectGroup
                    ? (item) => {
                        const [workCenter, reason] = item.id.split("|");
                        onSelectGroup(
                          workCenter,
                          reason === "none" ? null : reason,
                        );
                      }
                    : undefined
                }
              />
            </ChartCard>

            <ChartCard
              title="Ocorrências críticas"
              titleHint={DELPI_MES_COPY.help.downtimesInsightsCritical}
              classNames={cardClasses}
            >
              {noCriticalRule ? (
                <p role="status">
                  Nenhuma regra de criticidade parametrizada. Os limites são
                  definidos pelo processo industrial no Production Control.
                </p>
              ) : data.critical.items.length === 0 ? (
                <p role="status">Nenhuma ocorrência crítica no período.</p>
              ) : (
                <ul className="delpi-mes-insights__critical-list">
                  {data.critical.items.map((item, index) => (
                    <li key={item.rule + ":" + String(item.downtimeId ?? index)}>
                      <strong>{item.workCenter}</strong>
                      {" · "}
                      {item.reasonLabel ?? "Não classificado"}
                      {" — "}
                      {item.rule === "openStopLongDuration"
                        ? "parada aberta há " +
                          formatHoursMinutes(item.elapsedSeconds ?? 0)
                        : String(item.occurrencesCount ?? 0) +
                          " ocorrências (" +
                          formatHoursMinutes(item.seconds ?? 0) +
                          ")"}
                    </li>
                  ))}
                </ul>
              )}
            </ChartCard>
          </div>

          <ChartCard
            title="Eficácia das ações concluídas"
            titleHint={DELPI_MES_COPY.help.downtimesInsightsEffectiveness}
            classNames={cardClasses}
          >
            {data.actionEffectiveness.length === 0 ? (
              <p role="status">
                Nenhum tratamento concluído com evidência suficiente no período.
              </p>
            ) : (
              <ul className="delpi-mes-insights__effectiveness-list">
                {data.actionEffectiveness.map((record) => (
                  <li key={record.downtimeId}>
                    <strong>{record.workCenter}</strong>
                    {" · "}
                    {record.reasonLabel ?? record.reasonCode}
                    {" — "}
                    {String(record.before.occurrences)} →{" "}
                    {String(record.after.occurrences)} ocorrências (
                    {formatHoursMinutes(record.before.seconds)} →{" "}
                    {formatHoursMinutes(record.after.seconds)}) em janelas de{" "}
                    {String(record.windowDays)} dias em torno de{" "}
                    {formatDateTime(record.concludedAt)}
                  </li>
                ))}
              </ul>
            )}
            <p className="delpi-mes-insights__note" role="note">
              {DELPI_MES_COPY.help.downtimesInsightsEvidenceNote}
            </p>
          </ChartCard>
        </div>
      )}
    </section>
  );
}
