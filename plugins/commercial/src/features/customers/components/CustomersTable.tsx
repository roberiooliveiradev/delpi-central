import { useState, type MouseEvent } from "react";

import {
  CommercialDataCellValue,
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialExcelExportButton,
  CommercialStatusBadge,
  CommercialTableColumnVisibilityMenu,
  type DataTableColumn,
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
import { useCustomerTablePreferences } from "../hooks/useCustomerTablePreferences";
import { exportCustomersExcel } from "../utils/exportCustomersExcel";
import { hasCustomerEnrichmentCoverage } from "../utils/customerEnrichmentCoverage";
import type { CustomerColumnDef } from "../utils/customerTableColumns";
import {
  resolveCustomerStatus,
  statusLabel,
} from "../utils/customerListPresentation";
import { CM_HELP } from "../../../content/helpTooltips";
import { BillingTrendCell } from "./BillingTrendCell";
import { CustomerAvatar } from "./CustomerAvatar";

type CustomersTableProps = {
  customers: CustomerSummary[];
  exportRows: CustomerSummary[];
  canUseTeamScope: boolean;
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
  exportRows,
  canUseTeamScope,
  sortKey,
  sortDirection,
  onSort,
  basePath,
  listSearch,
  sellerAccess,
  loading = false,
  emptyMessage = "Nenhum cliente corresponde aos filtros selecionados.",
}: CustomersTableProps) {
  const [exporting, setExporting] = useState(false);
  const {
    visibility,
    orderedColumns,
    filterColumns,
    widths,
    setWidths,
    setColumnVisible,
    reorderColumns,
    applyVisibleOrder,
    reset,
  } = useCustomerTablePreferences(canUseTeamScope);

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
        render: (customer) => (
          <CommercialDataCellValue
            value={
              customer.city || customer.state
                ? [customer.city, customer.state].filter(Boolean).join(" / ")
                : null
            }
            present={hasCustomerEnrichmentCoverage(customer)}
          />
        ),
      },
      {
        key: "lastPurchaseDate",
        header: "Última venda",
        sortable: true,
        render: (customer) => (
          <CommercialDataCellValue
            value={
              customer.lastPurchaseDate
                ? formatDisplayDate(customer.lastPurchaseDate)
                : null
            }
            present={hasCustomerEnrichmentCoverage(customer)}
          />
        ),
      },
      {
        key: "billed12m",
        header: "Fat. 12 meses",
        sortable: true,
        align: "right",
        render: (customer) => (
          <CommercialDataCellValue
            value={customer.billed12m == null ? null : formatCurrency(customer.billed12m)}
            present={hasCustomerEnrichmentCoverage(customer)}
          />
        ),
      },
      {
        key: "billingTrend",
        header: "Tendência",
        headerHint: CM_HELP.customers.trend,
        sortable: true,
        render: (customer) => (
          <BillingTrendCell
            trend={customer.billingTrend}
            pct={customer.billingTrendPct}
            covered={hasCustomerEnrichmentCoverage(customer)}
          />
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
  const visibleColumns = filterColumns(columns).filter(
    (column): column is DataTableColumn<CustomerSummary> => Boolean(column),
  );
  const visibleExportColumns = filterColumns(
    orderedColumns,
  ) as CustomerColumnDef[];

  const handleExportExcel = async () => {
    if (exportRows.length === 0 || exporting) return;
    try {
      setExporting(true);
      await exportCustomersExcel(exportRows, visibleExportColumns);
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      <div className="cm-customers-list__desktop">
        <div className="cm-customers-list__toolbar">
          <CommercialExcelExportButton
            onExport={() => void handleExportExcel()}
            disabled={exportRows.length === 0 || exporting || loading}
            exporting={exporting}
          />
          <CommercialTableColumnVisibilityMenu
            columns={orderedColumns}
            visibility={visibility}
            onToggleColumn={setColumnVisible}
            onReset={reset}
            onReorderColumns={reorderColumns}
            labels={{
              trigger: "Colunas",
              panelTitle: "Colunas da carteira",
              reset: "Restaurar padrão",
              hint: CM_HELP.customers.tableColumns,
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
          columnWidths={widths}
          onColumnWidthsChange={setWidths}
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
                  value: (
                    <CommercialDataCellValue
                      value={
                        customer.lastPurchaseDate
                          ? formatDisplayDate(customer.lastPurchaseDate)
                          : null
                      }
                      present={hasCustomerEnrichmentCoverage(customer)}
                    />
                  ),
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
