import {
  CHART_COLORS_DEPARTMENTAL,
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  createDashboardSegmentToggle,
  MultiTypeSeriesChart,
} from "@delpi/plugin-ui/index";
import { Check, Timer } from "lucide-react";
import { useMemo, useState } from "react";

import { ChartCard } from "../components/ChartCard";
import { BillingDueDetailModal } from "../components/BillingDueDetailModal";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useOverview } from "../hooks/useOverview";
import type {
  BillingDueTodayCheck,
  BillingDueTodayLine,
  OverviewPayload,
  PpcBranch,
  ProblemIssue,
  VolumeView,
} from "../types";
import { formatOpQuantity } from "../utils/formatOpQuantity";
import { billingDueInvoicedPercent } from "../utils/billingDueProgress";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

const KpiCard = createDashboardKpiCard({
  prefix: "ppc",
  labels: copy.kpi,
});

const LoadingCard = createDashboardLoadingActivityCard({
  prefix: "ppc",
  labels: {
    progressRemaining: (n) => `Faltam ${n}%`,
    progressAriaDeterminate: (n) => `Faltam ${n} por cento`,
    progressAriaIndeterminate: copy.home.loading,
  },
});

const VolumeViewToggle = createDashboardSegmentToggle("ppc");

/** Mesmo motor Recharts do dashboard de produção (`OtdEvolutionChart` → kit). */
const OTD_CHART_HEIGHT = 196;
/** Altura do card featured de volume — alinhada ao «Produção no tempo» do apontamento. */
const VOLUME_CHART_HEIGHT = 280;

/** Cores das séries OTD no dashboard de produção: SC = [4], ES = [5]. */
function otdSeriesColor(branch: PpcBranch): string {
  return branch === "02"
    ? (CHART_COLORS_DEPARTMENTAL[5] ?? CHART_COLORS_DEPARTMENTAL[1]!)
    : CHART_COLORS_DEPARTMENTAL[4]!;
}

/** Azul secundário Delpi — colunas do volume (referência visual do plano de produção). */
const VOLUME_COLUMN_COLOR = "var(--ppc-title, #003866)";
/** Ano anterior — tom mais claro da mesma família. */
const VOLUME_PRIOR_COLUMN_COLOR = "color-mix(in srgb, var(--ppc-title, #003866) 42%, white)";

const VOLUME_VIEW_OPTIONS = [
  { value: "day" as const, label: copy.home.volumeViewDay },
  { value: "month_yoy" as const, label: copy.home.volumeViewMonthYoy },
];

function formatChartPercent(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return `${new Intl.NumberFormat("pt-BR", {
    maximumFractionDigits: 0,
  }).format(value)}%`;
}

function formatChartQty(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("pt-BR", {
    maximumFractionDigits: value >= 100 ? 0 : 1,
  }).format(value);
}

