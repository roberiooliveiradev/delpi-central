import {
  MultiTypeSeriesChart,
  SERIES_CHART_CATEGORY_PALETTE,
  useChartGranularitySelection,
  type ChartGranularity,
} from "@delpi/plugin-ui/index";
import {
  BadgeMinus,
  Banknote,
  Download,
  FileSpreadsheet,
  Landmark,
  Receipt,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useMemo, useState } from "react";

import { FinBlockState } from "../components/FinBlockState";
import {
  FinChartCard,
  FinChartGranularityToggle,
  FinKpiCard,
  FinLoadingCard,
} from "../components/finUiKit";
import { FinWorkspaceHeader } from "../components/FinWorkspaceHeader";
import { DataTable } from "../components/dataTableUi";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { fetchBillingInvoices } from "../api/financialApi";
import { useBilling } from "../hooks/useBilling";
import { useSubplugins } from "../hooks/useSubplugins";
import type { BillingLine, FinancialBranch } from "../types";
import {
  billingSeriesKeys,
  clampPercent,
  compositionStatementRows,
  customerPieRows,
  seriesChartRows,
} from "../utils/billingPresentation";
import { downloadExcel } from "../utils/exportExcel";
import { formatIsoDate, formatPeriodRange } from "../utils/formatDates";
import { formatCompactCurrency, formatCurrency, formatPercent } from "../utils/formatNumbers";
import { resolveKpiComparisonTone } from "../utils/kpiComparisonTone";
import { buildFinancialHref, replaceFinancialQuery } from "../utils/routeParser";

const SERIES_HEIGHT = 260;
const CUSTOMER_PIE_HEIGHT = 360;

const GRANULARITY_OPTIONS: { value: ChartGranularity; label: string }[] = [
  { value: "day", label: copy.billing.granularity.day },
  { value: "week", label: copy.billing.granularity.week },
  { value: "month", label: copy.billing.granularity.month },
  { value: "year", label: copy.billing.granularity.year },
];

type BillingPageProps = {
  branch: FinancialBranch;
  startDate: string | null;
  endDate: string | null;
  granularity: string | null;
};

