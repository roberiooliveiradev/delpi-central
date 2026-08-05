import { useEffect, useMemo, useState } from "react";
import {
  DataTable,
  EmptyState,
  SectionCard,
  StateBanner,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  enrichPortfolioCustomers,
  getMySellerPortfolio,
} from "../../api/commercialPortfolioApi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { navigateCustomerDetail } from "../../app/pluginNavigation";
import {
  CommercialLoadingCard,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStateBannerClassNames,
} from "../../app/commercialUi";
import type { CustomerEnrichmentItem, SellerCustomer } from "../../types/portfolio";
import { customerKey, formatCurrency, formatDate } from "../../shared/format";

type CustomerRow = SellerCustomer & {
  key: string;
  city: string | null;
  state: string | null;
  lastPurchaseDate: string | null;
  billed12m: number;
};

type CustomersPageProps = {
  basePath: string;
};

export function CustomersPage({ basePath }: CustomersPageProps) {
  const { loading: scopeLoading, error: scopeError } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<CustomerRow[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getMySellerPortfolio(controller.signal)
      .then(async (me) => {
        const customers = me.portfolio?.customers ?? [];
        if (customers.length === 0) {
          setRows([]);
          return;
        }

        const enriched = await enrichPortfolioCustomers(
          customers.map((item) => ({
            customer_code: item.customer_code,
            customer_store: item.customer_store,
          })),
          controller.signal,
        );
        const enrichmentByKey = new Map<string, CustomerEnrichmentItem>();
        for (const item of enriched) {
          enrichmentByKey.set(customerKey(item.customer_code, item.customer_store), item);
        }

        setRows(
          customers.map((customer) => {
            const enrich = enrichmentByKey.get(
              customerKey(customer.customer_code, customer.customer_store),
            );
            return {
              ...customer,
              key: customerKey(customer.customer_code, customer.customer_store),
              city: enrich?.city ?? null,
              state: enrich?.state ?? null,
              lastPurchaseDate: enrich?.last_purchase_date ?? null,
              billed12m: enrich?.billed_12m ?? 0,
            };
          }),
        );
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao carregar clientes.");
        setRows([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, []);

  const columns = useMemo<DataTableColumn<CustomerRow>[]>(
    () => [
      { key: "code", header: "Código", render: (row) => row.customer_code },
      { key: "store", header: "Loja", render: (row) => row.customer_store },
      {
        key: "name",
        header: "Cliente",
        render: (row) => row.customer_name?.trim() || "—",
      },
      {
        key: "location",
        header: "Cidade/UF",
        render: (row) =>
          [row.city, row.state].filter(Boolean).join("/") || "—",
      },
      {
        key: "billed",
        header: "Faturado 12m",
        align: "right",
        render: (row) => formatCurrency(row.billed12m),
      },
      {
        key: "lastPurchase",
        header: "Última compra",
        render: (row) => formatDate(row.lastPurchaseDate),
      },
    ],
    [],
  );

  const showLoading = scopeLoading || loading;
  const showError = scopeError ?? error;

  return (
    <section className="cm-page-stack">
      <SectionCard
        title="Minha carteira"
        subtitle="Clientes vinculados à sua carteira com enriquecimento comercial."
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {showLoading ? (
          <CommercialLoadingCard title="Carregando carteira" variant="panel" />
        ) : showError ? (
          <StateBanner variant="error" classNames={cmStateBannerClassNames}>
            {showError}
          </StateBanner>
        ) : rows.length === 0 ? (
          <EmptyState
            title="Carteira vazia"
            message="Nenhum cliente vinculado. Peça ao administrador para vincular clientes."
            defaultMessage="Nenhum cliente vinculado."
            classNames={cmEmptyStateClassNames}
          />
        ) : (
          <DataTable
            rows={rows}
            columns={columns}
            rowKey={(row: CustomerRow) => row.key}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
            onRowClick={(row: CustomerRow) =>
              navigateCustomerDetail(row.customer_code, row.customer_store, { basePath })
            }
            rowClickRole="button"
          />
        )}
      </SectionCard>
    </section>
  );
}
