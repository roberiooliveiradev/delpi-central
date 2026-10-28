import { runTabularExport, type DataTableColumn } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getBillingByCustomerMonth } from "../../api/analyticsApi";
import {
  CommercialActionButton,
  CommercialDataListToolbar,
  CommercialDataTable,
  CommercialEmptyState,
  CommercialExcelExportButton,
  CommercialLoadingCard,
  CommercialMetricCard,
  CommercialPageHero,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialSegmentToggle,
  CommercialSelectField,
  CommercialStateBanner,
  cmFiltersKit,
} from "../../app/commercialUi";
import {
  BILLING_NATURE_CONTENT,
  DEFAULT_PORTFOLIO_BILLING_NATURE,
  appendBillingNatureContext,
  type PortfolioBillingAmountNature,
} from "../../content/billingNature";
import {
  BILLING_BY_CUSTOMER_MONTH_CONTENT,
  monthLabelPt,
  monthOptionLabel,
  resolveYearMonthRange,
} from "../../content/billingByCustomerMonthContent";
import { CM_HELP } from "../../content/helpTooltips";
import type { BillingByCustomerMonthData } from "../../types/analytics";
import { formatCurrency } from "../../utils/format";
import { AnalyticsDeepPagePath } from "./components/AnalyticsDeepPagePath";
import { AnalyticsFilters } from "./components/AnalyticsFilters";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";

type BillingByCustomerMonthPageProps = {
  basePath: string;
};

type Row = {
  id: string;
  customerCode: string;
  customerStore: string;
  customerName: string;
  total: number;
  months: Record<string, number>;
};

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 8 }, (_, index) => CURRENT_YEAR - index);
const MONTH_OPTIONS = Array.from({ length: 12 }, (_, index) => index + 1);

function formatMonthHeader(monthKey: string): string {
  return monthLabelPt(monthKey);
}

