import { useEffect, useMemo, useState } from "react";
import { DataTable, runTabularExport } from "@delpi/plugin-ui/index";

import { getCommercialRolByCustomer } from "../../../api/analyticsApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialSectionCard,
  CommercialStateBanner,
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
import { billingSeriesPresetLabel } from "../utils/billingSeriesPeriod";
import type { PortfolioBillingWorkspaceFilters } from "../hooks/usePortfolioBillingWorkspaceFilters";
import {
  formatCityState,
  formatCnpj,
  formatSharePct,
} from "../utils/portfolioBillingTableMappers";

type PortfolioBillingAbcTableProps = {
  filters: PortfolioBillingWorkspaceFilters;
  sellerId?: string | null;
  active?: boolean;
  billingNature?: PortfolioBillingAmountNature;
};

type AbcRow = {
  id: string;
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

  const columns = useMemo((): DataTableColumn<AbcRow>[] => {
    return [
      {
        key: "customer",
        header: CUSTOMER_BILLING_CONTENT.colCustomer,
        render: (row) => row.customerName,
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
  }, []);

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
    <CommercialSectionCard
      title={title}
      hint={CM_HELP.customers.billingAbc}
      actions={
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
      }
    >
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
            <CommercialActionButton
              variant="ghost"
              onClick={filters.clearProductAndMarketFilters}
            >
              {CUSTOMER_BILLING_CONTENT.clearFilters}
            </CommercialActionButton>
          ) : null}
        </>
      ) : null}
      {rows.length ? (
        <>
          {error ? <CommercialStateBanner>{error}</CommercialStateBanner> : null}
          <DataTable
            classNames={sentenceTableClassNames()}
            labels={cmDataTableLabels}
            columns={columns}
            rows={rows}
            rowKey={(row) => row.id}
            layout="section"
            emptyMessage={CUSTOMER_BILLING_CONTENT.emptyAbc}
          />
        </>
      ) : null}
    </CommercialSectionCard>
  );
}
