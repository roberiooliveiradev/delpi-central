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
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCostCenterEntries,
  fetchCostCenterRankingCenters,
  fetchCostCenterRankingSuppliers,
} from "../api/financialApi";
import {
  CostCenterRankingPanel,
  EXPANDED_RANKING_LIMIT,
} from "../components/CostCenterRankingPanel";
import { DataTable, FIN_TABLE_CLASSES, FIN_TABLE_LABELS } from "../components/dataTableUi";
import { FinKpiCard, FinLoadingCard } from "../components/finUiKit";
import { FinWideDialog } from "../components/FinDialog";
import { FinPagination } from "../components/FinPagination";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useCostCenterMonth } from "../hooks/useCostCenterMonth";
import { useSubplugins } from "../hooks/useSubplugins";
import type { CostCenterEntry, CostCenterSummary, FinancialBranch } from "../types";
import { formatIssueDate, formatPeriodRange, formatYearMonth } from "../utils/formatDates";
import { downloadExcel } from "../utils/exportExcel";
import { formatCurrency, formatInteger, formatPercent } from "../utils/formatNumbers";
import { resolveMonthComparison, type MonthComparison } from "../utils/monthComparison";
import { monthPeriodRange } from "../utils/monthPeriod";
import {
  buildFinancialHref,
  navigateFinancial,
  replaceFinancialQuery,
} from "../utils/routeParser";

