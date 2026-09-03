import { useEffect, useMemo, useState } from "react";
import { DataTable, runTabularExport } from "@delpi/plugin-ui/index";

import { getCommercialRolByCustomer } from "../../../api/analyticsApi";
import {
  CommercialClearFiltersButton,
  CommercialDataListToolbar,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSectionCard,
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
import type { CommercialRolByCustomerItem } from "../../../types/analytics";
import {
  customerAvatarKey,
  useCustomerAvatarPresence,
} from "../../../hooks/useCustomerAvatarPresence";
import { OtdCustomerIdentityCell } from "../../analytics/components/OtdCustomerIdentityCell";
import { billingSeriesPresetLabel } from "../utils/billingSeriesPeriod";
import { usePortfolioBillingTablePreferences } from "../hooks/usePortfolioBillingTablePreferences";
import type { PortfolioBillingWorkspaceFilters } from "../hooks/usePortfolioBillingWorkspaceFilters";
import {
  PORTFOLIO_ABC_COLUMN_CATALOG,
  PORTFOLIO_ABC_COLUMNS_STORAGE_KEY,
  PORTFOLIO_ABC_FONT_STORAGE_KEY,
} from "../utils/portfolioBillingTableColumns";
import {
  formatCityState,
  formatCnpj,
  formatSharePct,
} from "../utils/portfolioBillingTableMappers";
import {
  PORTFOLIO_ABC_COLUMN_HELP,
  withColumnHelp,
} from "../../../utils/customersColumnHelp";

type PortfolioBillingAbcTableProps = {
  filters: PortfolioBillingWorkspaceFilters;
  sellerId?: string | null;
  active?: boolean;
  billingNature?: PortfolioBillingAmountNature;
};

type AbcRow = {
  id: string;
  customerCode: string;
  customerStore: string;
  customerName: string;
  cnpj: string;
  cityState: string;
  sharePct: number | null;
  amount: number;
};

function sentenceTableClassNames() {
  return {
    ...cmDataTableClassNames,
    wrapSection: [cmDataTableClassNames.wrapSection, cmDataTableClassNames.sentenceHeadersWrap]
      .filter(Boolean)
      .join(" "),
  };
}

function itemAmount(
  item: CommercialRolByCustomerItem,
  nature: PortfolioBillingAmountNature,
): number {
  return nature === "gross"
    ? Number(item.gross_revenue ?? item.rol ?? 0)
    : Number(item.rol ?? 0);
}

export function PortfolioBillingAbcTable({
  filters,
  sellerId = null,
  active = true,
  billingNature = "gross",
}: PortfolioBillingAbcTableProps) {
  const [items, setItems] = useState<CommercialRolByCustomerItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
    columnsStorageKey: PORTFOLIO_ABC_COLUMNS_STORAGE_KEY,
    fontSizeStorageKey: PORTFOLIO_ABC_FONT_STORAGE_KEY,
    columns: PORTFOLIO_ABC_COLUMN_CATALOG,
    emptyFallbackKeys: ["customer", "share"],
  });

  const queryEnabled =
    active && !filters.periodError && Boolean(filters.startDate && filters.endDate);

  useEffect(() => {
    if (!queryEnabled) return;
    const controller = new AbortController();
    let cancelled = false;
    setLoading(true);
    setError(null);

    void getCommercialRolByCustomer(
      {
        start_date: filters.startDate,
        end_date: filters.endDate,
        seller_id: sellerId || undefined,
        customer_codes: filters.customerCodesCsv || undefined,
        product_codes: filters.productCodesCsv || undefined,
        product_groups: filters.productGroupsCsv || undefined,
        market: filters.marketParam,
        limit: 500,
        include_others: false,
        nature: billingNature,
      },
      controller.signal,
    )
      .then((data) => {
        if (cancelled) return;
        setItems(Array.isArray(data.items) ? data.items : []);
      })
      .catch((err: unknown) => {
        if (cancelled || controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar ABC.");
        setItems([]);
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
    sellerId,
    billingNature,
  ]);

  const rows = useMemo((): AbcRow[] => {
    const mapped = items.map((item, index) => ({
      id: `${item.customer_code}|${item.customer_store || ""}|${index}`,
      customerCode: (item.customer_code || "").trim(),
      customerStore: (item.customer_store || "01").trim() || "01",
      customerName: item.customer_name || item.customer_code || "—",
      cnpj: formatCnpj(item.cnpj),
      cityState: formatCityState(item.city, item.state),
      sharePct: item.share_pct ?? null,
      amount: itemAmount(item, billingNature),
    }));
    if (billingNature === "gross") {
      const total = mapped.reduce((acc, row) => acc + row.amount, 0);
      return mapped
        .map((row) => ({
          ...row,
          sharePct:
            total > 0 ? Math.round((row.amount * 1000) / total) / 10 : null,
        }))
        .sort((a, b) => (b.sharePct ?? -1) - (a.sharePct ?? -1));
    }
    return mapped.sort((a, b) => (b.sharePct ?? -1) - (a.sharePct ?? -1));
  }, [items, billingNature]);

  const avatarPairs = useMemo(
    () =>
      rows
        .filter((row) => row.customerCode)
        .map((row) => ({
          customer_code: row.customerCode,
          customer_store: row.customerStore,
        })),
    [rows],
  );
  const avatarPresence = useCustomerAvatarPresence(avatarPairs);

  const columns = useMemo((): DataTableColumn<AbcRow>[] => {
    return [
      {
        key: "customer",
        header: CUSTOMER_BILLING_CONTENT.colCustomer,
        interactive: true,
        rowClick: "stop",
        render: (row) =>
          row.customerCode ? (
            <OtdCustomerIdentityCell
              customer={{
                code: row.customerCode,
                store: row.customerStore,
                name: row.customerName,
                hasAvatar: avatarPresence.get(
                  customerAvatarKey(row.customerCode, row.customerStore),
                ),
              }}
              size="sm"
              returnLabel="Minha Carteira"
            />
          ) : (
            row.customerName
          ),
        sortValue: (row) => row.customerName,
        sortable: true,
      },
      {
        key: "cnpj",
        header: CUSTOMER_BILLING_CONTENT.colCnpj,
        render: (row) => row.cnpj,
        sortValue: (row) => row.cnpj,
        sortable: true,
      },
      {
        key: "city",
        header: CUSTOMER_BILLING_CONTENT.colCityState,
        render: (row) => row.cityState,
        sortValue: (row) => row.cityState,
        sortable: true,
      },
      {
        key: "share",
        header: CUSTOMER_BILLING_CONTENT.colShare,
        render: (row) => formatSharePct(row.sharePct),
        sortValue: (row) => row.sharePct ?? -1,
        sortable: true,
        align: "right",
      },
    ];
  }, [avatarPresence]);

  const visibleColumns = useMemo(
    () => filterColumns(withColumnHelp(columns, PORTFOLIO_ABC_COLUMN_HELP)),
    [columns, filterColumns],
  );

  const periodLabel = billingSeriesPresetLabel(filters.preset);
  const title = appendBillingNatureContext(
    `${CUSTOMER_BILLING_CONTENT.abcTitle} — ${periodLabel}`,
    billingNature,
  );
  const hasFilters =
    filters.selectedProductCodes.length > 0 ||
    filters.selectedProductGroups.length > 0 ||
    filters.selectedMarkets.length > 0 ||
    filters.selectedCustomerKeys.length > 0;

  return (
    <CommercialSectionCard title={title} hint={CM_HELP.customers.billingAbc}>
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
                    columns: [
                      { key: "customerName", label: CUSTOMER_BILLING_CONTENT.colCustomer },
                      { key: "cnpj", label: CUSTOMER_BILLING_CONTENT.colCnpj },
                      { key: "cityState", label: CUSTOMER_BILLING_CONTENT.colCityState },
                      { key: "sharePct", label: CUSTOMER_BILLING_CONTENT.colShare },
                    ],
                    rows: rows.map((row) => ({
                      customerName: row.customerName,
                      cnpj: row.cnpj,
                      cityState: row.cityState,
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
                panelTitle: "Colunas do ABC",
                reset: "Restaurar padrão",
                hint: CM_HELP.customers.billingAbcColumns,
                columnAriaLabel: (label) => `Exibir coluna ${label}`,
                reorderAriaLabel: (label) => `Reordenar coluna ${label}`,
              }}
            />
          </>
        }
      />
      {loading && !rows.length ? (
        <CommercialLoadingCard title={CUSTOMER_BILLING_CONTENT.loadingAbc} variant="panel" />
      ) : null}
      {error && !rows.length ? (
        <CommercialStateBanner variant="error">{error}</CommercialStateBanner>
      ) : null}
      {!loading && !error && !rows.length ? (
        <>
          <CommercialEmptyState title={CUSTOMER_BILLING_CONTENT.emptyAbc} />
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
              emptyMessage={CUSTOMER_BILLING_CONTENT.emptyAbc}
              enableColumnReorder
              onColumnOrderChange={applyVisibleOrder}
            />
          </div>
        </>
      ) : null}
    </CommercialSectionCard>
  );
}
