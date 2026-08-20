import {
  createDashboardKpiCard,
  createDashboardLoadingActivityCard,
  DelpiLogoMark,
  LineSeriesChart,
} from "@delpi/plugin-ui/index";
import { ClockAlert, Timer } from "lucide-react";

import { copy } from "../content/copy";
import { useOverview } from "../hooks/useOverview";
import type { OverviewPayload, PpcBranch, ProblemIssue } from "../types";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { helpTooltips } from "../content/helpTooltips";
import { formatOpQuantity } from "../utils/formatOpQuantity";

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

type OverviewPageProps = {
  branch: PpcBranch;
};

export function OverviewPage({ branch }: OverviewPageProps) {
  const { data, loading, error, reload } = useOverview(branch);

  const openIssue = (issue: ProblemIssue) => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "problem-analysis",
        branch,
        issueId: issue.id,
      }),
    );
  };

  const seriesPoints = (data?.otd.series ?? [])
    .filter((point) => point.value != null)
    .map((point) => ({ label: point.label, value: point.value }));

  return (
    <div className="ppc-page-stack ppc-page-stack--home">
      <PpcWorkspaceHeader
        title={copy.home.title}
        subtitle={copy.home.subtitle}
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
          <section className="ppc-hero" aria-label={copy.productName}>
            <div className="ppc-hero__brand">
              <DelpiLogoMark className="ppc-hero__logo" title="DELPI" />
            </div>
            <div className="ppc-hero__copy">
              <p className="ppc-hero__kicker">{copy.home.kicker}</p>
              <p className="ppc-hero__lead">{copy.home.heroLead}</p>
              <p className="ppc-hero__period">{formatPeriod(data.period)}</p>
            </div>
          </section>

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
                  <LineSeriesChart
                    points={seriesPoints}
                    emptyMessage={copy.home.otdEmptyChart}
                    options={{
                      title: copy.home.otdChart,
                      showLegend: false,
                      showXAxisTitle: false,
                      showYAxisTitle: false,
                      valueFormat: "number",
                      decimalPlaces: 1,
                      categoryLabelFormat: "raw",
                    }}
                  />
                </div>
              }
            />

            <KpiCard
              className="ppc-board-card"
              title={copy.home.delayedTitle}
              titleHint={copy.home.delayedHint}
              value={String(data.delayed_ops.count)}
              subtitle={
                data.delayed_ops.late_percentage != null
                  ? `${formatPct(data.delayed_ops.late_percentage)} · ${copy.home.otdLateOps(data.otd.late_ops)}`
                  : copy.home.otdLateOps(data.otd.late_ops)
              }
              icon={<ClockAlert size={22} strokeWidth={1.75} />}
            />

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
        </div>
      ) : null}
    </div>
  );
}
