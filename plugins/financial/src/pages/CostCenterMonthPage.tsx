import {
  ArrowLeft,
  ArrowUpToLine,
  CircleDollarSign,
  ClipboardList,
  Download,
  Layers,
  Ticket,
  TrendingDown,
  TrendingUp,
  Truck,
} from "lucide-react";
import { useCallback, useMemo, useState } from "react";

import {
  fetchCostCenterRankingCenters,
  fetchCostCenterRankingSuppliers,
} from "../api/financialApi";
import {
  CostCenterRankingPanel,
  EXPANDED_RANKING_LIMIT,
} from "../components/CostCenterRankingPanel";
import { FinKpiCard, FinLoadingCard } from "../components/finUiKit";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useCostCenterMonth } from "../hooks/useCostCenterMonth";
import { useSubplugins } from "../hooks/useSubplugins";
import type { CostCenterSummary, FinancialBranch } from "../types";
import { formatPeriodRange, formatYearMonth } from "../utils/formatDates";
import { formatCurrency, formatInteger, formatPercent } from "../utils/formatNumbers";
import { resolveMonthComparison, type MonthComparison } from "../utils/monthComparison";
import { buildFinancialHref, navigateFinancial } from "../utils/routeParser";

type CostCenterMonthPageProps = {
  branch: FinancialBranch;
  month: string;
  costCenter: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  excludeMp: boolean;
  search: string | null;
  page: number;
};

type MonthKpi = {
  key: string;
  title: string;
  value: string;
  icon: React.ReactNode;
  comparison: MonthComparison | null;
  formatDelta: (value: number) => string;
};

function comparisonSubtitle(
  comparison: MonthComparison | null,
  previousMonth: string | null,
  formatDelta: (value: number) => string,
): string | undefined {
  if (!comparison || !previousMonth) return undefined;
  const signal = comparison.deltaAmount > 0 ? "+" : comparison.deltaAmount < 0 ? "−" : "";
  const amount = formatDelta(Math.abs(comparison.deltaAmount));
  const pct = comparison.deltaPct == null ? "" : ` (${signal}${formatPercent(Math.abs(comparison.deltaPct))})`;
  return `${signal}${amount}${pct} ${copy.costCenters.monthDetail.heroCompare(formatYearMonth(previousMonth))}`;
}

