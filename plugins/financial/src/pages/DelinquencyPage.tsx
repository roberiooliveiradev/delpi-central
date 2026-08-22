import { MultiTypeSeriesChart } from "@delpi/plugin-ui/index";
import { AlertTriangle, BadgeCheck, CalendarClock, Download, FileText, Percent, TimerOff } from "lucide-react";
import { useMemo, useState } from "react";

import { FinBlockState } from "../components/FinBlockState";
import { FinChartCard, FinKpiCard, FinLoadingCard } from "../components/finUiKit";
import { FinWideDialog } from "../components/FinDialog";
import { FinPagination } from "../components/FinPagination";
import { FinPeriodShortcuts } from "../components/FinPeriodShortcuts";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import {
  DataTable,
  DataTableSection,
  FIN_TABLE_CLASSES,
  FIN_TABLE_LABELS,
  type DataTableColumn,
} from "../components/dataTableUi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useDelinquency, useDelinquencyTitles } from "../hooks/useDelinquency";
import { useDelinquencyCustomerOptions } from "../hooks/useDelinquencyCustomerOptions";
import { useSubplugins } from "../hooks/useSubplugins";
import type { DelinquencyCustomer, FinancialBranch } from "../types";
import { buildTopDelinquentChartRows } from "../utils/delinquentCustomersChart";
import { validateDelinquencyPeriodRange } from "../utils/delinquencyPeriod";
import { sortAgingByOrder, estimateAverageDaysLateFromAging } from "../utils/agingRanges";
import { decodeDelinquencyCustomerKey } from "../utils/delinquencyCustomers";
import { downloadExcel } from "../utils/exportExcel";
import { formatPeriodRange, formatIsoDate, formatYearMonth } from "../utils/formatDates";
import { formatCurrency, formatDays, formatInteger, formatPercent } from "../utils/formatNumbers";
import {
  buildFinancialHref,
  replaceFinancialQuery,
} from "../utils/routeParser";

const SERIES_HEIGHT = 220;
const TOP_DELINQUENT_CHART_HEIGHT = 300;

type DelinquencyPageProps = {
  branch: FinancialBranch;
  startDate: string | null;
  endDate: string | null;
  clientKey: string | null;
  customerCode: string | null;
  customerStore: string | null;
  status: string | null;
  delayRange: string | null;
  page: number;
};

