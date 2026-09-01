import { MultiTypeSeriesChart } from "@delpi/plugin-ui/index";
import {
  ArrowUpToLine,
  CircleDollarSign,
  ClipboardList,
  Download,
  Layers,
  Ticket,
  Truck,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCostCenterRankingCenters,
  fetchCostCenterRankingSuppliers,
} from "../api/financialApi";
import {
  CostCenterRankingPanel,
  EXPANDED_RANKING_LIMIT,
} from "../components/CostCenterRankingPanel";

import { FinBlockState } from "../components/FinBlockState";
import { FinChartCard, FinKpiCard, FinLoadingCard } from "../components/finUiKit";
import { FinWideDialog } from "../components/FinDialog";
import { FinPagination } from "../components/FinPagination";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { DataTable, FIN_TABLE_CLASSES, FIN_TABLE_LABELS } from "../components/dataTableUi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useCostCenters } from "../hooks/useCostCenters";
import { useSubplugins } from "../hooks/useSubplugins";
import type { CostCenterEntry, FinancialBranch } from "../types";
import { downloadExcel } from "../utils/exportExcel";
import { formatIsoDate, formatIssueDate, formatPeriodRange, formatYearMonth } from "../utils/formatDates";
import { formatCompactCurrency, formatCurrency, formatInteger } from "../utils/formatNumbers";
import { buildFinancialHref, replaceFinancialQuery } from "../utils/routeParser";

const SERIES_HEIGHT = 280;

type CostCentersPageProps = {
  branch: FinancialBranch;
  startDate: string | null;
  endDate: string | null;
  search: string | null;
  costCenter: string | null;
  supplierCode: string | null;
  supplierStore: string | null;
  excludeMp: boolean;
  page: number;
};

