import {
  HelpTooltip,
  OPERATIONAL_UNIT_COLUMN_LABEL,
  IconButton,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { ChevronDown, ChevronRight } from "lucide-react";
import { type ReactNode, useMemo, useState } from "react";

import {
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialEntityLink,
  CommercialFilterBarShell,
  CommercialScopeChipBar,
  CommercialSectionCard,
  CommercialStatusBadge,
  CommercialTextField,
} from "../../../app/commercialUi";
import {
  currentLocationAsReturnTo,
} from "../../../app/commercialNavigationReturn";
import {
  buildCustomerOrderDetailHref,
  navigateCustomerOrderDetail,
} from "../../../app/pluginNavigation";
import { orderLinkTitle } from "../../../content/entityLinkHints";
import { CUSTOMER_ORDERS_CONTENT } from "../../../content/customerOrdersContent";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  CUSTOMER_ORDERS_COLUMN_HELP,
  withColumnHelp,
} from "../../../utils/customersColumnHelp";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import {
  nextTableSortState,
  sortTableRows,
  type TableSortDirection,
} from "../../../utils/sortTableRows";
import type {
  CustomerOrderSituation,
  CustomerOrderSummary,
} from "../types/customerOrderSummary";
import { orderSituationLabel } from "../utils/customerOrderAggregation";
import { CustomerOrderLines } from "./CustomerOrderLines";

type CustomerOrdersTableProps = {
  orders: CustomerOrderSummary[];
  basePath: string;
  codigo: string;
  loja: string;
  canViewAnalytics: boolean;
};

type SituationFilter = "all" | CustomerOrderSituation;

type OrderSortKey =
  | "branch"
  | "order"
  | "customer-order"
  | "status"
  | "lines"
  | "overdue"
  | "delivery"
  | "value";

function formatMaxOverdue(days: number): string {
  if (days <= 0) return "—";
  if (days === 1) return "1 dia";
  return `${days.toLocaleString("pt-BR")} dias`;
}

function renderStatus(order: CustomerOrderSummary): ReactNode {
  return (
    <CommercialStatusBadge
      variant={
        order.situacao === "atrasado"
          ? "danger"
          : order.situacao === "parcial"
            ? "warning"
            : "neutral"
      }
      label={orderSituationLabel(order.situacao)}
    />
  );
}

