import { useEffect, useMemo, useState } from "react";
import {
  DataTable,
  EmptyState,
  SectionCard,
  StateBanner,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import { enrichPortfolioCustomers } from "../../api/commercialPortfolioApi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { navigateCustomerDetail } from "../../app/pluginNavigation";
import {
  CommercialLoadingCard,
  CommercialSelectField,
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmFiltersKit,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStateBannerClassNames,
  cmStatusBadgeClassNames,
} from "../../app/commercialUi";
import type { CustomerEnrichmentItem, SellerCustomer } from "../../types/portfolio";
import { customerKey, formatCurrency, formatDate } from "../../shared/format";

const { FiltersRow, FilterInputField } = cmFiltersKit;

type CustomerRow = SellerCustomer & {
  key: string;
  city: string | null;
  state: string | null;
  lastPurchaseDate: string | null;
  billed12m: number;
  hasAvatar: boolean;
};

type CustomersPageProps = {
  basePath: string;
};

export function CustomersPage({ basePath }: CustomersPageProps) {
  const {
    loading: scopeLoading,
    error: scopeError,
    isAdmin,
    myPortfolio,
    sellers,
    sellerIdFilter,
    setSellerIdFilter,
  } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<CustomerRow[]>([]);
  const [search, setSearch] = useState("");

  const activePortfolio = isAdmin
    ? (sellers.find((seller) => seller.id === sellerIdFilter) ?? null)
    : myPortfolio;

  useEffect(() => {
    const controller = new AbortController();
    const customers = activePortfolio?.customers ?? [];

    if (isAdmin && !activePortfolio) {
      setRows([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    if (customers.length === 0) {
      setRows([]);
      setLoading(false);
      return () => controller.abort();
    }

    enrichPortfolioCustomers(
      customers.map((item) => ({
        customer_code: item.customer_code,
        customer_store: item.customer_store,
      })),
      controller.signal,
    )
      .then((enriched) => {
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
              hasAvatar: enrich?.has_avatar ?? false,
            };
          }),
        );
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar clientes.");
        setRows([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePortfolio?.id]);

  const filteredRows = useMemo(() => {
    const normalized = search.trim().toLocaleLowerCase("pt-BR");
    if (!normalized) return rows;
    return rows.filter((row) => {
      const haystack = [row.customer_code, row.customer_name]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("pt-BR");
      return haystack.includes(normalized);
    });
  }, [rows, search]);

  const sellerOptions = useMemo(
    () => sellers.map((seller) => ({ value: seller.id, label: seller.display_name })),
    [sellers],
  );

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
      {
        key: "avatar",
        header: "Logo",
        render: (row) => (
          <StatusBadge
            label={row.hasAvatar ? "Cadastrado" : "Sem logo"}
            variant={row.hasAvatar ? "success" : "neutral"}
            classNames={cmStatusBadgeClassNames}
          />
        ),
      },
    ],
    [],
  );

  const showLoading = scopeLoading || loading;
  const showError = scopeError ?? error;

  return (
    <section className="cm-page-stack">
      <SectionCard
        title={isAdmin ? "Clientes por carteira" : "Minha carteira"}
        subtitle="Clientes vinculados à carteira com enriquecimento comercial."
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <FiltersRow>
          <FilterInputField
            label="Buscar"
            type="search"
            value={search}
            onChange={setSearch}
            placeholder="Código ou nome do cliente"
          />
          {isAdmin ? (
            <CommercialSelectField
              label="Carteira"
              value={sellerIdFilter ?? ""}
              onChange={(value: string) => setSellerIdFilter(value || null)}
              options={sellerOptions}
              allowEmpty
              emptyLabel="Selecione uma carteira"
              searchable
            />
          ) : null}
        </FiltersRow>

        {showLoading ? (
          <CommercialLoadingCard title="Carregando carteira" variant="panel" />
        ) : showError ? (
          <StateBanner variant="error" classNames={cmStateBannerClassNames}>
            {showError}
          </StateBanner>
        ) : isAdmin && !activePortfolio ? (
          <EmptyState
            title="Selecione uma carteira"
            message="Escolha uma carteira de vendedor para ver os clientes vinculados."
            defaultMessage="Escolha uma carteira de vendedor para ver os clientes vinculados."
            classNames={cmEmptyStateClassNames}
          />
        ) : filteredRows.length === 0 ? (
          <EmptyState
            title="Carteira vazia"
            message="Nenhum cliente vinculado para os filtros atuais."
            defaultMessage="Nenhum cliente vinculado."
            classNames={cmEmptyStateClassNames}
          />
        ) : (
          <DataTable
            rows={filteredRows}
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