export function CostCenterMonthPage({
  branch,
  month,
  costCenter,
  supplierCode,
  supplierStore,
  excludeMp,
  search,
  page,
}: CostCenterMonthPageProps) {
  const { canExport } = useSubplugins();
  const [sortBy] = useState("data_emissao");
  const [sortDir] = useState<"asc" | "desc">("desc");

  const { data, loading, error, reload } = useCostCenterMonth({
    branch,
    month,
    costCenter,
    supplierCode,
    supplierStore,
    excludeMp,
    search,
    page,
    sortBy,
    sortDir,
  });

  const summary: CostCenterSummary | undefined = data?.summary;
  const previous = data?.previousSummary ?? null;
  const previousMonth = data?.previousMonth ?? null;

  const totalComparison = useMemo(
    () => resolveMonthComparison(summary?.totalAmount, previous?.totalAmount),
    [summary?.totalAmount, previous?.totalAmount],
  );

  const kpis: MonthKpi[] = useMemo(() => {
    if (!summary) return [];
    return [
      {
        key: "total",
        title: copy.costCenters.monthDetail.totalLabel,
        value: formatCurrency(summary.totalAmount),
        icon: <CircleDollarSign size={22} strokeWidth={1.75} />,
        comparison: resolveMonthComparison(summary.totalAmount, previous?.totalAmount),
        formatDelta: formatCurrency,
      },
      {
        key: "entries",
        title: copy.costCenters.entriesLabel,
        value: formatInteger(summary.entryCount),
        icon: <ClipboardList size={22} strokeWidth={1.75} />,
        comparison: resolveMonthComparison(summary.entryCount, previous?.entryCount),
        formatDelta: formatInteger,
      },
      {
        key: "centers",
        title: copy.costCenters.centersLabel,
        value: formatInteger(summary.costCenterCount),
        icon: <Layers size={22} strokeWidth={1.75} />,
        comparison: resolveMonthComparison(summary.costCenterCount, previous?.costCenterCount),
        formatDelta: formatInteger,
      },
      {
        key: "suppliers",
        title: copy.costCenters.suppliersLabel,
        value: formatInteger(summary.supplierCount),
        icon: <Truck size={22} strokeWidth={1.75} />,
        comparison: resolveMonthComparison(summary.supplierCount, previous?.supplierCount),
        formatDelta: formatInteger,
      },
      {
        key: "averageTicket",
        title: copy.costCenters.averageTicketLabel,
        value: formatCurrency(summary.averageTicket),
        icon: <Ticket size={22} strokeWidth={1.75} />,
        comparison: resolveMonthComparison(summary.averageTicket, previous?.averageTicket),
        formatDelta: formatCurrency,
      },
      {
        key: "largestEntry",
        title: copy.costCenters.largestEntryLabel,
        value: formatCurrency(summary.largestEntry),
        icon: <ArrowUpToLine size={22} strokeWidth={1.75} />,
        comparison: resolveMonthComparison(summary.largestEntry, previous?.largestEntry),
        formatDelta: formatCurrency,
      },
    ];
  }, [summary, previous]);

  const rankingQuery = useMemo(
    () => ({
      branch,
      startDate: data?.period.startDate ?? null,
      endDate: data?.period.endDate ?? null,
      costCenter,
      supplierCode,
      supplierStore,
      excludeMpProducts: excludeMp,
      limit: EXPANDED_RANKING_LIMIT,
    }),
    [branch, data?.period.startDate, data?.period.endDate, costCenter, supplierCode, supplierStore, excludeMp],
  );

  const loadExpandedCenters = useCallback(async () => {
    const response = await fetchCostCenterRankingCenters(rankingQuery);
    return response.items;
  }, [rankingQuery]);

  const loadExpandedSuppliers = useCallback(async () => {
    const response = await fetchCostCenterRankingSuppliers(rankingQuery);
    return response.items;
  }, [rankingQuery]);

  const goBack = () => {
    navigateFinancial(
      buildFinancialHref({
        subpluginId: "cost-centers",
        branch,
        costCenter,
        supplierCode,
        supplierStore,
        excludeMp,
      }),
    );
  };

  const scopeChips = [
    costCenter ? copy.costCenters.monthDetail.filtersLabel.costCenter(costCenter) : null,
    supplierCode ? copy.costCenters.monthDetail.filtersLabel.supplier(supplierCode) : null,
    excludeMp ? copy.costCenters.monthDetail.filtersLabel.excludeMp : null,
  ].filter((chip): chip is string => Boolean(chip));

  return (
    <div className="fin-page-stack fin-page-stack--padded">
      <FinWorkspaceHeader
        title={copy.costCenters.monthDetail.title(formatYearMonth(month))}
        subtitle={copy.costCenters.monthDetail.subtitle}
        period={data ? formatPeriodRange(data.period.startDate, data.period.endDate) : null}
        titleHint={helpTooltips.costCenters}
        branch={branch}
        subpluginId="cost-centers"
        month={month}
        onRefresh={reload}
        refreshBusy={loading}
        stats={
          scopeChips.length ? (
            <>
              {scopeChips.map((chip) => (
                <span key={chip} className="fin-month-chip">
                  {chip}
                </span>
              ))}
            </>
          ) : null
        }
        actions={
          <>
            <button
              type="button"
              className="fin-icon-btn fin-month-back"
              onClick={goBack}
              aria-label={copy.costCenters.monthDetail.backAria}
            >
              <ArrowLeft size={16} strokeWidth={1.75} aria-hidden />
              <span>{copy.costCenters.monthDetail.back}</span>
            </button>
            {canExport ? (
              <button type="button" className="fin-icon-btn" disabled>
                <Download size={16} strokeWidth={1.75} aria-hidden />
                <span>{copy.costCenters.exportLabel}</span>
              </button>
            ) : null}
          </>
        }
      />

      {loading && !data ? <FinLoadingCard title={copy.costCenters.monthDetail.loading} /> : null}
      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {summary ? (
        <>
          {data?.sectionErrors.summary ? (
            <p className="fin-block-state fin-block-state--error" role="alert">
              {data.sectionErrors.summary}
            </p>
          ) : null}

          <section className="fin-month-hero" aria-label={copy.costCenters.monthDetail.heroLabel}>
            <p className="fin-month-hero__label">{copy.costCenters.monthDetail.heroLabel}</p>
            <p className="fin-month-hero__value">{formatCurrency(summary.totalAmount)}</p>
            {totalComparison && previousMonth ? (
              <p
                className={`fin-month-hero__delta${
                  totalComparison.deltaAmount > 0
                    ? " fin-month-hero__delta--up"
                    : totalComparison.deltaAmount < 0
                      ? " fin-month-hero__delta--down"
                      : ""
                }`}
              >
                {totalComparison.deltaAmount >= 0 ? (
                  <TrendingUp size={18} strokeWidth={1.9} aria-hidden />
                ) : (
                  <TrendingDown size={18} strokeWidth={1.9} aria-hidden />
                )}
                <span>
                  {comparisonSubtitle(totalComparison, previousMonth, formatCurrency)}
                </span>
              </p>
            ) : (
              <p className="fin-month-hero__delta fin-month-hero__delta--muted">
                {copy.costCenters.monthDetail.heroNoBase}
              </p>
            )}
          </section>

          <div className="fin-kpi-grid" aria-label={copy.costCenters.monthDetail.kpiAria}>
            {kpis.map((kpi) => (
              <FinKpiCard
                key={kpi.key}
                title={kpi.title}
                value={kpi.value}
                icon={kpi.icon}
                comparisonTone={kpi.comparison?.tone ?? null}
                subtitle={comparisonSubtitle(kpi.comparison, previousMonth, kpi.formatDelta)}
              />
            ))}
          </div>

          <div className="fin-board-grid fin-board-grid--rankings">
            <CostCenterRankingPanel
              title={copy.costCenters.rankingCentersTitle}
              items={data?.centers ?? []}
              variant="centers"
              loading={loading}
              loadError={data?.sectionErrors.centers}
              previewHint={copy.costCenters.monthDetail.rankingPreviewHint}
              expandAriaLabel={copy.costCenters.rankingExpandCentersAria}
              modalTitle={copy.costCenters.rankingCentersTitle}
              modalSubtitle={copy.costCenters.monthDetail.rankingExpandedCentersSubtitle}
              onLoadExpanded={loadExpandedCenters}
            />
            <CostCenterRankingPanel
              title={copy.costCenters.rankingSuppliersTitle}
              items={data?.suppliers ?? []}
              variant="suppliers"
              loading={loading}
              loadError={data?.sectionErrors.suppliers}
              previewHint={copy.costCenters.monthDetail.rankingPreviewHint}
              expandAriaLabel={copy.costCenters.rankingExpandSuppliersAria}
              modalTitle={copy.costCenters.rankingSuppliersTitle}
              modalSubtitle={copy.costCenters.monthDetail.rankingExpandedSuppliersSubtitle}
              onLoadExpanded={loadExpandedSuppliers}
            />
          </div>
        </>
      ) : null}
    </div>
  );
}