function formatPct(value: number | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)}%`;
}

function formatPeriod(period: OverviewPayload["period"]): string {
  const start = period.start_date.split("-").reverse().join("/");
  const end = period.end_date.split("-").reverse().join("/");
  return `${start} — ${end}`;
}

function formatDueDate(value: string | null | undefined): string {
  if (!value || value.length < 10) return "—";
  return `${value.slice(8, 10)}/${value.slice(5, 7)}`;
}

function billingCheckLabel(check: BillingDueTodayCheck): string {
  if (check === "stock") return copy.home.billingDueCheckStock;
  if (check === "invoiced") return copy.home.billingDueCheckInvoiced;
  return copy.home.billingDueCheckPending;
}

function BillingCheckMark({ check }: { check: BillingDueTodayCheck }) {
  if (check === "pending") {
    return (
      <span
        className="ppc-billing-check ppc-billing-check--pending"
        title={billingCheckLabel(check)}
        aria-label={billingCheckLabel(check)}
      />
    );
  }
  return (
    <span
      className={`ppc-billing-check ppc-billing-check--${check}`}
      title={billingCheckLabel(check)}
      aria-label={billingCheckLabel(check)}
    >
      <Check size={14} strokeWidth={2.5} aria-hidden />
    </span>
  );
}

type OverviewPageProps = {
  branch: PpcBranch;
};

export function OverviewPage({ branch }: OverviewPageProps) {
  const [volumeView, setVolumeView] = useState<VolumeView>("day");
  const [selectedBillingLine, setSelectedBillingLine] = useState<BillingDueTodayLine | null>(
    null,
  );
  const { data, loading, error, reload } = useOverview(branch, volumeView);

  /** A fila de atraso leva ao rastreio na Carga máquina, onde a OP pode ser reprogramada. */
  const openIssue = (issue: ProblemIssue) => {
    const query = issue.production_order ?? issue.product_code;
    if (!query) return;
    navigatePpc(
      buildPpcHref({
        subpluginId: "machine-load",
        branch,
        locateQuery: query,
      }),
    );
  };

  const otdRows = (data?.otd.series ?? [])
    .filter((point) => point.value != null)
    .map((point) => ({ periodo: point.label, otd: point.value }));

  const isMonthYoy = (data?.production_volume?.view ?? volumeView) === "month_yoy";

  const volumeRows = useMemo(
    () =>
      (data?.production_volume?.series ?? [])
        .filter((point) => point.value != null)
        .map((point) =>
          isMonthYoy
            ? {
                periodo: point.label,
                prior: point.prior_value ?? null,
                produced: point.value,
              }
            : {
                periodo: point.label,
                produced: point.value,
              },
        ),
    [data?.production_volume?.series, isMonthYoy],
  );

  const volumeHint = useMemo(() => {
    const volume = data?.production_volume;
    if (!volume) return "";
    const parts = [copy.home.volumeTotal(formatChartQty(volume.total ?? 0))];
    if (volume.view === "month_yoy" && volume.prior_total != null) {
      parts.push(copy.home.volumePriorTotal(formatChartQty(volume.prior_total)));
    } else if (volume.weekday_average != null) {
      parts.push(
        copy.home.volumeWeekdayAverage(
          formatChartQty(volume.weekday_average),
          volume.weekday_day_count ?? 0,
        ),
      );
    }
    return parts.join(" · ");
  }, [data?.production_volume]);

  const volumeSeries = useMemo(() => {
    const current = {
      dataKey: "produced",
      name:
        isMonthYoy && data?.production_volume?.current_year != null
          ? String(data.production_volume.current_year)
          : copy.home.volumeSeries,
      fill: VOLUME_COLUMN_COLOR,
    };
    if (!isMonthYoy) return [current];
    // Ano mais antigo à esquerda do par de colunas (Recharts segue a ordem do array).
    return [
      {
        dataKey: "prior",
        name:
          data?.production_volume?.prior_year != null
            ? String(data.production_volume.prior_year)
            : copy.home.volumeSeriesPrior,
        fill: VOLUME_PRIOR_COLUMN_COLOR,
      },
      current,
    ];
  }, [data?.production_volume?.current_year, data?.production_volume?.prior_year, isMonthYoy]);

  const billing = data?.billing_due_today;
  const billingTotal = billing?.line_count ?? 0;
  const billingInvoiced = billing?.invoiced_count ?? 0;
  const billingProgressPct = billingDueInvoicedPercent(billingInvoiced, billingTotal);

  return (
    <div className="ppc-page-stack ppc-page-stack--home">
      <PpcWorkspaceHeader
        title={copy.home.title}
        subtitle={copy.home.heroLead}
        period={data ? formatPeriod(data.period) : undefined}
        titleHint={helpTooltips.home}
        branch={branch}
        subpluginId="home"
        onRefresh={reload}
      />

      {loading && !data ? (
        <LoadingCard title={copy.home.loading} description={copy.home.loadingHint} />
      ) : null}

      {error ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {error || copy.home.loadError}
        </div>
      ) : null}

      {data ? (
        <div className="ppc-board">
          <div className="ppc-board-grid">
            <KpiCard
              className="ppc-board-card ppc-board-card--otd"
              title={copy.home.otdTitle}
              titleHint={copy.home.otdHint}
              value={formatPct(data.otd.on_time_delivery_pct)}
              subtitle={`${copy.branch[branch]} · ${formatPeriod(data.period)}`}
              icon={<Timer size={22} strokeWidth={1.75} />}
              footer={
                <div className="ppc-otd-chart" aria-label={copy.home.otdChart}>
                  {otdRows.length === 0 ? (
                    <p className="ppc-otd-chart__empty">{copy.home.otdEmptyChart}</p>
                  ) : (
                    <MultiTypeSeriesChart
                      data={otdRows}
                      categoryKey="periodo"
                      series={[
                        {
                          dataKey: "otd",
                          name: copy.home.otdChart,
                          fill: otdSeriesColor(branch),
                        },
                      ]}
                      chartType="line"
                      height={OTD_CHART_HEIGHT}
                      showLegend={false}
                      formatY={formatChartPercent}
                      formatTooltipValue={formatChartPercent}
                      margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
                    />
                  )}
                </div>
              }
            />

            <article className="ppc-board-list ppc-board-billing" aria-label={copy.home.billingDueTitle}>
              <header className="ppc-board-list__head">
                <div className="ppc-board-billing__title-row">
                  <h2 className="ppc-board-list__title">{copy.home.billingDueTitle}</h2>
                  {billingTotal > 0 ? (
                    <span className="ppc-board-billing__pct">
                      {copy.home.billingDueProgressLabel(billingProgressPct)}
                    </span>
                  ) : null}
                </div>
                <p className="ppc-board-list__hint">
                  {copy.home.billingDueSummary(
                    billing?.pending_count ?? 0,
                    billing?.stock_count ?? 0,
                    billingInvoiced,
                  )}
                </p>
                {billingTotal > 0 ? (
                  <div
                    className="ppc-board-billing__progress"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={billingProgressPct}
                    aria-label={copy.home.billingDueProgressAria(
                      billingProgressPct,
                      billingInvoiced,
                      billingTotal,
                    )}
                  >
                    <span
                      className="ppc-board-billing__progress-fill"
                      style={{ width: `${billingProgressPct}%` }}
                    />
                  </div>
                ) : null}
              </header>
              {(data.billing_due_today?.customers.length ?? 0) === 0 ? (
                <p className="ppc-board-list__empty">{copy.home.billingDueEmpty}</p>
              ) : (
                <ul className="ppc-board-list__scroll">
                  {(data.billing_due_today?.customers ?? []).map((customer) => (
                    <li
                      key={`${customer.customer_code}|${customer.customer_store}|${customer.customer_name}`}
                      className="ppc-billing-customer"
                    >
                      <div className="ppc-billing-customer__head">
                        <strong>{customer.customer_name || "—"}</strong>
                        <span>
                          {customer.line_count} ite{customer.line_count === 1 ? "m" : "ns"}
                        </span>
                      </div>
                      <ul className="ppc-billing-customer__lines">
                        {customer.lines.map((line) => (
                          <li key={line.id}>
                            <button
                              type="button"
                              className="ppc-billing-line"
                              onClick={() => setSelectedBillingLine(line)}
                            >
                              <BillingCheckMark check={line.check} />
                              <span className="ppc-billing-line__body">
                                <strong>{line.product_code || "—"}</strong>
                                <span>
                                  {copy.home.billingDueOrder} {line.sales_order || "—"}
                                  {line.line_item ? `/${line.line_item}` : ""}
                                  {" · "}
                                  {formatDueDate(line.due_date)}
                                  {line.check !== "invoiced" ? (
                                    <>
                                      {" · "}
                                      {copy.home.billingDueQty}{" "}
                                      {formatOpQuantity(line.open_quantity)}
                                    </>
                                  ) : null}
                                </span>
                              </span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="ppc-board-list" aria-label={copy.home.delayedListTitle}>
              <header className="ppc-board-list__head">
                <h2 className="ppc-board-list__title">{copy.home.delayedListTitle}</h2>
                <p className="ppc-board-list__hint">{copy.home.delayedListHint}</p>
              </header>
              {data.delayed_ops.items.length === 0 ? (
                <p className="ppc-board-list__empty">{copy.home.delayedEmpty}</p>
              ) : (
                <ul className="ppc-board-list__scroll">
                  {data.delayed_ops.items.map((item) => (
                    <li key={item.id}>
                      <button
                        type="button"
                        className="ppc-board-list__row"
                        onClick={() => openIssue(item)}
                      >
                        <span className="ppc-board-list__product">
                          <strong>{item.product_code ?? "—"}</strong>
                          <span>{item.product_description ?? item.title}</span>
                        </span>
                        <span className="ppc-board-list__meta">
                          <span>
                            {copy.problemAnalysis.order} {item.production_order ?? "—"}
                          </span>
                          <span>
                            {copy.home.pending} {formatOpQuantity(item.metrics.pending_qty)}
                          </span>
                          <span>
                            {item.delay_days} {copy.problemAnalysis.days}
                          </span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>

          <section className="ppc-volume-section" aria-label={copy.home.volumeTitle}>
            <ChartCard
              title={copy.home.volumeTitle}
              titleHint={helpTooltips.productionVolume}
              hint={volumeHint}
              className="ppc-volume-card"
              headerActions={
                <VolumeViewToggle
                  ariaLabel={copy.home.volumeViewAria}
                  idPrefix="ppc-volume-view"
                  size="sm"
                  value={volumeView}
                  onChange={setVolumeView}
                  options={VOLUME_VIEW_OPTIONS}
                />
              }
            >
              {volumeRows.length === 0 ? (
                <p className="ppc-volume-card__empty">{copy.home.volumeEmpty}</p>
              ) : (
                <div className="ppc-volume-chart">
                  <MultiTypeSeriesChart
                    data={volumeRows}
                    categoryKey="periodo"
                    series={volumeSeries}
                    chartType="column"
                    height={VOLUME_CHART_HEIGHT}
                    showLegend={isMonthYoy}
                    showValueLabels
                    formatY={formatChartQty}
                    formatTooltipValue={formatChartQty}
                    margin={{ top: 28, right: 12, left: 4, bottom: 4 }}
                  />
                </div>
              )}
            </ChartCard>
          </section>
        </div>
      ) : null}

      <BillingDueDetailModal
        line={selectedBillingLine}
        branch={branch}
        onClose={() => setSelectedBillingLine(null)}
      />
    </div>
  );
}