/** Teto do Excel do mês: 200 linhas/página do BFF × 20 páginas. */
const EXPORT_PAGE_SIZE = 200;
const EXPORT_PAGE_LIMIT = 20;

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
  const [searchDraft, setSearchDraft] = useState(search ?? "");
  const [sortBy, setSortBy] = useState("data_emissao");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [selected, setSelected] = useState<CostCenterEntry | null>(null);
  const [exporting, setExporting] = useState(false);

  const syncQuery = useCallback(
    (changes: { search?: string | null; page?: number; excludeMp?: boolean }) => {
      replaceFinancialQuery(
        buildFinancialHref({
          subpluginId: "cost-centers",
          branch,
          month,
          costCenter,
          supplierCode,
          supplierStore,
          excludeMp: changes.excludeMp === undefined ? excludeMp : changes.excludeMp,
          search: changes.search === undefined ? search : changes.search,
          page: changes.page ?? 1,
        }),
      );
    },
    [branch, month, costCenter, supplierCode, supplierStore, excludeMp, search],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if ((searchDraft || null) === (search || null)) return;
      syncQuery({ search: searchDraft || null, page: 1 });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [searchDraft, search, syncQuery]);

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

  const monthRange = useMemo(() => monthPeriodRange(month), [month]);

  const rankingQuery = useMemo(
    () => ({
      branch,
      startDate: monthRange?.startDate ?? null,
      endDate: monthRange?.endDate ?? null,
      costCenter,
      supplierCode,
      supplierStore,
      excludeMpProducts: excludeMp,
      limit: EXPANDED_RANKING_LIMIT,
    }),
    [branch, monthRange, costCenter, supplierCode, supplierStore, excludeMp],
  );

  const loadExpandedCenters = useCallback(async () => {
    const response = await fetchCostCenterRankingCenters(rankingQuery);
    return response.items;
  }, [rankingQuery]);

  const loadExpandedSuppliers = useCallback(async () => {
    const response = await fetchCostCenterRankingSuppliers(rankingQuery);
    return response.items;
  }, [rankingQuery]);

  /** O Excel do mês não pode ficar preso à página visível da tabela. */
  const collectMonthEntries = useCallback(async (): Promise<CostCenterEntry[]> => {
    if (!monthRange) return [];
    const collected: CostCenterEntry[] = [];
    for (let current = 1; current <= EXPORT_PAGE_LIMIT; current += 1) {
      const payload = await fetchCostCenterEntries({
        branch,
        startDate: monthRange.startDate,
        endDate: monthRange.endDate,
        costCenter,
        supplierCode,
        supplierStore,
        excludeMpProducts: excludeMp,
        search,
        page: current,
        pageSize: EXPORT_PAGE_SIZE,
        sortBy,
        sortDir,
      });
      collected.push(...payload.items);
      if (!payload.pagination.hasNext) break;
    }
    return collected;
  }, [
    monthRange,
    branch,
    costCenter,
    supplierCode,
    supplierStore,
    excludeMp,
    search,
    sortBy,
    sortDir,
  ]);

  const exportEntries = async () => {
    if (exporting) return;
    setExporting(true);
    let rows: CostCenterEntry[] = [];
    try {
      rows = await collectMonthEntries();
    } catch {
      rows = data?.entries.items ?? [];
    } finally {
      setExporting(false);
    }
    if (!rows.length) {
      window.alert(copy.costCenters.exportEmpty);
      return;
    }
    void downloadExcel(
      {
        title: copy.costCenters.exportSheetTitle,
        columns: [
          { key: "issue", label: copy.costCenters.columns.issueDate },
          { key: "center", label: copy.costCenters.columns.costCenter },
          { key: "supplier", label: copy.costCenters.columns.supplier },
          { key: "document", label: copy.costCenters.columns.document },
          { key: "product", label: copy.costCenters.columns.product },
          { key: "notes", label: copy.costCenters.columns.notes },
          { key: "qty", label: copy.costCenters.columns.quantity },
          { key: "amount", label: copy.costCenters.columns.totalAmount },
        ],
        rows: rows.map((row) => ({
          issue: formatIssueDate(row.issueDate, row.issueDateLabel),
          center: row.costCenterLabel || row.costCenterCode,
          supplier: row.supplierName,
          document: row.document,
          product: row.productLabel || row.productCode,
          notes: row.notes,
          qty: row.quantity,
          amount: row.totalAmount,
        })),
      },
      copy.costCenters.monthDetail.exportFileName(month),
    );
  };

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
            <label
              className={`fin-month-toggle${excludeMp ? " fin-month-toggle--on" : ""}`}
              title={helpTooltips.excludeMpProducts}
            >
              <input
                type="checkbox"
                checked={excludeMp}
                onChange={(event) => syncQuery({ excludeMp: event.target.checked, page: 1 })}
              />
              <span>{copy.costCenters.excludeMpLabel}</span>
            </label>
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
              <button
                type="button"
                className="fin-icon-btn"
                onClick={() => void exportEntries()}
                disabled={exporting}
              >
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

          <div
            className="fin-kpi-grid fin-kpi-grid--month"
            aria-label={copy.costCenters.monthDetail.kpiAria}
          >
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

          <article className="fin-board-list" aria-label={copy.costCenters.monthDetail.entriesTitle}>
            <header className="fin-board-list__head">
              <h2 className="fin-board-list__title">
                {copy.costCenters.monthDetail.entriesTitle}
              </h2>
              <label className="fin-month-search">
                <span className="fin-sr-only">{copy.costCenters.searchPlaceholder}</span>
                <input
                  type="search"
                  value={searchDraft}
                  placeholder={copy.costCenters.searchPlaceholder}
                  onChange={(event) => setSearchDraft(event.target.value)}
                />
              </label>
              <p className="fin-board-list__hint">{copy.costCenters.entriesHint}</p>
            </header>
            {data?.sectionErrors.entries ? (
              <p className="fin-block-state fin-block-state--error" role="alert">
                {data.sectionErrors.entries}
              </p>
            ) : null}
            <DataTable
              classNames={FIN_TABLE_CLASSES}
              labels={FIN_TABLE_LABELS}
              columns={[
                {
                  key: "data_emissao",
                  header: copy.costCenters.columns.issueDate,
                  sortable: true,
                  render: (row) => formatIssueDate(row.issueDate, row.issueDateLabel),
                },
                {
                  key: "centro_custo_descricao",
                  header: copy.costCenters.columns.costCenter,
                  sortable: true,
                  render: (row) => row.costCenterLabel || row.costCenterCode,
                },
                {
                  key: "razao_social",
                  header: copy.costCenters.columns.supplier,
                  sortable: true,
                  render: (row) => row.supplierName,
                },
                {
                  key: "documento",
                  header: copy.costCenters.columns.document,
                  sortable: true,
                  render: (row) => row.document,
                },
                {
                  key: "produto_descricao",
                  header: copy.costCenters.columns.product,
                  render: (row) => row.productLabel || row.productCode,
                },
                {
                  key: "observacoes",
                  header: copy.costCenters.columns.notes,
                  className: "fin-table__col--wide fin-notes-cell",
                  render: (row) =>
                    row.notes ? (
                      <span className="fin-notes-cell__text" title={row.notes}>
                        {row.notes}
                      </span>
                    ) : (
                      "—"
                    ),
                },
                {
                  key: "valor_total",
                  header: copy.costCenters.columns.totalAmount,
                  align: "right",
                  sortable: true,
                  render: (row) => formatCurrency(row.totalAmount),
                },
              ]}
              rows={data?.entries.items ?? []}
              rowKey={(row) => row.id}
              emptyMessage={copy.costCenters.entriesEmpty}
              onRowClick={setSelected}
              sortKey={sortBy}
              sortDirection={sortDir}
              onSortChange={(column) => {
                if (sortBy === column) {
                  setSortDir((current) => (current === "asc" ? "desc" : "asc"));
                  return;
                }
                setSortBy(column);
                setSortDir("desc");
              }}
            />
            {data ? (
              <FinPagination
                pagination={data.entries.pagination}
                onPageChange={(next) => syncQuery({ page: next })}
              />
            ) : null}
          </article>
        </>
      ) : null}

      {selected ? (
        <FinWideDialog
          open
          title={copy.costCenters.detail.title}
          onClose={() => setSelected(null)}
          closeAriaLabel={copy.costCenters.detail.close}
        >
          <dl className="fin-detail-grid">
            <div>
              <dt>{copy.costCenters.detail.branch}</dt>
              <dd>{selected.branch}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.issueDate}</dt>
              <dd>{formatIssueDate(selected.issueDate, selected.issueDateLabel)}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.document}</dt>
              <dd>
                {selected.document} / {selected.series}
              </dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.purchaseOrder}</dt>
              <dd>{selected.purchaseOrder || "—"}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.supplier}</dt>
              <dd>{selected.supplierName}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.costCenter}</dt>
              <dd>{selected.costCenterLabel || selected.costCenterCode}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.product}</dt>
              <dd>{selected.productLabel || selected.productCode}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.quantity}</dt>
              <dd>{formatInteger(selected.quantity)}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.unitAmount}</dt>
              <dd>{formatCurrency(selected.unitAmount)}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.totalAmount}</dt>
              <dd>{formatCurrency(selected.totalAmount)}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.ledgerAccount}</dt>
              <dd>{selected.ledgerAccount || "—"}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.apportionment}</dt>
              <dd>{selected.apportionment || "—"}</dd>
            </div>
            <div>
              <dt>{copy.costCenters.detail.notes}</dt>
              <dd>{selected.notes || "—"}</dd>
            </div>
          </dl>
        </FinWideDialog>
      ) : null}
    </div>
  );
}
