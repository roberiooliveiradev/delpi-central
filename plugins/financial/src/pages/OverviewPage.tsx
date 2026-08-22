import { MultiTypeSeriesChart } from "@delpi/plugin-ui/index";
import { CalendarClock, Gauge, HandCoins, PiggyBank, Wallet } from "lucide-react";
import { useMemo } from "react";

import { FinBlockState } from "../components/FinBlockState";
import { FinChartCard, FinKpiCard, FinLoadingCard } from "../components/finUiKit";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useOverview } from "../hooks/useOverview";
import type { FinancialBranch, KpiBlock } from "../types";
import { formatPeriodRange, formatYearMonth } from "../utils/formatDates";
import {
  formatCompactCurrency,
  formatCurrency,
  formatDays,
  formatInteger,
  formatPercent,
  formatScore,
} from "../utils/formatNumbers";
import { buildFinancialHref, navigateFinancial } from "../utils/routeParser";

const SERIES_HEIGHT = 208;

function kpiValue(block: KpiBlock | undefined, kind: "currency" | "percent" | "days"): string {
  if (!block || block.available === false) return "—";
  if (kind === "currency") return formatCompactCurrency(block.value);
  if (kind === "days") return formatDays(block.value);
  return formatPercent(block.value);
}

function kpiGoal(block: KpiBlock | undefined, kind: "currency" | "percent" | "days"): string | null {
  if (!block || block.available === false || block.target === undefined) return null;
  if (kind === "currency") return formatCompactCurrency(block.target);
  if (kind === "days") return formatDays(block.target);
  return formatPercent(block.target);
}

function formatChartPercent(value: number): string {
  return Number.isFinite(value) ? formatPercent(value, 0) : "—";
}

type OverviewPageProps = {
  branch: FinancialBranch;
};

