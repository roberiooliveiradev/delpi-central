import { useEffect, useMemo, useState } from "react";
import { DataTable, runTabularExport } from "@delpi/plugin-ui/index";

import { getCommercialRolByProduct } from "../../../api/analyticsApi";
import {
  CommercialClearFiltersButton,
  CommercialDataListToolbar,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialSegmentToggle,
  CommercialStateBanner,
  CommercialTableColumnVisibilityMenu,
  CommercialTableFontSizeControls,
  CommercialTabularExportButtons,
  cmDataTableClassNames,
  cmDataTableLabels,
  type DataTableColumn,
} from "../../../app/commercialUi";
import { CUSTOMER_BILLING_CONTENT } from "../../../content/customerBillingContent";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  appendBillingNatureContext,
  type PortfolioBillingAmountNature,
} from "../../../content/billingNature";
import type { PortfolioBillingMetric } from "../../../content/billingMetric";
import type { CommercialRolByProductItem } from "../../../types/analytics";
import { formatCurrency, formatQuantity } from "../../../utils/format";
import {
  PORTFOLIO_BY_PRODUCT_COLUMN_HELP,
  withColumnHelp,
} from "../../../utils/customersColumnHelp";
import { billingSeriesPresetLabel } from "../utils/billingSeriesPeriod";
import { usePortfolioBillingTablePreferences } from "../hooks/usePortfolioBillingTablePreferences";
import type { PortfolioBillingWorkspaceFilters } from "../hooks/usePortfolioBillingWorkspaceFilters";
import {
  PORTFOLIO_BY_PRODUCT_COLUMN_CATALOG,
  PORTFOLIO_BY_PRODUCT_COLUMNS_STORAGE_KEY,
  PORTFOLIO_BY_PRODUCT_FONT_STORAGE_KEY,
} from "../utils/portfolioBillingTableColumns";
import {
  formatSharePct,
  mapRolByProductRows,
  type PortfolioBillingByProductRow,
} from "../utils/portfolioBillingTableMappers";

type PortfolioBillingByProductTableProps = {
  filters: PortfolioBillingWorkspaceFilters;
  sellerId?: string | null;
  active?: boolean;
  billingNature?: PortfolioBillingAmountNature;
  billingMetric?: PortfolioBillingMetric;
  onCatalogOptions?: (options: {
    products: Array<{ value: string; label: string }>;
    groups: Array<{ value: string; label: string }>;
  }) => void;
};

function sentenceTableClassNames() {
  return {
    ...cmDataTableClassNames,
    wrapSection: [cmDataTableClassNames.wrapSection, cmDataTableClassNames.sentenceHeadersWrap]
      .filter(Boolean)
      .join(" "),
  };
}