function orderMatchesSearch(order: CustomerOrderSummary, query: string): boolean {
  if (!query) return true;
  const haystack = [
    order.pedido,
    order.pedidoCliente,
    order.filial,
    formatOperationalUnitCode(order.filial),
    orderSituationLabel(order.situacao),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

export function CustomerOrdersTable({
  orders,
  basePath,
  codigo,
  loja,
  canViewAnalytics,
}: CustomerOrdersTableProps) {
  const [expandedRowKey, setExpandedRowKey] = useState<string | null>(null);
  const [situationFilter, setSituationFilter] = useState<SituationFilter>("all");
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<OrderSortKey>("overdue");
  const [sortDirection, setSortDirection] = useState<TableSortDirection>("desc");

  const orderReturnNav = {
    returnTo: currentLocationAsReturnTo(),
    returnLabel: "Pedidos da conta",
  };

  const openOrderDetail = (order: CustomerOrderSummary) => {
    if (!order.filial?.trim() || !order.pedido?.trim()) return;
    navigateCustomerOrderDetail(codigo, loja, order.filial, order.pedido, {
      basePath,
      returnNav: orderReturnNav,
    });
  };

  const orderHref = (order: CustomerOrderSummary) =>
    buildCustomerOrderDetailHref(codigo, loja, order.filial, order.pedido, {
      basePath,
      returnNav: orderReturnNav,
    });

  const toggleExpand = (orderKey: string) => {
    setExpandedRowKey((current) => (current === orderKey ? null : orderKey));
  };

  const situationCounts = useMemo(() => {
    const counts: Record<SituationFilter, number> = {
      all: orders.length,
      atrasado: 0,
      parcial: 0,
      em_aberto: 0,
    };
    for (const order of orders) {
      counts[order.situacao] += 1;
    }
    return counts;
  }, [orders]);

  const filteredOrders = useMemo(() => {
    const query = search.trim().toLowerCase();
    return orders.filter((order) => {
      if (situationFilter !== "all" && order.situacao !== situationFilter) {
        return false;
      }
      return orderMatchesSearch(order, query);
    });
  }, [orders, search, situationFilter]);

  const columns: DataTableColumn<CustomerOrderSummary>[] = useMemo(
    () => [
      {
        key: "expand",
        header: "",
        className: "delpi-ui-table__col--compact",
        interactive: true,
        rowClick: "stop",
        render: (order) => {
          const isExpanded = expandedRowKey === order.key;
          return (
            <IconButton
              aria-label={
                isExpanded
                  ? CUSTOMER_ORDERS_CONTENT.collapseLinesAriaLabel
                  : CUSTOMER_ORDERS_CONTENT.expandLinesAriaLabel
              }
              aria-expanded={isExpanded}
              onClick={() => toggleExpand(order.key)}
            >
              {isExpanded ? (
                <ChevronDown size={16} aria-hidden />
              ) : (
                <ChevronRight size={16} aria-hidden />
              )}
            </IconButton>
          );
        },
      },
      {
        key: "branch",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        sortable: true,
        sortValue: (order) => order.filial,
        render: (order) => formatOperationalUnitCode(order.filial),
      },
      {
        key: "order",
        header: "Pedido",
        sortable: true,
        sortValue: (order) => order.pedido,
        interactive: true,
        rowClick: "stop",
        render: (order) => {
          const href = orderHref(order);
          if (!href) return order.pedido || "—";
          return (
            <CommercialEntityLink
              href={href}
              title={orderLinkTitle(order.pedido)}
              className="cm-link-button"
              onNavigate={() => openOrderDetail(order)}
            >
              {order.pedido || "—"}
            </CommercialEntityLink>
          );
        },
      },
      {
        key: "customer-order",
        header: "Pedido do cliente",
        sortable: true,
        sortValue: (order) => order.pedidoCliente,
        render: (order) => order.pedidoCliente || "—",
      },
      {
        key: "status",
        header: "Situação",
        sortable: true,
        sortValue: (order) => orderSituationLabel(order.situacao),
        render: renderStatus,
      },
      {
        key: "lines",
        header: "Linhas",
        align: "right",
        sortable: true,
        sortValue: (order) => order.quantidadeLinhas,
        render: (order) => order.quantidadeLinhas.toLocaleString("pt-BR"),
      },
      {
        key: "overdue",
        header: "Maior atraso",
        align: "right",
        sortable: true,
        sortValue: (order) => order.maiorAtrasoDias,
        render: (order) => formatMaxOverdue(order.maiorAtrasoDias),
      },
      {
        key: "delivery",
        header: "Próxima entrega",
        sortable: true,
        sortValue: (order) => order.proximaEntrega,
        render: (order) =>
          order.proximaEntrega ? formatDisplayDate(order.proximaEntrega) : "—",
      },
      {
        key: "value",
        header: "Valor em aberto",
        align: "right",
        sortable: true,
        sortValue: (order) => order.valorTotalAberto,
        render: (order) => formatCurrency(order.valorTotalAberto),
      },
    ],
    [expandedRowKey, basePath, codigo, loja],
  );

  const sortedOrders = useMemo(
    () => sortTableRows(filteredOrders, columns, sortKey, sortDirection),
    [columns, filteredOrders, sortDirection, sortKey],
  );

  const handleSortChange = (columnKey: string) => {
    const next = nextTableSortState(sortKey, sortDirection, columnKey);
    setSortKey(next.sortKey as OrderSortKey);
    setSortDirection(next.sortDirection);
  };

  const sectionTitle = `${CUSTOMER_ORDERS_CONTENT.ordersSectionTitle} (${sortedOrders.length.toLocaleString("pt-BR")})`;

  return (
    <CommercialSectionCard title={sectionTitle}>
      <CommercialScopeChipBar
        aria-label={CUSTOMER_ORDERS_CONTENT.situationFilterAriaLabel}
        label={
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            {CUSTOMER_ORDERS_CONTENT.situationFilterLabel}
            <HelpTooltip
              content={CM_HELP.customerDetail.ordersSituationFilter}
              ariaLabel="Ajuda: filtro de situação"
            />
          </span>
        }
        chips={[
          {
            id: "all",
            label: `${CUSTOMER_ORDERS_CONTENT.situationAll} (${situationCounts.all.toLocaleString("pt-BR")})`,
            active: situationFilter === "all",
            onSelect: () => setSituationFilter("all"),
          },
          {
            id: "atrasado",
            label: `${CUSTOMER_ORDERS_CONTENT.situationLate} (${situationCounts.atrasado.toLocaleString("pt-BR")})`,
            active: situationFilter === "atrasado",
            onSelect: () => setSituationFilter("atrasado"),
          },
          {
            id: "parcial",
            label: `${CUSTOMER_ORDERS_CONTENT.situationPartial} (${situationCounts.parcial.toLocaleString("pt-BR")})`,
            active: situationFilter === "parcial",
            onSelect: () => setSituationFilter("parcial"),
          },
          {
            id: "em_aberto",
            label: `${CUSTOMER_ORDERS_CONTENT.situationOnTime} (${situationCounts.em_aberto.toLocaleString("pt-BR")})`,
            active: situationFilter === "em_aberto",
            onSelect: () => setSituationFilter("em_aberto"),
          },
        ]}
      />

      <CommercialFilterBarShell
        embedded
        layout="inline"
        ariaLabel={CUSTOMER_ORDERS_CONTENT.searchLabel}
      >
        <CommercialTextField
          label={CUSTOMER_ORDERS_CONTENT.searchLabel}
          hint={CM_HELP.customerDetail.ordersSearch}
          placeholder={CUSTOMER_ORDERS_CONTENT.searchPlaceholder}
          value={search}
          onChange={setSearch}
        />
      </CommercialFilterBarShell>

      {sortedOrders.length === 0 ? (
        <p className="cm-cell-muted" role="status">
          {CUSTOMER_ORDERS_CONTENT.emptyFiltered}
        </p>
      ) : null}

      <div className="cm-customer-orders__desktop">
        <CommercialDataTable
          rows={sortedOrders}
          columns={withColumnHelp(columns, CUSTOMER_ORDERS_COLUMN_HELP)}
          rowKey={(order) => order.key}
          layout="section"
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSortChange={handleSortChange}
          onRowClick={openOrderDetail}
          rowClickRole="button"
          expandedRowKey={expandedRowKey}
          onExpandedRowKeyChange={setExpandedRowKey}
          renderExpandedRow={(order) => (
            <CustomerOrderLines
              lines={order.lines}
              orderKey={order.key}
              basePath={basePath}
              canViewAnalytics={canViewAnalytics}
              returnNav={orderReturnNav}
            />
          )}
        />
      </div>

      <div
        className="cm-customer-orders__mobile"
        aria-label={CUSTOMER_ORDERS_CONTENT.mobileListAriaLabel}
      >
        {sortedOrders.map((order) => {
          const href = orderHref(order);
          return (
            <div
              key={order.key}
              className="cm-customer-orders__mobile-item cm-customer-orders__mobile-item--clickable"
              role="button"
              tabIndex={0}
              onClick={() => openOrderDetail(order)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  openOrderDetail(order);
                }
              }}
            >
              <CommercialDataRecordCard
                title={
                  href ? (
                    <CommercialEntityLink
                      href={href}
                      title={orderLinkTitle(order.pedido)}
                      className="cm-link-button"
                      onNavigate={() => openOrderDetail(order)}
                    >
                      {`Pedido ${order.pedido || "não informado"}`}
                    </CommercialEntityLink>
                  ) : (
                    `Pedido ${order.pedido || "não informado"}`
                  )
                }
                subtitle={formatOperationalUnitCode(order.filial, "Unidade não informada")}
                status={renderStatus(order)}
                fields={[
                  {
                    id: "customer-order",
                    label: "Pedido do cliente",
                    value: order.pedidoCliente || "—",
                  },
                  {
                    id: "lines",
                    label: "Linhas",
                    value: order.quantidadeLinhas.toLocaleString("pt-BR"),
                  },
                  {
                    id: "overdue",
                    label: "Maior atraso",
                    value: formatMaxOverdue(order.maiorAtrasoDias),
                  },
                  {
                    id: "delivery",
                    label: "Próxima entrega",
                    value: order.proximaEntrega
                      ? formatDisplayDate(order.proximaEntrega)
                      : "—",
                  },
                  {
                    id: "value",
                    label: "Valor em aberto",
                    value: formatCurrency(order.valorTotalAberto),
                  },
                ]}
              />
            </div>
          );
        })}
      </div>
    </CommercialSectionCard>
  );
}