export function OverviewPage({ branch }: OverviewPageProps) {
  const { data, loading, error, reload } = useOverview(branch);
  const blocks = data?.blocks;

  const delinquencyRows = useMemo(
    () =>
      (blocks?.delinquency?.series ?? []).map((point) => ({
        periodo: formatYearMonth(point.yearMonth) || point.month,
        pontualidade: point.onTimePctByAmount,
      })),
    [blocks?.delinquency?.series],
  );

  const topCostCenters = blocks?.costCenters?.top ?? [];
  const department = blocks?.indicators?.department;
  const departmentIndicators = department?.indicators ?? [];

  const period = data ? formatPeriodRange(data.period.startDate, data.period.endDate) : null;

  const openSubplugin = (subpluginId: string) => {
    navigateFinancial(buildFinancialHref({ subpluginId, branch }));
  };

  return (
    <div className="fin-page-stack">
      <FinWorkspaceHeader
        title={copy.home.title}
        subtitle={copy.home.subtitle}
        period={period}
        titleHint={helpTooltips.home}
        branch={branch}
        subpluginId="home"
        onRefresh={reload}
        refreshBusy={loading}
      />

      {loading && !data ? (
        <FinLoadingCard title={copy.home.loading} description={copy.home.loadingHint} />
      ) : null}

      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error || copy.home.loadError}
        </div>
      ) : null}

      {data && blocks ? (
        <div className="fin-board">
          <div className="fin-kpi-grid">
            <FinKpiCard
              title={blocks.rol.label ?? "ROL"}
              titleHint={helpTooltips.rol}
              value={kpiValue(blocks.rol, "currency")}
              goalLabel={kpiGoal(blocks.rol, "currency")}
              subtitle={copy.branch[branch]}
              icon={<Wallet size={22} strokeWidth={1.75} />}
              footer={<FinBlockState block={blocks.rol} />}
            />
            <FinKpiCard
              title={blocks.ebitda.label ?? "EBITDA"}
              titleHint={helpTooltips.ebitda}
              value={kpiValue(blocks.ebitda, "percent")}
              goalLabel={kpiGoal(blocks.ebitda, "percent")}
              subtitle={formatCurrency(blocks.ebitda.amount)}
              icon={<PiggyBank size={22} strokeWidth={1.75} />}
              footer={<FinBlockState block={blocks.ebitda} />}
            />
            <FinKpiCard
              title={blocks.fixedCost.label ?? "Custo fixo"}
              titleHint={helpTooltips.fixedCost}
              value={kpiValue(blocks.fixedCost, "percent")}
              goalLabel={kpiGoal(blocks.fixedCost, "percent")}
              subtitle={formatCurrency(blocks.fixedCost.amount)}
              icon={<HandCoins size={22} strokeWidth={1.75} />}
              footer={<FinBlockState block={blocks.fixedCost} />}
            />
            <FinKpiCard
              title={blocks.pmr.label ?? "PMR"}
              titleHint={helpTooltips.pmr}
              value={kpiValue(blocks.pmr, "days")}
              goalLabel={kpiGoal(blocks.pmr, "days")}
              subtitle={copy.branch[branch]}
              icon={<CalendarClock size={22} strokeWidth={1.75} />}
              footer={<FinBlockState block={blocks.pmr} />}
            />
            <FinKpiCard
              title={copy.home.iddLabel}
              titleHint={helpTooltips.idd}
              value={
                department?.available
                  ? copy.scoreOutOfTen(formatScore(department.idd))
                  : "—"
              }
              subtitle={department?.classification ?? copy.branch[branch]}
              icon={<Gauge size={22} strokeWidth={1.75} />}
              footer={
                <FinBlockState
                  block={
                    department && department.available === false
                      ? {
                          available: false,
                          error: department.reason ?? copy.indicators.unavailable,
                        }
                      : blocks.indicators
                  }
                />
              }
            />
          </div>

          <div className="fin-board-grid">
            <FinChartCard
              title={copy.home.delinquencyTitle}
              titleHint={helpTooltips.delinquency}
              hint={blocks.delinquency.scopeNotice}
              className="fin-board-card"
              headerActions={
                <button
                  type="button"
                  className="fin-link-btn"
                  onClick={() => openSubplugin("delinquency")}
                >
                  {copy.home.seeAll}
                </button>
              }
            >
              {blocks.delinquency.available === false ? (
                <FinBlockState block={blocks.delinquency} />
              ) : (
                <>
                  <ul className="fin-metric-row">
                    <li>
                      <span>{copy.home.onTimeLabel}</span>
                      <strong>
                        {formatPercent(blocks.delinquency.indicators?.onTimePctByAmount)}
                      </strong>
                    </li>
                    <li>
                      <span>{copy.home.lateAmountLabel}</span>
                      <strong>{formatCurrency(blocks.delinquency.totals?.lateAmount)}</strong>
                    </li>
                    <li>
                      <span>{copy.home.lateTitlesLabel}</span>
                      <strong>{formatInteger(blocks.delinquency.totals?.lateTitles)}</strong>
                    </li>
                  </ul>
                  {delinquencyRows.length === 0 ? (
                    <FinBlockState block={undefined} empty emptyMessage={copy.home.delinquencyEmpty} />
                  ) : (
                    <MultiTypeSeriesChart
                      data={delinquencyRows}
                      categoryKey="periodo"
                      series={[
                        {
                          dataKey: "pontualidade",
                          name: copy.home.delinquencySeries,
                          fill: "var(--fin-accent, #0b7285)",
                        },
                      ]}
                      chartType="line"
                      height={SERIES_HEIGHT}
                      showLegend={false}
                      formatY={formatChartPercent}
                      formatTooltipValue={formatChartPercent}
                      margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
                    />
                  )}
                </>
              )}
            </FinChartCard>

            <article className="fin-board-list" aria-label={copy.home.costCentersTitle}>
              <header className="fin-board-list__head">
                <h2 className="fin-board-list__title">{copy.home.costCentersTitle}</h2>
                <p className="fin-board-list__hint">
                  {copy.home.costCentersTotal}:{" "}
                  {formatCurrency(blocks.costCenters.totalAmount)}
                </p>
                <button
                  type="button"
                  className="fin-link-btn"
                  onClick={() => openSubplugin("cost-centers")}
                >
                  {copy.home.seeAll}
                </button>
              </header>
              {blocks.costCenters.available === false ? (
                <FinBlockState block={blocks.costCenters} />
              ) : topCostCenters.length === 0 ? (
                <FinBlockState block={undefined} empty emptyMessage={copy.home.costCentersEmpty} />
              ) : (
                <ul className="fin-bar-list">
                  {topCostCenters.map((item) => (
                    <li key={`${item.code}-${item.label}`}>
                      <div className="fin-bar-list__head">
                        <strong>{item.label || item.code}</strong>
                        <span>{formatCurrency(item.totalAmount)}</span>
                      </div>
                      <div className="fin-bar-list__track">
                        <span
                          className="fin-bar-list__fill"
                          style={{ width: `${Math.min(Math.max(item.percentage, 0), 100)}%` }}
                        />
                      </div>
                      <span className="fin-bar-list__meta">
                        {formatPercent(item.percentage)} · {formatInteger(item.entryCount)}{" "}
                        lançamentos
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>

          <article className="fin-board-list" aria-label={copy.home.indicatorsTitle}>
            <header className="fin-board-list__head">
              <h2 className="fin-board-list__title">{copy.home.indicatorsTitle}</h2>
              {department?.notice ? (
                <p className="fin-board-list__hint">{department.notice}</p>
              ) : null}
              <button
                type="button"
                className="fin-link-btn"
                onClick={() => openSubplugin("indicators")}
              >
                {copy.home.seeAll}
              </button>
            </header>
            {department?.available === false ? (
              <p className="fin-block-state fin-block-state--error" role="status">
                {department.reason ?? copy.indicators.unavailable}
              </p>
            ) : departmentIndicators.length === 0 ? (
              <FinBlockState block={undefined} empty emptyMessage={copy.home.indicatorsEmpty} />
            ) : (
              <ul className="fin-indicator-list">
                {departmentIndicators.map((indicator) => (
                  <li key={indicator.indicatorId}>
                    <span className="fin-indicator-list__name">{indicator.name}</span>
                    <span className="fin-indicator-list__goal">
                      {copy.home.goalLabel} {indicator.goalLabel ?? "—"}
                    </span>
                    <span className="fin-indicator-list__score">
                      {copy.scoreOutOfTen(formatScore(indicator.score))}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </div>
      ) : null}
    </div>
  );
}