export function PortfolioBillingByProductTable({
  filters,
  sellerId = null,
  active = true,
  billingNature = "gross",
  billingMetric = "value",
  onCatalogOptions,
}: PortfolioBillingByProductTableProps) {
  const [groupBy, setGroupBy] = useState<"product" | "product_group">("product");
  const [items, setItems] = useState<CommercialRolByProductItem[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const marketMode =
    filters.marketParam === "domestic" || filters.marketParam === "export"
      ? filters.marketParam
      : "all";
  const {
    visibility,
    orderedColumns,
    visibleColumnCount,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    resetColumns,
    filterColumns,
    tableStyle,
    fontSize,
    increaseFont,
    decreaseFont,
    resetFont,
    canIncreaseFont,
    canDecreaseFont,
    isDefaultFont,
  } = usePortfolioBillingTablePreferences({
    columnsStorageKey: PORTFOLIO_BY_PRODUCT_COLUMNS_STORAGE_KEY,
    fontSizeStorageKey: PORTFOLIO_BY_PRODUCT_FONT_STORAGE_KEY,
    columns: PORTFOLIO_BY_PRODUCT_COLUMN_CATALOG,
    emptyFallbackKeys: ["label", "share"],
  });
  const queryEnabled =
    active && !filters.periodError && Boolean(filters.startDate && filters.endDate);

  useEffect(() => {
    if (!queryEnabled || !onCatalogOptions) return;
    const controller = new AbortController();
    void getCommercialRolByProduct(
      {
        start_date: filters.startDate,
        end_date: filters.endDate,
        seller_id: sellerId || undefined,
        customer_codes: filters.customerCodesCsv || undefined,
        group_by: "product",
        limit: 500,
        nature: billingNature,
      },
      controller.signal,
    )
      .then((data) => {
        if (controller.signal.aborted) return;
        const nextItems = Array.isArray(data.items) ? data.items : [];
        const products = new Map<string, string>();
        const groups = new Map<string, string>();
        for (const item of nextItems) {
          if (item.product_code) {
            products.set(
              item.product_code,
              `${item.product_code} · ${item.product_name || item.product_code}`,
            );
          }
          if (item.product_group) {
            groups.set(
              item.product_group,
              `${item.product_group}${item.product_name ? ` · ${item.product_name}` : ""}`,
            );
          }
        }
        onCatalogOptions({
          products: [...products.entries()].map(([value, label]) => ({ value, label })),
          groups: [...groups.entries()].map(([value, label]) => ({ value, label })),
        });
      })
      .catch(() => {
        /* catálogo opcional — falha silenciosa */
      });
    return () => controller.abort();
  }, [
    queryEnabled,
    filters.startDate,
    filters.endDate,
    filters.customerCodesCsv,
    sellerId,
    billingNature,
    onCatalogOptions,
  ]);

  useEffect(() => {
    if (!queryEnabled) return;
    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setError(null);

    void getCommercialRolByProduct(
      {
        start_date: filters.startDate,
        end_date: filters.endDate,
        seller_id: sellerId || undefined,
        customer_codes: filters.customerCodesCsv || undefined,
        product_codes: filters.productCodesCsv || undefined,
        product_groups: filters.productGroupsCsv || undefined,
        market: filters.marketParam,
        group_by: groupBy,
        limit: 500,
        nature: billingNature,
      },
      controller.signal,
    )
      .then((data) => {
        if (cancelled) return;
        setItems(Array.isArray(data.items) ? data.items : []);
        setCountries(
          Array.isArray(data.export_destination_countries)
            ? data.export_destination_countries
            : [],
        );
      })
      .catch((err: unknown) => {
        if (cancelled || controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar mix de produto.");
        setItems([]);
        setCountries([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [
    queryEnabled,
    filters.startDate,
    filters.endDate,
    filters.customerCodesCsv,
    filters.productCodesCsv,
    filters.productGroupsCsv,
    filters.marketParam,
    groupBy,
    sellerId,
    billingNature,
  ]);

  const rows = useMemo(
    () =>
      mapRolByProductRows(items, {
        nature: billingNature,
        market: marketMode,
        groupBy,
        metric: billingMetric,
      }),
    [items, billingNature, billingMetric, marketMode, groupBy],
  );

  const formatAmount = (value: number) =>
    billingMetric === "quantity" ? formatQuantity(value) : formatCurrency(value);

  const columns = useMemo((): DataTableColumn<PortfolioBillingByProductRow>[] => {
    const base: DataTableColumn<PortfolioBillingByProductRow>[] = [
      {
        key: "label",
        header: CUSTOMER_BILLING_CONTENT.colProduct,
        render: (row) => row.label,
        sortValue: (row) => row.label,
        sortable: true,
      },
    ];
    if (marketMode === "all") {
      base.push(
        {
          key: "domestic",
          header: CUSTOMER_BILLING_CONTENT.colDomestic,
          render: (row) => formatAmount(row.domestic),
          sortValue: (row) => row.domestic,
          sortable: true,
          align: "right",
        },
        {
          key: "export",
          header: CUSTOMER_BILLING_CONTENT.colExport,
          render: (row) => formatAmount(row.export),
          sortValue: (row) => row.export,
          sortable: true,
          align: "right",
        },
        {
          key: "total",
          header: CUSTOMER_BILLING_CONTENT.colTotal,
          render: (row) => formatAmount(row.total),
          sortValue: (row) => row.total,
          sortable: true,
          align: "right",
        },
      );
    } else {
      base.push({
        key: "total",
        header: CUSTOMER_BILLING_CONTENT.colValue,
        render: (row) => formatAmount(row.total),
        sortValue: (row) => row.total,
        sortable: true,
        align: "right",
      });
    }
    if (billingMetric === "quantity") {
      base.push({
        key: "unit",
        header: "UM",
        render: (row) => (row.mixedUnits ? "mistas" : row.unit?.trim() || "—"),
        sortValue: (row) => row.unit || "",
        sortable: true,
      });
    } else {
      base.push({
        key: "share",
        header: CUSTOMER_BILLING_CONTENT.colShare,
        render: (row) => formatSharePct(row.sharePct),
        sortValue: (row) => row.sharePct ?? -1,
        sortable: true,
        align: "right",
      });
    }
    return base;
  }, [billingMetric, marketMode]);

  const visibleColumns = useMemo(() => {
    return filterColumns(withColumnHelp(columns, PORTFOLIO_BY_PRODUCT_COLUMN_HELP)).filter(
      (column) => {
        if (marketMode !== "all" && (column.key === "domestic" || column.key === "export")) {
          return false;
        }
        return true;
      },
    );
  }, [columns, filterColumns, marketMode]);

  const periodLabel = billingSeriesPresetLabel(filters.preset);
  const mixTitleBase =
    groupBy === "product_group"
      ? CUSTOMER_BILLING_CONTENT.byProductGroupTitle
      : CUSTOMER_BILLING_CONTENT.byProductTitle;
  const title =
    billingMetric === "quantity"
      ? `${mixTitleBase} (qtd) — ${periodLabel}`
      : appendBillingNatureContext(`${mixTitleBase} — ${periodLabel}`, billingNature);
  const hasFilters =
    filters.selectedProductCodes.length > 0 ||
    filters.selectedProductGroups.length > 0 ||
    filters.selectedMarkets.length > 0 ||
    filters.selectedCustomerKeys.length > 0;
  const showCountries =
    marketMode !== "domestic" && countries.length > 0 && rows.length > 0;

  const exportColumns =
    marketMode === "all"
      ? [
          { key: "label", label: CUSTOMER_BILLING_CONTENT.colProduct },
          { key: "domestic", label: CUSTOMER_BILLING_CONTENT.colDomestic },
          { key: "export", label: CUSTOMER_BILLING_CONTENT.colExport },
          { key: "total", label: CUSTOMER_BILLING_CONTENT.colTotal },
          { key: "sharePct", label: CUSTOMER_BILLING_CONTENT.colShare },
        ]
      : [
          { key: "label", label: CUSTOMER_BILLING_CONTENT.colProduct },
          { key: "total", label: CUSTOMER_BILLING_CONTENT.colValue },
          { key: "sharePct", label: CUSTOMER_BILLING_CONTENT.colShare },
        ];

  return (
    <CommercialSectionCard
      title={title}
      hint={CM_HELP.customers.billingByProduct}
      actions={
        <div className="cm-portfolio-billing-by-product__actions">
          <CommercialSegmentToggle
            ariaLabel="Agrupar por produto ou família"
            idPrefix="portfolio-billing-group-by"
            value={groupBy}
            onChange={(value) => {
              if (value === "product" || value === "product_group") setGroupBy(value);
            }}
            options={[
              { value: "product", label: CUSTOMER_BILLING_CONTENT.byProductGroupProduct },
              {
                value: "product_group",
                label: CUSTOMER_BILLING_CONTENT.byProductGroupFamily,
              },
            ]}
          />
        </div>
      }
    >
      <CommercialDataListToolbar
        style={tableStyle}
        hint={
          <span className="delpi-ui-section-hint-label">
            {visibleColumnCount} coluna(s) · {rows.length.toLocaleString("pt-BR")} linha(s)
          </span>
        }
        actions={
          <>
            <CommercialTabularExportButtons
              compact
              disabled={!rows.length || loading}
              onExport={(format) => {
                runTabularExport({
                  kind: "table",
                  format,
                  payload: {
                    title,
                    columns: exportColumns,
                    rows: rows.map((row) => ({
                      label: row.label,
                      domestic: formatAmount(row.domestic),
                      export: formatAmount(row.export),
                      total: formatAmount(row.total),
                      sharePct: formatSharePct(row.sharePct),
                    })),
                  },
                });
              }}
            />
            <CommercialTableFontSizeControls
              fontSize={fontSize}
              onIncrease={increaseFont}
              onDecrease={decreaseFont}
              onReset={resetFont}
              canIncrease={canIncreaseFont}
              canDecrease={canDecreaseFont}
              isDefault={isDefaultFont}
            />
            <CommercialTableColumnVisibilityMenu
              columns={orderedColumns}
              visibility={visibility}
              onToggleColumn={setColumnVisible}
              onReorderColumns={reorderColumns}
              onReset={resetColumns}
              labels={{
                trigger: "Colunas",
                panelTitle: "Colunas do mix",
                reset: "Restaurar padrão",
                hint: CM_HELP.customers.billingByProductColumns,
                columnAriaLabel: (label) => `Exibir coluna ${label}`,
                reorderAriaLabel: (label) => `Reordenar coluna ${label}`,
              }}
            />
          </>
        }
      />
      {loading && !rows.length ? (
        <CommercialLoadingCard
          title={CUSTOMER_BILLING_CONTENT.loadingByProduct}
          variant="panel"
        />
      ) : null}
      {error && !rows.length ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {!loading && !error && !rows.length ? (
        <>
          <CommercialEmptyState title={CUSTOMER_BILLING_CONTENT.emptyByProduct} />
          {hasFilters ? (
            <CommercialClearFiltersButton
              onClick={filters.clearProductAndMarketFilters}
              label={CUSTOMER_BILLING_CONTENT.clearFilters}
            />
          ) : null}
        </>
      ) : null}
      {rows.length ? (
        <>
          {error ? <CommercialStateBanner>{error}</CommercialStateBanner> : null}
          <div style={tableStyle}>
            <DataTable
              classNames={sentenceTableClassNames()}
              labels={cmDataTableLabels}
              columns={visibleColumns}
              rows={rows}
              rowKey={(row) => row.id}
              layout="section"
              emptyMessage={CUSTOMER_BILLING_CONTENT.emptyByProduct}
              enableColumnReorder
              onColumnOrderChange={applyVisibleOrder}
            />
          </div>
          {showCountries ? (
            <p className="cm-muted">
              * {CUSTOMER_BILLING_CONTENT.exportCountriesPrefix} {countries.join(", ")}
            </p>
          ) : null}
        </>
      ) : null}
    </CommercialSectionCard>
  );
}