export function BillingByCustomerMonthPage({ basePath }: BillingByCustomerMonthPageProps) {
  const filters = useAnalyticsFilters();
  const { FiltersRow } = cmFiltersKit;
  const [year, setYear] = useState(CURRENT_YEAR);
  const [month, setMonth] = useState<number | "all">(new Date().getMonth() + 1);
  const [billingNature, setBillingNature] = useState<PortfolioBillingAmountNature>(
    DEFAULT_PORTFOLIO_BILLING_NATURE,
  );
  const [data, setData] = useState<BillingByCustomerMonthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [exporting, setExporting] = useState(false);

  const period = useMemo(() => resolveYearMonthRange(year, month), [year, month]);

  useEffect(() => {
    if (filters.dateStart !== period.start || filters.dateEnd !== period.end) {
      filters.setDateStart(period.start);
      filters.setDateEnd(period.end);
    }
    // Sync only when year/month chips change — avoid loop with filter URL writer.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period.start, period.end]);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setError(null);

    void getBillingByCustomerMonth(
      {
        ...filters.apiParams,
        start_date: period.start,
        end_date: period.end,
        nature: billingNature,
        limit: 5000,
      },
      controller.signal,
    )
      .then((payload) => {
        if (cancelled) return;
        setData(payload);
      })
      .catch((err: unknown) => {
        if (cancelled || controller.signal.aborted) return;
        setData(null);
        setError(
          err instanceof Error
            ? err.message
            : BILLING_BY_CUSTOMER_MONTH_CONTENT.errorFallback,
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [filters.apiParams, period.start, period.end, billingNature, reloadKey]);

  const months = data?.months ?? [];
  const rows = useMemo((): Row[] => {
    const items = data?.items ?? [];
    return items.map((item, index) => ({
      id: `${item.customer_code}|${item.customer_store}|${index}`,
      customerCode: item.customer_code,
      customerStore: item.customer_store || "01",
      customerName: item.customer_name || item.customer_code,
      total: Number(item.total || 0),
      months: item.monthly_values || {},
    }));
  }, [data]);

  const columns = useMemo((): DataTableColumn<Row>[] => {
    const base: DataTableColumn<Row>[] = [
      {
        key: "customerCode",
        header: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.code,
        sortable: true,
        sortValue: (row) => row.customerCode,
        render: (row) => row.customerCode,
      },
      {
        key: "customerStore",
        header: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.store,
        sortable: true,
        sortValue: (row) => row.customerStore,
        render: (row) => row.customerStore,
      },
      {
        key: "customerName",
        header: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.name,
        sortable: true,
        sortValue: (row) => row.customerName,
        render: (row) => row.customerName,
      },
    ];
    for (const monthKey of months) {
      base.push({
        key: `m-${monthKey}`,
        header: formatMonthHeader(monthKey),
        sortable: true,
        align: "right",
        sortValue: (row) => row.months[monthKey] ?? 0,
        render: (row) => formatCurrency(row.months[monthKey] ?? 0),
      });
    }
    base.push({
      key: "total",
      header: appendBillingNatureContext(
        BILLING_BY_CUSTOMER_MONTH_CONTENT.table.total,
        billingNature,
      ),
      sortable: true,
      align: "right",
      sortValue: (row) => row.total,
      render: (row) => formatCurrency(row.total),
    });
    return base;
  }, [months, billingNature]);

  const handleExport = useCallback(() => {
    if (!rows.length) return;
    setExporting(true);
    try {
      const columns = [
        { key: "customerCode", label: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.code },
        { key: "customerStore", label: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.store },
        { key: "customerName", label: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.name },
        ...months.map((monthKey) => ({
          key: `m_${monthKey}`,
          label: formatMonthHeader(monthKey),
        })),
        { key: "total", label: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.total },
      ];
      const exportRows: Record<string, unknown>[] = rows.map((row) => {
        const record: Record<string, unknown> = {
          customerCode: row.customerCode,
          customerStore: row.customerStore,
          customerName: row.customerName,
          total: row.total,
        };
        for (const monthKey of months) {
          record[`m_${monthKey}`] = row.months[monthKey] ?? 0;
        }
        return record;
      });
      const monthlyTotals = data?.summary?.monthly_totals ?? {};
      const totalsRow: Record<string, unknown> = {
        customerCode: "",
        customerStore: "",
        customerName: BILLING_BY_CUSTOMER_MONTH_CONTENT.table.grandTotal,
        total: data?.summary?.grand_total ?? 0,
      };
      for (const monthKey of months) {
        totalsRow[`m_${monthKey}`] = monthlyTotals[monthKey] ?? 0;
      }
      exportRows.push(totalsRow);
      runTabularExport({
        kind: "table",
        format: "xlsx",
        payload: {
          title: `${BILLING_BY_CUSTOMER_MONTH_CONTENT.export.filenamePrefix}-${year}${
            month === "all" ? "" : `-${String(month).padStart(2, "0")}`
          }-${billingNature}`,
          columns,
          rows: exportRows,
        },
      });
    } finally {
      setExporting(false);
    }
  }, [rows, months, data, year, month, billingNature]);

  const grandTotal = data?.summary?.grand_total ?? 0;
  const customersCount = data?.summary?.customers_count ?? rows.length;

  return (
    <div className="cm-page-stack">
      <CommercialPageHero
        title={BILLING_BY_CUSTOMER_MONTH_CONTENT.title}
        description={BILLING_BY_CUSTOMER_MONTH_CONTENT.description}
        actions={
          <CommercialActionButton
            type="button"
            variant="ghost"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            <RefreshCw size={16} aria-hidden="true" />{" "}
            {BILLING_BY_CUSTOMER_MONTH_CONTENT.reload}
          </CommercialActionButton>
        }
      />
      <AnalyticsDeepPagePath
        basePath={basePath}
        current={BILLING_BY_CUSTOMER_MONTH_CONTENT.title}
        backTo="home"
        viewId="analytics_billing_by_customer"
      />

      <CommercialSectionCard title="Filtros">
        <FiltersRow variant="extended">
          <CommercialSelectField
            label={BILLING_BY_CUSTOMER_MONTH_CONTENT.filters.year}
            value={String(year)}
            onChange={(value) => setYear(Number(value) || CURRENT_YEAR)}
            options={YEAR_OPTIONS.map((option) => ({
              value: String(option),
              label: String(option),
            }))}
            hint={CM_HELP.billingByCustomerMonth.filterYear}
          />
          <CommercialSelectField
            label={BILLING_BY_CUSTOMER_MONTH_CONTENT.filters.month}
            value={month === "all" ? "all" : String(month)}
            onChange={(value) => {
              if (value === "all") {
                setMonth("all");
                return;
              }
              const parsed = Number(value);
              setMonth(Number.isFinite(parsed) ? parsed : "all");
            }}
            options={[
              {
                value: "all",
                label: BILLING_BY_CUSTOMER_MONTH_CONTENT.filters.monthAll,
              },
              ...MONTH_OPTIONS.map((option) => ({
                value: String(option),
                label: monthOptionLabel(option),
              })),
            ]}
            hint={CM_HELP.billingByCustomerMonth.filterMonth}
          />
          <div>
            <CommercialSectionHintLabel
              label={BILLING_BY_CUSTOMER_MONTH_CONTENT.filters.nature}
              hint={CM_HELP.billingByCustomerMonth.billingNature}
            />
            <CommercialSegmentToggle
              ariaLabel={BILLING_BY_CUSTOMER_MONTH_CONTENT.filters.nature}
              idPrefix="billing-by-customer-month-nature"
              value={billingNature}
              widthMode="content"
              onChange={(value) => {
                if (value === "gross" || value === "net") {
                  setBillingNature(value);
                }
              }}
              options={[
                {
                  value: "gross",
                  label: BILLING_NATURE_CONTENT.gross.shortLabel,
                },
                {
                  value: "net",
                  label: BILLING_NATURE_CONTENT.net.shortLabel,
                },
              ]}
            />
          </div>
        </FiltersRow>
        <AnalyticsFilters
          dateStart={filters.dateStart}
          dateEnd={filters.dateEnd}
          competence={filters.competence}
          periodPreset={filters.periodPreset}
          branches={filters.branches}
          customerSegment={filters.customerSegment}
          sellerIds={filters.sellerIds}
          canFilterPortfolios={filters.canFilterPortfolios}
          canUseTeamScope={filters.canUseTeamScope}
          filterablePortfolios={filters.filterablePortfolios}
          onDateStart={filters.setDateStart}
          onDateEnd={filters.setDateEnd}
          onCompetence={filters.setCompetence}
          onPeriodPreset={filters.setPeriodPreset}
          onBranches={filters.setBranches}
          onCustomerSegment={filters.setCustomerSegment}
          customerCodes={filters.customerCodes}
          onCustomerCodes={filters.setCustomerCodes}
          customerCenters={filters.customerCenters}
          onCustomerCenters={filters.setCustomerCenters}
          onSellerIds={filters.setSellerIds}
        />
      </CommercialSectionCard>

      {error ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {data?.summary?.truncated ? (
        <CommercialStateBanner>
          {BILLING_BY_CUSTOMER_MONTH_CONTENT.table.truncated}
        </CommercialStateBanner>
      ) : null}

      <div className="cm-kpi-grid">
        <CommercialMetricCard
          label={appendBillingNatureContext(
            BILLING_BY_CUSTOMER_MONTH_CONTENT.table.grandTotal,
            billingNature,
          )}
          value={formatCurrency(grandTotal)}
          hint={CM_HELP.billingByCustomerMonth.grandTotal}
        />
        <CommercialMetricCard
          label="Clientes"
          value={String(customersCount)}
          hint={CM_HELP.billingByCustomerMonth.customersCount}
        />
      </div>

      <CommercialSectionCard
        title={appendBillingNatureContext(
          BILLING_BY_CUSTOMER_MONTH_CONTENT.title,
          billingNature,
        )}
      >
        {loading ? (
          <CommercialLoadingCard
            title={BILLING_BY_CUSTOMER_MONTH_CONTENT.loading}
            variant="panel"
          />
        ) : rows.length === 0 ? (
          <CommercialEmptyState title={BILLING_BY_CUSTOMER_MONTH_CONTENT.table.empty} />
        ) : (
          <>
            <CommercialDataListToolbar
              hint={
                <span className="delpi-ui-section-hint-label">
                  {rows.length.toLocaleString("pt-BR")} cliente(s)
                </span>
              }
              actions={
                <CommercialExcelExportButton
                  density="toolbar"
                  label={BILLING_BY_CUSTOMER_MONTH_CONTENT.export.label}
                  exporting={exporting}
                  disabled={rows.length === 0}
                  onExport={handleExport}
                />
              }
            />
            <CommercialDataTable
              columns={columns}
              rows={rows}
              rowKey={(row) => row.id}
              layout="section"
            />
          </>
        )}
      </CommercialSectionCard>
    </div>
  );
}
