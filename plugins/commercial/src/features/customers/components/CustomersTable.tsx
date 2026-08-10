import { useEffect, useState, type MouseEvent } from "react";

import {
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialStatusBadge,
  CommercialTableColumnVisibilityMenu,
  type DataTableColumn,
  type DataTableColumnWidths,
} from "../../../app/commercialUi";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import {
  buildCustomerDetailPath,
  navigateCustomerDetail,
} from "../../../app/pluginNavigation";
import type { CustomersListSellerAccess } from "../../../utils/customersListDeepLink";
import type {
  CustomerListSortDirection,
  CustomerListSortKey,
  CustomerSummary,
} from "../types/customerSummary";
import {
  resolveCustomerStatus,
  statusLabel,
} from "../utils/customerListPresentation";
import { CM_HELP } from "../../../content/helpTooltips";
import { BillingTrendCell } from "./BillingTrendCell";
import { CustomerAvatar } from "./CustomerAvatar";

const CUSTOMER_TABLE_PREFERENCES_KEY = "commercial:customers:table-columns:v1";

const CUSTOMER_COLUMN_CATALOG = [
  { key: "nome", label: "Cliente" },
  { key: "sellerName", label: "Vendedor" },
  { key: "city", label: "Cidade / UF" },
  { key: "lastPurchaseDate", label: "Última venda" },
  { key: "billed12m", label: "Fat. 12 meses" },
  { key: "billingTrend", label: "Tendência" },
  { key: "status", label: "Status" },
  { key: "valorTotalAberto", label: "Em aberto" },
  { key: "quantidadePedidosAtrasados", label: "Atrasos" },
  { key: "proximaEntrega", label: "Próxima entrega" },
] as const;

type CustomerTablePreferences = {
  visibility: Record<string, boolean>;
  order: string[];
  widths: DataTableColumnWidths;
};

function defaultTablePreferences(): CustomerTablePreferences {
  return {
    visibility: Object.fromEntries(CUSTOMER_COLUMN_CATALOG.map((column) => [column.key, true])),
    order: CUSTOMER_COLUMN_CATALOG.map((column) => column.key),
    widths: {},
  };
}

function loadTablePreferences(): CustomerTablePreferences {
  const defaults = defaultTablePreferences();
  if (typeof window === "undefined") return defaults;
  try {
    const parsed = JSON.parse(
      window.localStorage.getItem(CUSTOMER_TABLE_PREFERENCES_KEY) ?? "null",
    ) as Partial<CustomerTablePreferences> | null;
    if (!parsed) return defaults;
    const known = new Set(defaults.order);
    const savedOrder = Array.isArray(parsed.order)
      ? parsed.order.filter((key, index, values) => known.has(key) && values.indexOf(key) === index)
      : [];
    const order = [
      ...savedOrder,
      ...defaults.order.filter((key) => !savedOrder.includes(key)),
    ];
    const visibility = Object.fromEntries(
      defaults.order.map((key) => [key, parsed.visibility?.[key] !== false]),
    );
    if (!Object.values(visibility).some(Boolean)) visibility.nome = true;
    return {
      visibility,
      order,
      widths:
        parsed.widths && typeof parsed.widths === "object"
          ? Object.fromEntries(
              Object.entries(parsed.widths).filter(
                ([key, value]) => known.has(key) && typeof value === "number",
              ),
            )
          : {},
    };
  } catch {
    return defaults;
  }
}

type CustomersTableProps = {
  customers: CustomerSummary[];
  sortKey: CustomerListSortKey;
  sortDirection: CustomerListSortDirection;
  onSort: (key: Exclude<CustomerListSortKey, "attention">) => void;
  basePath: string;
  listSearch: string;
  sellerAccess: CustomersListSellerAccess;
  loading?: boolean;
  emptyMessage?: string;
};

function statusVariant(
  status: ReturnType<typeof resolveCustomerStatus>,
): "success" | "warning" | "neutral" {
  if (status === "ativo") return "success";
  if (status === "atencao") return "warning";
  return "neutral";
}