export function DelinquencyPage({
  branch,
  startDate,
  endDate,
  clientKey,
  customerCode,
  customerStore,
  status,
  delayRange,
  page,
}: DelinquencyPageProps) {
  const { canExport } = useSubplugins();
  const selectedClient = useMemo(() => decodeDelinquencyCustomerKey(clientKey), [clientKey]);
  const [onlyWithDelays, setOnlyWithDelays] = useState(false);
  const [sortBy, setSortBy] = useState("late_amount");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [titlePage, setTitlePage] = useState(1);

  const customerOptions = useDelinquencyCustomerOptions({
    startDate,
    endDate,
  });

  const { data, loading, error, reload } = useDelinquency({
    startDate,
    endDate,
    clientCode: selectedClient?.customerCode ?? null,
    clientStore: selectedClient?.store ?? null,
    onlyWithDelays,
    page,
    sortBy,
    sortDir,
  });

  const titles = useDelinquencyTitles({
    customerCode,
    store: customerStore,
    status,
    delayRange,
    startDate,
    endDate,
    page: titlePage,
    enabled: Boolean(customerCode),
  });

  const summary = data?.summary;
  const aging = useMemo(() => sortAgingByOrder(data?.aging ?? []), [data?.aging]);
  const topDelinquentRows = useMemo(
    () => buildTopDelinquentChartRows(data?.topDelinquentCustomers ?? []),
    [data?.topDelinquentCustomers],
  );
  const topDelinquentByLabel = useMemo(
    () => new Map(topDelinquentRows.map((row) => [row.label, row])),
    [topDelinquentRows],
  );
  const periodError = useMemo(
    () => validateDelinquencyPeriodRange(startDate, endDate),
    [startDate, endDate],
  );
  const averageDaysLate = useMemo(() => {
    const fromSummary = summary?.indicators.averageDaysLate ?? 0;
    if (fromSummary > 0) return fromSummary;
    return estimateAverageDaysLateFromAging(aging);
  }, [aging, summary?.indicators.averageDaysLate]);
  const monthlyRows = useMemo(
    () =>
      (data?.monthly ?? []).map((point) => ({
        periodo: formatYearMonth(point.yearMonth) || point.month,
        pontualidade: point.onTimePctByAmount,
      })),
    [data?.monthly],
  );

  const openCustomer = (row: DelinquencyCustomer) => {
    setTitlePage(1);
    replaceFinancialQuery(
      buildFinancialHref({
        subpluginId: "delinquency",
        branch,
        startDate,
        endDate,
        clientKey,
        customerCode: row.customerCode,
        customerStore: row.store,
        status,
        delayRange,
        page,
      }),
    );
  };

  const openCustomerFromChart = (label: string) => {
    const row = topDelinquentByLabel.get(label);
    if (!row) return;
    openCustomer({
      customerCode: row.customerCode,
      store: row.store,
      customerName: row.label,
      shortName: row.label,
      totalTitles: row.totalTitles,
      onTimeTitles: row.totalTitles - row.lateTitles,
      lateTitles: row.lateTitles,
      totalAmount: 0,
      lateAmount: 0,
      onTimePctByCount: 0,
      onTimePctByAmount: 0,
    });
  };

  const closeModal = () => {
    replaceFinancialQuery(
      buildFinancialHref({
        subpluginId: "delinquency",
        branch,
        startDate,
        endDate,
        clientKey,
        page,
      }),
    );
  };

  const syncPage = (nextPage: number) => {
    replaceFinancialQuery(
      buildFinancialHref({
        subpluginId: "delinquency",
        branch,
        startDate,
        endDate,
        clientKey,
        customerCode,
        customerStore,
        status,
        delayRange,
        page: nextPage,
      }),
    );
  };

  const toggleSort = (column: string) => {
    if (sortBy === column) {
      setSortDir((current) => (current === "asc" ? "desc" : "asc"));
      return;
    }
    setSortBy(column);
    setSortDir("desc");
  };

  const customerColumns = useMemo<DataTableColumn<DelinquencyCustomer>[]>(
    () => [
      {
        key: "customer_name",
        header: copy.delinquency.columns.customer,
        className: "fin-table__col--wide",
        render: (row) => (
          <div className="fin-customer-cell">
            <strong>{row.customerName}</strong>
            <span>
              {row.customerCode}/{row.store}
            </span>
          </div>
        ),
      },
      {
        key: "late_titles",
        header: copy.delinquency.columns.lateTitles,
        align: "right",
        sortable: true,
        render: (row) => formatInteger(row.lateTitles),
      },
      {
        key: "late_amount",
        header: copy.delinquency.columns.lateAmount,
        align: "right",
        sortable: true,
        render: (row) => formatCurrency(row.lateAmount),
      },
      {
        key: "on_time_by_amount_percent",
        header: copy.delinquency.columns.punctuality,
        align: "right",
        sortable: true,
        render: (row) => formatPercent(row.onTimePctByAmount),
      },
    ],
    [],
  );

  const exportCustomers = () => {
    const rows = data?.customers.items ?? [];
    if (!rows.length) {
      window.alert(copy.delinquency.exportEmpty);
      return;
    }
    void downloadExcel(
      {
        title: copy.delinquency.exportSheetTitle,
        columns: [
          { key: "customer", label: copy.delinquency.columns.customer },
          { key: "titles", label: copy.delinquency.columns.titles },
          { key: "lateTitles", label: copy.delinquency.columns.lateTitles },
          { key: "totalAmount", label: copy.delinquency.columns.totalAmount },
          { key: "lateAmount", label: copy.delinquency.columns.lateAmount },
          { key: "punctuality", label: copy.delinquency.columns.punctuality },
        ],
        rows: rows.map((row) => ({
          customer: row.customerName,
          titles: row.totalTitles,
          lateTitles: row.lateTitles,
          totalAmount: row.totalAmount,
          lateAmount: row.lateAmount,
          punctuality: row.onTimePctByAmount,
        })),
      },
      copy.delinquency.exportFileName,
    );
  };

  return (
    <div className="fin-page-stack fin-page-stack--padded">
      <FinWorkspaceHeader
        title={copy.delinquency.title}
        subtitle={copy.delinquency.subtitle}
        period={summary ? formatPeriodRange(summary.period.startDate, summary.period.endDate) : null}
        titleHint={helpTooltips.delinquency}
        branch={branch}
        subpluginId="delinquency"
        showBranchSelector={false}
        startDate={startDate}
        endDate={endDate}
        onRefresh={reload}
        refreshBusy={loading}
        actions={
          canExport ? (
            <button type="button" className="fin-icon-btn" onClick={exportCustomers}>
              <Download size={16} strokeWidth={1.75} aria-hidden />
              <span>{copy.delinquency.exportLabel}</span>
            </button>
          ) : null
        }
      />

      <div className="fin-toolbar">
        <FinPeriodShortcuts
          startDate={startDate}
          endDate={endDate}
          disabled={loading}
          onApply={({ startDate: nextStart, endDate: nextEnd }) =>
            replaceFinancialQuery(
              buildFinancialHref({
                subpluginId: "delinquency",
                branch,
                startDate: nextStart,
                endDate: nextEnd,
                clientKey,
                page: 1,
              }),
            )
          }
        />
        <div className="fin-filters" aria-label={copy.period.label}>
          <label>
            {copy.period.from}
            <input
              type="date"
              value={startDate ?? ""}
              onChange={(event) =>
                replaceFinancialQuery(
                  buildFinancialHref({
                    subpluginId: "delinquency",
                    branch,
                    startDate: event.target.value || null,
                    endDate,
                    clientKey,
                    page: 1,
                  }),
                )
              }
            />
          </label>
          <label>
            {copy.period.to}
            <input
              type="date"
              value={endDate ?? ""}
              onChange={(event) =>
                replaceFinancialQuery(
                  buildFinancialHref({
                    subpluginId: "delinquency",
                    branch,
                    startDate,
                    endDate: event.target.value || null,
                    clientKey,
                    page: 1,
                  }),
                )
              }
            />
          </label>
          {periodError ? <p className="fin-field-error">{periodError}</p> : null}
          <label>
            {copy.delinquency.customerLabel}
            <select
              value={clientKey ?? ""}
              disabled={customerOptions.loading}
              onChange={(event) =>
                replaceFinancialQuery(
                  buildFinancialHref({
                    subpluginId: "delinquency",
                    branch,
                    startDate,
                    endDate,
                    clientKey: event.target.value || null,
                    customerCode,
                    customerStore,
                    status,
                    delayRange,
                    page: 1,
                  }),
                )
              }
            >
              <option value="">{copy.delinquency.allCustomersOption}</option>
              {(customerOptions.data ?? []).map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="fin-check">
            <input
              type="checkbox"
              checked={onlyWithDelays}
              onChange={(event) => setOnlyWithDelays(event.target.checked)}
            />
            <span className="fin-check__label">{copy.delinquency.onlyWithDelays}</span>
          </label>
        </div>
      </div>

      {loading && !data ? <FinLoadingCard title={copy.delinquency.loading} /> : null}
      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error}
        </div>
      ) : null}

      {summary ? (
        <>
          <p className="fin-scope-notice" role="note">
            {summary.scopeNotice || copy.delinquency.scopeNotice}
          </p>
          <div className="fin-kpi-grid" aria-label={copy.delinquency.kpiAria}>
            <FinKpiCard
              title={copy.delinquency.titlesLabel}
              value={formatInteger(summary.totals.titles)}
              icon={<FileText size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.delinquency.onTimeLabel}
              value={formatInteger(summary.totals.onTimeTitles)}
              icon={<BadgeCheck size={22} strokeWidth={1.75} />}
              iconTone="success"
            />
            <FinKpiCard
              title={copy.delinquency.lateLabel}
              value={formatInteger(summary.totals.lateTitles)}
              icon={<TimerOff size={22} strokeWidth={1.75} />}
              iconTone="danger"
            />
            <FinKpiCard
              title={copy.delinquency.punctualityLabel}
              value={formatPercent(summary.indicators.onTimePctByAmount)}
              subtitle={formatPercent(summary.indicators.onTimePctByCount)}
              icon={<Percent size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.delinquency.averageDaysLate}
              value={averageDaysLate != null ? formatDays(averageDaysLate) : "—"}
              icon={<CalendarClock size={22} strokeWidth={1.75} />}
            />
          </div>

          <div className="fin-board-grid">
            <FinChartCard title={copy.delinquency.seriesTitle} titleHint={helpTooltips.delinquency}>
              {monthlyRows.length === 0 ? (
                <FinBlockState empty emptyMessage={copy.delinquency.seriesEmpty} block={undefined} />
              ) : (
                <MultiTypeSeriesChart
                  data={monthlyRows}
                  categoryKey="periodo"
                  series={[
                    {
                      dataKey: "pontualidade",
                      name: copy.delinquency.seriesTitle,
                      fill: "var(--fin-accent, #0b7285)",
                    },
                  ]}
                  chartType="line"
                  height={SERIES_HEIGHT}
                  showLegend={false}
                  showValueLabels
                  formatY={(value) => formatPercent(value, 0)}
                  formatTooltipValue={(value) => formatPercent(value, 0)}
                />
              )}
            </FinChartCard>

            <FinChartCard title={copy.delinquency.agingTitle} titleHint={helpTooltips.delinquencyAging}>
              {topDelinquentRows.length === 0 ? (
                <FinBlockState empty emptyMessage={copy.delinquency.agingEmpty} block={undefined} />
              ) : (
                <div className="fin-top-delinquent-chart">
                  <MultiTypeSeriesChart
                    data={topDelinquentRows}
                    categoryKey="label"
                    categoryFillKey="fill"
                    series={[
                      {
                        dataKey: "delinquencyPct",
                        name: copy.delinquency.agingMetric,
                        fill: "var(--fin-critical, #e5484d)",
                      },
                    ]}
                    chartType="horizontal_bar"
                    height={TOP_DELINQUENT_CHART_HEIGHT}
                    showLegend={false}
                    showValueLabels
                    formatY={(value) => formatPercent(value, 0)}
                    formatTooltipValue={(value) => formatPercent(value, 1)}
                    onCategoryClick={openCustomerFromChart}
                  />
                </div>
              )}
            </FinChartCard>
          </div>

          <DataTableSection
            title={copy.delinquency.customersTitle}
            titleHint={helpTooltips.delinquencyCustomers}
            hint={copy.delinquency.customersHint}
            columns={customerColumns}
            rows={data?.customers.items ?? []}
            rowKey={(row) => `${row.customerCode}-${row.store}`}
            emptyMessage={copy.delinquency.customersEmpty}
            loading={loading}
            onRowClick={openCustomer}
            hideSearch
            hidePageSizeSelect
            serverPagination={
              data
                ? {
                    page: data.customers.pagination.page,
                    pageSize: data.customers.pagination.pageSize,
                    total: data.customers.pagination.totalItems,
                    onPageChange: syncPage,
                  }
                : undefined
            }
            serverSort={{
              sortKey: sortBy,
              sortDirection: sortDir,
              onSortChange: toggleSort,
            }}
          />
        </>
      ) : null}

      {customerCode ? (
        <FinWideDialog
          open
          title={copy.delinquency.modal.title}
          onClose={closeModal}
          closeAriaLabel={copy.delinquency.modal.close}
        >
          <div className="fin-filters">
            {(["all", "on_time", "late"] as const).map((value) => (
              <button
                key={value}
                type="button"
                className={`fin-link-btn${(status ?? "all") === value ? " fin-branch__btn--on" : ""}`}
                onClick={() => {
                  setTitlePage(1);
                  replaceFinancialQuery(
                    buildFinancialHref({
                      subpluginId: "delinquency",
                      branch,
                      startDate,
                      endDate,
                      clientKey,
                      customerCode,
                      customerStore,
                      status: value,
                      delayRange,
                      page,
                    }),
                  );
                }}
              >
                {value === "all"
                  ? copy.delinquency.modal.statusAll
                  : value === "on_time"
                    ? copy.delinquency.modal.statusOnTime
                    : copy.delinquency.modal.statusLate}
              </button>
            ))}
          </div>
          <DataTable
            classNames={FIN_TABLE_CLASSES}
            labels={FIN_TABLE_LABELS}
            columns={[
              {
                key: "number",
                header: copy.delinquency.modal.columns.title,
                render: (row) => `${row.prefix}-${row.number}/${row.installment}`,
              },
              {
                key: "issue",
                header: copy.delinquency.modal.columns.issue,
                render: (row) => formatIsoDate(row.issueDate),
              },
              {
                key: "due",
                header: copy.delinquency.modal.columns.due,
                render: (row) => formatIsoDate(row.dueDate),
              },
              {
                key: "payment",
                header: copy.delinquency.modal.columns.payment,
                render: (row) => formatIsoDate(row.paymentDate),
              },
              {
                key: "amount",
                header: copy.delinquency.modal.columns.amount,
                align: "right",
                render: (row) => formatCurrency(row.amount),
              },
              {
                key: "delay",
                header: copy.delinquency.modal.columns.delay,
                render: (row) =>
                  row.paidOnTime
                    ? copy.delinquency.modal.onTime
                    : copy.delinquency.modal.daysLate(row.daysLate),
              },
            ]}
            rows={titles.data?.items ?? []}
            rowKey={(row) => `${row.prefix}-${row.number}-${row.installment}`}
            emptyMessage={copy.delinquency.modal.empty}
            loading={titles.loading}
          />
          {titles.data ? (
            <FinPagination pagination={titles.data.pagination} onPageChange={setTitlePage} />
          ) : null}
        </FinWideDialog>
      ) : null}
    </div>
  );
}