export function CostCentersPage({
  branch,
  startDate,
  endDate,
  search,
  costCenter,
  supplierCode,
  supplierStore,
  excludeMp,
  page,
}: CostCentersPageProps) {
  const { canExport } = useSubplugins();
  const [searchDraft, setSearchDraft] = useState(search ?? "");
  const [sortBy, setSortBy] = useState("data_emissao");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [selected, setSelected] = useState<CostCenterEntry | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      replaceFinancialQuery(
        buildFinancialHref({
          subpluginId: "cost-centers",
          branch,
          startDate,
          endDate,
          search: searchDraft || null,
          costCenter,
          supplierCode,
          supplierStore,
          excludeMp,
          page: 1,
        }),
      );
    }, 350);
    return () => window.clearTimeout(timer);
  }, [searchDraft, branch, startDate, endDate, costCenter, supplierCode, supplierStore, excludeMp]);

  const { data, loading, error, reload } = useCostCenters({
    branch,
    startDate,
    endDate,
    costCenter,
    supplierCode,
    supplierStore,
    excludeMp,
    search,
    page,
    sortBy,
    sortDir,
  });

  const seriesRows = useMemo(
    () =>
      (data?.series ?? []).map((point) => ({
        periodo: formatYearMonth(point.yearMonth),
        valor: point.totalAmount,
      })),
    [data?.series],
  );

  const rankingQuery = useMemo(
    () => ({
      branch,
      startDate,
      endDate,
      costCenter,
      supplierCode,
      supplierStore,
      excludeMpProducts: excludeMp,
    }),
    [branch, startDate, endDate, costCenter, supplierCode, supplierStore, excludeMp],
  );

  const loadExpandedCenters = useCallback(async () => {
    const response = await fetchCostCenterRankingCenters({
      ...rankingQuery,
      limit: EXPANDED_RANKING_LIMIT,
    });
    return response.items;
  }, [rankingQuery]);

  const loadExpandedSuppliers = useCallback(async () => {
    const response = await fetchCostCenterRankingSuppliers({
      ...rankingQuery,
      limit: EXPANDED_RANKING_LIMIT,
    });
    return response.items;
  }, [rankingQuery]);

  const sync = (changes: Partial<CostCentersPageProps>) => {
    replaceFinancialQuery(
      buildFinancialHref({
        subpluginId: "cost-centers",
        branch: changes.branch ?? branch,
        startDate: changes.startDate === undefined ? startDate : changes.startDate,
        endDate: changes.endDate === undefined ? endDate : changes.endDate,
        search: changes.search === undefined ? search : changes.search,
        costCenter: changes.costCenter === undefined ? costCenter : changes.costCenter,
        supplierCode: changes.supplierCode === undefined ? supplierCode : changes.supplierCode,
        supplierStore: changes.supplierStore === undefined ? supplierStore : changes.supplierStore,
        excludeMp: changes.excludeMp === undefined ? excludeMp : changes.excludeMp,
        page: changes.page ?? 1,
      }),
    );
  };

  const exportEntries = () => {
    const rows = data?.entries.items ?? [];
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
      copy.costCenters.exportFileName,
    );
  };

  const summary = data?.summary;
  const catalog = data?.filters;

  return (
    <div className="fin-page-stack fin-page-stack--padded">
      <FinWorkspaceHeader
        title={copy.costCenters.title}
        subtitle={copy.costCenters.subtitle}
        period={summary ? formatPeriodRange(summary.period.startDate, summary.period.endDate) : null}
        titleHint={helpTooltips.costCenters}
        branch={branch}
        subpluginId="cost-centers"
        startDate={startDate}
        endDate={endDate}
        onRefresh={reload}
        refreshBusy={loading}
        actions={
          canExport ? (
            <button type="button" className="fin-icon-btn" onClick={exportEntries}>
              <Download size={16} strokeWidth={1.75} aria-hidden />
              <span>{copy.costCenters.exportLabel}</span>
            </button>
          ) : null
        }
      />

      <div className="fin-filters" aria-label={copy.costCenters.filtersAria}>
        <label>
          {copy.period.from}
          <input type="date" value={startDate ?? ""} onChange={(event) => sync({ startDate: event.target.value || null })} />
        </label>
        <label>
          {copy.period.to}
          <input type="date" value={endDate ?? ""} onChange={(event) => sync({ endDate: event.target.value || null })} />
        </label>
        <label>
          {copy.costCenters.costCenterLabel}
          <select
            value={costCenter ?? ""}
            onChange={(event) => sync({ costCenter: event.target.value || null })}
          >
            <option value="">{copy.costCenters.allOption}</option>
            {(catalog?.costCenters ?? []).map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          {copy.costCenters.supplierLabel}
          <select
            value={supplierCode && supplierStore ? `${supplierCode}|${supplierStore}` : ""}
            onChange={(event) => {
              const [code, store] = event.target.value.split("|");
              sync({ supplierCode: code || null, supplierStore: store || null });
            }}
          >
            <option value="">{copy.costCenters.allOption}</option>
            {(catalog?.suppliers ?? []).map((option) => (
              <option key={`${option.code}-${option.store}`} value={`${option.code}|${option.store ?? ""}`}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          {copy.costCenters.searchPlaceholder}
          <input
            type="search"
            value={searchDraft}
            placeholder={copy.costCenters.searchPlaceholder}
            onChange={(event) => setSearchDraft(event.target.value)}
          />
        </label>
        <label className="fin-check" title={helpTooltips.excludeMpProducts}>
          <input
            type="checkbox"
            checked={excludeMp}
            onChange={(event) => sync({ excludeMp: event.target.checked, page: 1 })}
          />
          <span className="fin-check__label">{copy.costCenters.excludeMpLabel}</span>
        </label>
        <button
          type="button"
          className="fin-link-btn"
          onClick={() =>
            sync({
              startDate: null,
              endDate: null,
              costCenter: null,
              supplierCode: null,
              supplierStore: null,
              excludeMp: false,
              search: null,
              page: 1,
            })
          }
        >
          {copy.costCenters.clearFilters}
        </button>
      </div>

      {loading && !data ? <FinLoadingCard title={copy.costCenters.loading} /> : null}
      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {summary ? (
        <>
          <div className="fin-kpi-grid" aria-label={copy.costCenters.kpiAria}>
            <FinKpiCard
              title={copy.costCenters.totalLabel}
              value={formatCurrency(summary.totalAmount)}
              icon={<CircleDollarSign size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.costCenters.entriesLabel}
              value={formatInteger(summary.entryCount)}
              icon={<ClipboardList size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.costCenters.centersLabel}
              value={formatInteger(summary.costCenterCount)}
              icon={<Layers size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.costCenters.suppliersLabel}
              value={formatInteger(summary.supplierCount)}
              icon={<Truck size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.costCenters.averageTicketLabel}
              value={formatCurrency(summary.averageTicket)}
              icon={<Ticket size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.costCenters.largestEntryLabel}
              value={formatCurrency(summary.largestEntry)}
              icon={<ArrowUpToLine size={22} strokeWidth={1.75} />}
            />
          </div>

          <div className="fin-chart-section fin-chart-section--full">
            <FinChartCard
              title={copy.costCenters.seriesTitle}
              titleHint={helpTooltips.costCenters}
              hint={copy.costCenters.seriesHint}
            >
              {data?.sectionErrors.series ? (
                <p className="fin-block-state fin-block-state--error" role="alert">
                  {data.sectionErrors.series}
                </p>
              ) : seriesRows.length === 0 ? (
                <FinBlockState empty emptyMessage={copy.costCenters.seriesEmpty} block={undefined} />
              ) : (
                <MultiTypeSeriesChart
                  data={seriesRows}
                  categoryKey="periodo"
                  series={[
                    {
                      dataKey: "valor",
                      name: copy.costCenters.seriesTitle,
                      fill: "var(--fin-accent, #0b7285)",
                    },
                  ]}
                  chartType="column"
                  height={SERIES_HEIGHT}
                  showLegend={false}
                  showValueLabels
                  formatY={formatCompactCurrency}
                  formatTooltipValue={formatCurrency}
                />
              )}
            </FinChartCard>
          </div>

          <div className="fin-board-grid fin-board-grid--rankings">
            <CostCenterRankingPanel
              title={copy.costCenters.rankingCentersTitle}
              items={data?.centers ?? []}
              variant="centers"
              loading={loading}
              loadError={data?.sectionErrors.centers}
              expandAriaLabel={copy.costCenters.rankingExpandCentersAria}
              modalTitle={copy.costCenters.rankingCentersTitle}
              modalSubtitle={copy.costCenters.rankingExpandedCentersSubtitle}
              onLoadExpanded={loadExpandedCenters}
            />
            <CostCenterRankingPanel
              title={copy.costCenters.rankingSuppliersTitle}
              items={data?.suppliers ?? []}
              variant="suppliers"
              loading={loading}
              loadError={data?.sectionErrors.suppliers}
              expandAriaLabel={copy.costCenters.rankingExpandSuppliersAria}
              modalTitle={copy.costCenters.rankingSuppliersTitle}
              modalSubtitle={copy.costCenters.rankingExpandedSuppliersSubtitle}
              onLoadExpanded={loadExpandedSuppliers}
            />
          </div>

          <article className="fin-board-list" aria-label={copy.costCenters.entriesTitle}>
            <header className="fin-board-list__head">
              <h2 className="fin-board-list__title">{copy.costCenters.entriesTitle}</h2>
              <p className="fin-board-list__hint">{copy.costCenters.entriesHint}</p>
            </header>
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
            {data ? <FinPagination pagination={data.entries.pagination} onPageChange={(next) => sync({ page: next })} /> : null}
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