export function BillingPage({
  branch,
  startDate,
  endDate,
  granularity: granularityFromUrl,
}: BillingPageProps) {
  const { canExport } = useSubplugins();
  const [extracting, setExtracting] = useState(false);
  const [extractNotice, setExtractNotice] = useState<string | null>(null);
  const auto = useChartGranularitySelection(startDate ?? undefined, endDate ?? undefined);
  const granularity = (granularityFromUrl as ChartGranularity | null) ?? auto.granularity;
  const { data, loading, error, reload } = useBilling(branch, startDate, endDate, granularity);
  const summary = data?.summary;
  const period = data
    ? formatPeriodRange(data.period.startDate, data.period.endDate)
    : null;

  const applyPeriod = (next: { startDate: string; endDate: string } | null) => {
    replaceFinancialQuery(
      buildFinancialHref({
        subpluginId: "billing",
        branch,
        startDate: next?.startDate ?? null,
        endDate: next?.endDate ?? null,
        granularity,
      }),
    );
  };

  const setGranularity = (next: ChartGranularity) => {
    replaceFinancialQuery(
      buildFinancialHref({
        subpluginId: "billing",
        branch,
        startDate,
        endDate,
        granularity: next,
      }),
    );
  };

  const seriesKeys = billingSeriesKeys(branch);
  const seriesRows = useMemo(
    () => seriesChartRows(data?.series.items ?? []),
    [data?.series.items],
  );
  const statementRows = useMemo(
    () => compositionStatementRows(summary?.composition ?? []),
    [summary?.composition],
  );
  const taxMix = useMemo(
    () => (summary?.taxMix ?? []).filter((line) => line.value > 0),
    [summary?.taxMix],
  );
  const customers = data?.customers.items ?? [];
  const customerPie = useMemo(
    () =>
      customerPieRows(
        customers,
        data?.customers.others,
        copy.billing.othersLabel,
        SERIES_CHART_CATEGORY_PALETTE,
      ),
    [customers, data?.customers.others],
  );
  const unitItems = data?.branches.items ?? [];
  const rolTone = resolveKpiComparisonTone(
    summary
      ? { available: true, error: null, value: summary.rol, target: summary.target ?? undefined }
      : undefined,
    "higher_is_better",
  );
  const attainment = clampPercent(summary?.targetPct);
  const gap = summary?.gap;
  const gapLabel =
    gap == null
      ? copy.billing.noGoal
      : `${formatCurrency(Math.abs(gap))} ${gap >= 0 ? copy.billing.gapAbove : copy.billing.gapBelow}`;

  const exportComposition = () => {
    const rows = (summary?.detail ?? []).map((line) => ({
      component: line.label,
      value: line.value,
    }));
    if (!rows.length) return;
    void downloadExcel(
      {
        title: copy.billing.exportSheetTitle,
        columns: [
          { key: "component", label: copy.billing.columns.component },
          { key: "value", label: copy.billing.columns.value },
        ],
        rows,
      },
      copy.billing.exportFileName,
    );
  };

  const exportInvoices = async () => {
    setExtractNotice(null);
    setExtracting(true);
    try {
      const extract = await fetchBillingInvoices({
        branch,
        startDate: startDate ?? data?.period.startDate,
        endDate: endDate ?? data?.period.endDate,
      });
      if (!extract.items.length) {
        setExtractNotice(copy.billing.exportExtractEmpty);
        return;
      }
      await downloadExcel(
        {
          title: copy.billing.exportExtractSheetTitle,
          columns: [
            { key: "kind", label: copy.billing.extractColumns.kind },
            { key: "branch", label: copy.billing.extractColumns.branch },
            { key: "issueDate", label: copy.billing.extractColumns.issueDate },
            { key: "invoiceNumber", label: copy.billing.extractColumns.invoiceNumber },
            { key: "series", label: copy.billing.extractColumns.series },
            { key: "customerCode", label: copy.billing.extractColumns.customerCode },
            { key: "customerStore", label: copy.billing.extractColumns.customerStore },
            { key: "customerName", label: copy.billing.extractColumns.customerName },
            { key: "gross", label: copy.billing.extractColumns.gross },
            { key: "discounts", label: copy.billing.extractColumns.discounts },
            { key: "returns", label: copy.billing.extractColumns.returns },
            { key: "taxes", label: copy.billing.extractColumns.taxes },
            { key: "rol", label: copy.billing.extractColumns.rol },
          ],
          rows: extract.items.map((item) => ({
            kind: item.kindLabel,
            branch: item.branch,
            issueDate: formatIsoDate(item.issueDate),
            invoiceNumber: item.invoiceNumber,
            series: item.series,
            customerCode: item.customerCode,
            customerStore: item.customerStore,
            customerName: item.customerName,
            gross: item.gross,
            discounts: item.discounts,
            returns: item.returns,
            taxes: item.taxes,
            rol: item.rol,
          })),
        },
        copy.billing.exportExtractFileName,
      );
      if (extract.truncated) {
        setExtractNotice(copy.billing.exportExtractTruncated);
      }
    } catch (error) {
      setExtractNotice(
        error instanceof Error && error.message.trim()
          ? error.message
          : copy.billing.exportExtractError,
      );
    } finally {
      setExtracting(false);
    }
  };

  return (
    <div className="fin-page-stack">
      <FinWorkspaceHeader
        title={copy.billing.title}
        subtitle={copy.billing.subtitle}
        period={period}
        periodDefaultStart={data?.period.startDate ?? null}
        periodDefaultEnd={data?.period.endDate ?? null}
        periodEditable
        titleHint={helpTooltips.billing}
        branch={branch}
        subpluginId="billing"
        startDate={startDate}
        endDate={endDate}
        granularity={granularity}
        onPeriodChange={applyPeriod}
        onRefresh={reload}
        refreshBusy={loading}
        actions={
          canExport ? (
            <>
              <button
                type="button"
                className="fin-icon-btn"
                onClick={() => void exportInvoices()}
                disabled={extracting}
                title={helpTooltips.billingExtract}
              >
                <FileSpreadsheet size={16} strokeWidth={1.75} aria-hidden />
                <span>
                  {extracting ? copy.billing.exportExtractBusy : copy.billing.exportExtractLabel}
                </span>
              </button>
              <button
                type="button"
                className="fin-icon-btn"
                onClick={exportComposition}
                disabled={!summary?.detail.length || extracting}
                title={copy.billing.exportLabel}
              >
                <Download size={16} strokeWidth={1.75} aria-hidden />
                <span>{copy.billing.exportLabel}</span>
              </button>
            </>
          ) : null
        }
      />

      {loading && !data ? (
        <FinLoadingCard title={copy.billing.loading} description={copy.billing.loadingHint} />
      ) : null}

      {extractNotice ? (
        <div className="fin-state fin-state--error" role="status">
          {extractNotice}
        </div>
      ) : null}

      {error ? (
        <div className="fin-state fin-state--error" role="alert">
          {error || copy.billing.loadError}
        </div>
      ) : null}

      {summary ? (
        <div className="fin-board">
          <article className="fin-billing-hero" aria-label={copy.billing.heroEyebrow}>
            <div className="fin-billing-hero__main">
              <p className="fin-billing-hero__eyebrow">{copy.billing.heroEyebrow}</p>
              <p className="fin-billing-hero__value">{formatCurrency(summary.rol)}</p>
              <p className="fin-billing-hero__meta">
                {copy.branch[branch]} · {period}
              </p>
            </div>
            <div className="fin-billing-hero__goal">
              <p className="fin-billing-hero__goal-label">
                {copy.home.goalLabel}
                {summary.target != null ? ` ${formatCurrency(summary.target)}` : ` —`}
              </p>
              {summary.target != null ? (
                <>
                  <div
                    className="fin-billing-hero__meter"
                    role="meter"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={Math.round(attainment)}
                    aria-label={copy.billing.vsGoal}
                  >
                    <span
                      className={`fin-billing-hero__meter-fill${
                        rolTone === "negative" ? " fin-billing-hero__meter-fill--behind" : ""
                      }`}
                      style={{ width: `${attainment}%` }}
                    />
                  </div>
                  <p className="fin-billing-hero__goal-meta">
                    {formatPercent(summary.targetPct)} {copy.billing.vsGoal}
                    {summary.goalLabel ? ` · ${summary.goalLabel}` : ""}
                  </p>
                  <p
                    className={`fin-billing-hero__status${
                      rolTone === "negative" ? " fin-billing-hero__status--behind" : ""
                    }`}
                  >
                    {rolTone === "negative" ? copy.billing.offTrack : copy.billing.onTrack}
                    {" · "}
                    {gapLabel}
                  </p>
                </>
              ) : (
                <p className="fin-billing-hero__goal-meta">{copy.billing.noGoal}</p>
              )}
            </div>
          </article>

          <div className="fin-kpi-grid fin-kpi-grid--billing" aria-label={copy.billing.kpiAria}>
            <FinKpiCard
              title={copy.billing.grossLabel}
              titleHint={helpTooltips.billingWaterfall}
              value={formatCurrency(summary.grossRevenue)}
              subtitle={copy.branch[branch]}
              icon={<Banknote size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.billing.taxesLabel}
              titleHint={helpTooltips.billingWaterfall}
              value={formatCurrency(summary.taxes)}
              subtitle={formatPercent(summary.grossRevenue ? (summary.taxes / summary.grossRevenue) * 100 : null)}
              icon={<Landmark size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.billing.returnsLabel}
              titleHint={helpTooltips.billingWaterfall}
              value={formatCurrency(summary.returns)}
              subtitle={copy.branch[branch]}
              icon={<Receipt size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.billing.discountsLabel}
              titleHint={helpTooltips.billingWaterfall}
              value={formatCurrency(summary.discounts)}
              subtitle={copy.branch[branch]}
              icon={<BadgeMinus size={22} strokeWidth={1.75} />}
            />
            <FinKpiCard
              title={copy.billing.gapLabel}
              titleHint={helpTooltips.rol}
              value={formatCurrency(gap)}
              comparisonTone={rolTone}
              subtitle={gap == null ? copy.billing.noGoal : gapLabel}
              icon={
                gap != null && gap < 0 ? (
                  <TrendingDown size={22} strokeWidth={1.75} />
                ) : (
                  <TrendingUp size={22} strokeWidth={1.75} />
                )
              }
            />
          </div>

          <div className="fin-board-grid">
            <FinChartCard
              title={copy.billing.seriesTitle}
              titleHint={helpTooltips.billingSeries}
              hint={`${copy.branch[branch]} · ${period ?? ""}`}
              className="fin-board-card"
              headerActions={
                <FinChartGranularityToggle
                  value={granularity}
                  onChange={setGranularity}
                  options={GRANULARITY_OPTIONS}
                />
              }
            >
              {data?.series.available === false ? (
                <FinBlockState block={data.series} />
              ) : seriesRows.length === 0 ? (
                <FinBlockState block={undefined} empty emptyMessage={copy.billing.seriesEmpty} />
              ) : (
                <MultiTypeSeriesChart
                  data={seriesRows}
                  categoryKey="periodo"
                  series={seriesKeys.map((key) => ({
                    dataKey: key,
                    name: key === "rol01" ? copy.billing.series01 : copy.billing.series02,
                    fill:
                      key === "rol01"
                        ? "var(--fin-accent, #089bdb)"
                        : "var(--fin-title, #003866)",
                  }))}
                  chartType="area"
                  height={SERIES_HEIGHT}
                  showLegend={seriesKeys.length > 1}
                  formatY={formatCompactCurrency}
                  formatTooltipValue={formatCurrency}
                  margin={{ top: 8, right: 8, left: 8, bottom: 0 }}
                />
              )}
            </FinChartCard>

            <article className="fin-board-list fin-statement-card" aria-label={copy.billing.waterfallTitle}>
              <header className="fin-board-list__head">
                <h2 className="fin-board-list__title">{copy.billing.waterfallTitle}</h2>
                <p className="fin-board-list__hint">{copy.billing.waterfallHint}</p>
              </header>
              <div className="fin-statement" role="table" aria-label={copy.billing.waterfallTitle}>
                <div className="fin-statement__row fin-statement__row--head" role="row">
                  <span className="fin-statement__op" role="columnheader" />
                  <span role="columnheader">{copy.billing.columns.component}</span>
                  <span className="fin-statement__num" role="columnheader">
                    {copy.billing.statementMovement}
                  </span>
                  <span className="fin-statement__num" role="columnheader">
                    {copy.billing.statementBalance}
                  </span>
                </div>
                {statementRows.map((line) => (
                  <div
                    key={line.key}
                    className={`fin-statement__row fin-statement__row--${line.role}`}
                    role="row"
                  >
                    <span
                      className={`fin-statement__op fin-statement__op--${line.role}`}
                      role="cell"
                      aria-hidden={line.role === "add"}
                    >
                      {line.role === "subtract"
                        ? copy.billing.statementMinus
                        : line.role === "result"
                          ? copy.billing.statementEquals
                          : copy.billing.statementPlus}
                    </span>
                    <span className="fin-statement__label" role="cell">
                      {line.label}
                    </span>
                    <span className="fin-statement__num" role="cell">
                      {line.role === "result" ? "" : formatCurrency(Math.abs(line.movement))}
                    </span>
                    <span className="fin-statement__num fin-statement__balance" role="cell">
                      {formatCurrency(line.balance)}
                    </span>
                  </div>
                ))}
              </div>
              {taxMix.length ? (
                <div className="fin-tax-mix">
                  <p className="fin-tax-mix__title">{copy.billing.taxMixTitle}</p>
                  <ul className="fin-tax-mix__list">
                    {taxMix.map((line) => (
                      <li key={line.key}>
                        <span>{line.label}</span>
                        <strong>{formatCurrency(line.value)}</strong>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </article>
          </div>

          <div className="fin-board-grid fin-board-grid--rankings">
            <article className="fin-board-list" aria-label={copy.billing.unitsTitle}>
              <header className="fin-board-list__head">
                <h2 className="fin-board-list__title">{copy.billing.unitsTitle}</h2>
                <p className="fin-board-list__hint">{helpTooltips.billingUnits}</p>
              </header>
              {data?.branches.available === false ? (
                <FinBlockState block={data.branches} />
              ) : unitItems.length === 0 ? (
                <FinBlockState block={undefined} empty emptyMessage={copy.billing.unitsEmpty} />
              ) : (
                <ul className="fin-bar-list">
                  {unitItems.map((item) => {
                    const total = data?.branches.totalRol || 1;
                    const share = (item.rol / total) * 100;
                    const unitLabel =
                      item.branch === "01"
                        ? copy.branch["01"]
                        : item.branch === "02"
                          ? copy.branch["02"]
                          : item.branch;
                    return (
                      <li key={item.branch}>
                        <div className="fin-bar-list__head">
                          <strong>{unitLabel}</strong>
                          <span>{formatCurrency(item.rol)}</span>
                        </div>
                        <div className="fin-bar-list__track">
                          <span
                            className="fin-bar-list__fill"
                            style={{ width: `${Math.min(Math.max(share, 0), 100)}%` }}
                          />
                        </div>
                        <span className="fin-bar-list__meta">
                          {formatPercent(share)} · {copy.billing.grossLabel}{" "}
                          {formatCurrency(item.grossRevenue)}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </article>

            <FinChartCard
              title={copy.billing.customersTitle}
              titleHint={helpTooltips.billingCustomers}
              hint={copy.billing.customersHint}
              className="fin-board-card"
            >
              {data?.customers.available === false ? (
                <FinBlockState block={data.customers} />
              ) : customerPie.length === 0 ? (
                <FinBlockState block={undefined} empty emptyMessage={copy.billing.customersEmpty} />
              ) : (
                <div className="fin-customer-pie">
                  <MultiTypeSeriesChart
                    data={customerPie}
                    categoryKey="label"
                    categoryFillKey="fill"
                    series={[
                      {
                        dataKey: "rol",
                        name: copy.billing.rolShort,
                        fill: "var(--fin-accent, #089bdb)",
                      },
                    ]}
                    chartType="pie"
                    height={CUSTOMER_PIE_HEIGHT}
                    showLegend
                    formatY={formatCompactCurrency}
                    formatTooltipValue={formatCurrency}
                  />
                </div>
              )}
            </FinChartCard>
          </div>

          <article className="fin-board-list" aria-label={copy.billing.detailTitle}>
            <header className="fin-board-list__head">
              <h2 className="fin-board-list__title">{copy.billing.detailTitle}</h2>
            </header>
            <DataTable
              columns={[
                {
                  key: "label",
                  header: copy.billing.columns.component,
                  render: (row: BillingLine) => row.label,
                },
                {
                  key: "value",
                  header: copy.billing.columns.value,
                  align: "right",
                  render: (row: BillingLine) => formatCurrency(row.value),
                },
              ]}
              rows={summary.detail}
              rowKey={(row: BillingLine) => row.key}
              emptyMessage={copy.billing.detailEmpty}
            />
          </article>
        </div>
      ) : null}
    </div>
  );
}