export function CustomersTable({
  customers,
  sortKey,
  sortDirection,
  onSort,
  basePath,
  listSearch,
  sellerAccess,
  loading = false,
  emptyMessage = "Nenhum cliente corresponde aos filtros selecionados.",
}: CustomersTableProps) {
  const [tablePreferences, setTablePreferences] = useState(loadTablePreferences);

  useEffect(() => {
    try {
      window.localStorage.setItem(
        CUSTOMER_TABLE_PREFERENCES_KEY,
        JSON.stringify(tablePreferences),
      );
    } catch {
      // Preferência local é progressiva; a tabela continua funcional sem storage.
    }
  }, [tablePreferences]);

  const detailHref = (customer: CustomerSummary) => {
    const path = buildCustomerDetailPath(basePath, customer.codigo, customer.loja);
    return path ? `${path}${listSearch}` : `${basePath}/customers${listSearch}`;
  };

  const openCustomer = (customer: CustomerSummary) =>
    navigateCustomerDetail(customer.codigo, customer.loja, {
      basePath,
      search: listSearch,
      sellerAccess,
    });

  const handleExplicitNavigate = (
    event: MouseEvent<HTMLAnchorElement>,
    customer: CustomerSummary,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    openCustomer(customer);
  };

  const columns: DataTableColumn<CustomerSummary>[] = [
      {
        key: "nome",
        header: "Cliente",
        sortable: true,
        interactive: true,
        render: (customer) => {
          const codeStore =
            formatEntityCodeStore(customer.codigo, customer.loja) ??
            `${customer.codigo}-${customer.loja}`;
          return (
            <a
              href={detailHref(customer)}
              aria-label={`Abrir cliente ${customer.nome || codeStore}`}
              onClick={(event) => handleExplicitNavigate(event, customer)}
            >
              <strong>{customer.nome || codeStore}</strong>
              <span className="cm-customer-identity__code">
                {customer.codigo} · Loja {customer.loja}
              </span>
            </a>
          );
        },
      },
      {
        key: "sellerName",
        header: "Vendedor",
        sortable: true,
        render: (customer) => customer.sellerName?.trim() || "—",
      },
      {
        key: "city",
        header: "Cidade / UF",
        sortable: true,
        render: (customer) =>
          customer.city || customer.state
            ? [customer.city, customer.state].filter(Boolean).join(" / ")
            : "—",
      },
      {
        key: "lastPurchaseDate",
        header: "Última venda",
        sortable: true,
        render: (customer) => formatDisplayDate(customer.lastPurchaseDate ?? null),
      },
      {
        key: "billed12m",
        header: "Fat. 12 meses",
        sortable: true,
        align: "right",
        render: (customer) => formatCurrency(customer.billed12m ?? 0),
      },
      {
        key: "billingTrend",
        header: "Tendência",
        headerHint: CM_HELP.customers.trend,
        sortable: true,
        render: (customer) => (
          <BillingTrendCell trend={customer.billingTrend} pct={customer.billingTrendPct} />
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (customer) => {
          const status = customer.status ?? resolveCustomerStatus(customer);
          return (
            <CommercialStatusBadge
              label={statusLabel(status)}
              variant={statusVariant(status)}
            />
          );
        },
      },
      {
        key: "valorTotalAberto",
        header: "Em aberto",
        sortable: true,
        align: "right",
        render: (customer) => formatCurrency(customer.valorTotalAberto),
      },
      {
        key: "quantidadePedidosAtrasados",
        header: "Atrasos",
        sortable: true,
        align: "right",
        render: (customer) =>
          customer.quantidadePedidosAtrasados.toLocaleString("pt-BR"),
      },
      {
        key: "proximaEntrega",
        header: "Próxima entrega",
        sortable: true,
        render: (customer) => formatDisplayDate(customer.proximaEntrega),
      },
  ];
  const columnsByKey = new Map(columns.map((column) => [column.key, column]));
  const visibleColumns = tablePreferences.order
    .filter((key) => tablePreferences.visibility[key])
    .map((key) => columnsByKey.get(key))
    .filter((column): column is DataTableColumn<CustomerSummary> => Boolean(column));
  const orderedCatalog = tablePreferences.order
    .map((key) => CUSTOMER_COLUMN_CATALOG.find((column) => column.key === key))
    .filter((column): column is (typeof CUSTOMER_COLUMN_CATALOG)[number] => Boolean(column));

  const setColumnVisible = (key: string, visible: boolean) => {
    setTablePreferences((current) => {
      const visibleCount = current.order.filter((columnKey) => current.visibility[columnKey]).length;
      if (!visible && current.visibility[key] && visibleCount <= 1) return current;
      return {
        ...current,
        visibility: { ...current.visibility, [key]: visible },
      };
    });
  };

  const reorderColumns = (fromKey: string, toKey: string) => {
    setTablePreferences((current) => {
      const fromIndex = current.order.indexOf(fromKey);
      const toIndex = current.order.indexOf(toKey);
      if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex) return current;
      const order = [...current.order];
      const [moved] = order.splice(fromIndex, 1);
      order.splice(toIndex, 0, moved);
      return { ...current, order };
    });
  };

  const applyVisibleOrder = (visibleOrder: string[]) => {
    setTablePreferences((current) => {
      let visibleIndex = 0;
      return {
        ...current,
        order: current.order.map((key) =>
          current.visibility[key] ? (visibleOrder[visibleIndex++] ?? key) : key,
        ),
      };
    });
  };

  return (
    <>
      <div className="cm-customers-list__desktop">
        <div className="cm-customers-list__toolbar">
          <CommercialTableColumnVisibilityMenu
            columns={orderedCatalog}
            visibility={tablePreferences.visibility}
            onToggleColumn={setColumnVisible}
            onReset={() => setTablePreferences(defaultTablePreferences())}
            onReorderColumns={reorderColumns}
            labels={{
              trigger: "Colunas",
              panelTitle: "Colunas da carteira",
              reset: "Restaurar padrão",
              hint: "Escolha e reordene as colunas exibidas.",
              columnAriaLabel: (label) => `Exibir coluna ${label}`,
              reorderAriaLabel: (label) => `Reordenar coluna ${label}`,
            }}
          />
        </div>
        <CommercialDataTable
          rows={customers}
          columns={visibleColumns}
          rowKey={(customer) => customer.key}
          layout="section"
          loading={loading}
          emptyMessage={emptyMessage}
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSortChange={(key) => onSort(key as Exclude<CustomerListSortKey, "attention">)}
          onRowClick={openCustomer}
          rowClickRole="button"
          columnWidths={tablePreferences.widths}
          onColumnWidthsChange={(widths) =>
            setTablePreferences((current) => ({ ...current, widths }))
          }
          resizableColumns
          enableColumnReorder
          onColumnOrderChange={applyVisibleOrder}
        />
      </div>

      <div className="cm-customers-list__mobile" aria-label="Clientes da carteira">
        {customers.map((customer) => {
          const status = customer.status ?? resolveCustomerStatus(customer);
          const codeStore =
            formatEntityCodeStore(customer.codigo, customer.loja) ??
            `${customer.codigo}-${customer.loja}`;
          return (
            <CommercialDataRecordCard
              key={customer.key}
              leading={
                <CustomerAvatar
                  code={customer.codigo}
                  store={customer.loja}
                  name={customer.nome}
                  hasAvatar={Boolean(customer.hasAvatar)}
                  size="sm"
                />
              }
              title={customer.nome || codeStore}
              subtitle={`${customer.codigo} · Loja ${customer.loja}`}
              status={
                <CommercialStatusBadge
                  label={statusLabel(status)}
                  variant={statusVariant(status)}
                />
              }
              fields={[
                {
                  id: "last-sale",
                  label: "Última venda",
                  value: formatDisplayDate(customer.lastPurchaseDate ?? null),
                },
                {
                  id: "open-value",
                  label: "Em aberto",
                  value: formatCurrency(customer.valorTotalAberto),
                },
                {
                  id: "late",
                  label: "Atrasos",
                  value: customer.quantidadePedidosAtrasados.toLocaleString("pt-BR"),
                },
                {
                  id: "next-delivery",
                  label: "Próxima entrega",
                  value: formatDisplayDate(customer.proximaEntrega),
                },
              ]}
              context={customer.nextAction || "Ver conta"}
              href={detailHref(customer)}
              onNavigate={(event) => handleExplicitNavigate(event, customer)}
              ariaLabel={`Abrir cliente ${customer.nome || codeStore}`}
            />
          );
        })}
      </div>
    </>
  );
}
