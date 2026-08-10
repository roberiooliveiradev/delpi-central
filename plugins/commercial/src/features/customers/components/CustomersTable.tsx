import type { CSSProperties, MouseEvent } from "react";
import { useState } from "react";
import { HelpTooltip, SegmentToggle } from "@delpi/plugin-ui/index";

import {
  CommercialDataCellValue,
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialExcelExportButton,
  CommercialSelectField,
  CommercialStatusBadge,
  CommercialTableColumnVisibilityMenu,
  UI_PREFIX,
  type DataTableColumn,
} from "../../../app/commercialUi";
import {
  buildCustomerDetailPath,
  navigateCustomerDetail,
} from "../../../app/pluginNavigation";
import { TableFontSizeControls } from "../../../components/TableFontSizeControls";
import { CM_HELP } from "../../../content/helpTooltips";
import { useTableFontSize } from "../../../hooks/useTableFontSize";
import type { CustomersListSellerAccess } from "../../../utils/customersListDeepLink";
import { formatDisplayDate } from "../../../utils/dates";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { formatCurrency } from "../../../utils/format";
import { useCustomerTablePreferences } from "../hooks/useCustomerTablePreferences";
import { useCustomersListLayout } from "../hooks/useCustomersListLayout";
import type {
  CustomerListSortDirection,
  CustomerListSortKey,
  CustomerSummary,
} from "../types/customerSummary";
import { hasCustomerEnrichmentCoverage } from "../utils/customerEnrichmentCoverage";
import {
  resolveCustomerStatus,
  statusLabel,
} from "../utils/customerListPresentation";
import type { CustomerColumnDef, CustomerColumnKey } from "../utils/customerTableColumns";
import { CUSTOMER_COLUMN_CATALOG } from "../utils/customerTableColumns";
import { exportCustomersExcel } from "../utils/exportCustomersExcel";
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

const SORTABLE_COLUMN_KEYS = new Set<CustomerColumnKey>(
  CUSTOMER_COLUMN_CATALOG.map((column) => column.key),
);

const SORT_OPTIONS = CUSTOMER_COLUMN_CATALOG.filter((column) =>
  SORTABLE_COLUMN_KEYS.has(column.key),
).map((column) => ({
  value: column.key,
  label: column.label,
}));

function statusVariant(
  status: ReturnType<typeof resolveCustomerStatus>,
): "success" | "warning" | "neutral" {
  if (status === "ativo") return "success";
  if (status === "atencao") return "warning";
  return "neutral";
}

function isSortableCustomerColumnKey(
  key: string,
): key is Exclude<CustomerListSortKey, "attention"> {
  return SORTABLE_COLUMN_KEYS.has(key as CustomerColumnKey);
}

function customerIdentity(customer: CustomerSummary): {
  name: string;
  codeStore: string;
} {
  const codeStore =
    formatEntityCodeStore(customer.codigo, customer.loja) ??
    `${customer.codigo}-${customer.loja}`;
  return {
    name: customer.nome?.trim() || "—",
    codeStore,
  };
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
  const { layout, setLayout } = useCustomersListLayout();
  const {
    fontSize,
    increase,
    decrease,
    reset: resetFontSize,
    canIncrease,
    canDecrease,
    isDefault,
  } = useTableFontSize();
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

  const visibleColumnCount = orderedColumns.filter(
    (column) => visibility[column.key],
  ).length;

  const tableStyle = {
    "--cm-table-font-size": `${fontSize}px`,
    "--delpi-ui-table-font-size": `${fontSize}px`,
  } as CSSProperties;

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
    event: MouseEvent<HTMLElement>,
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
        const { name, codeStore } = customerIdentity(customer);
        return (
          <div className="cm-open-orders-client">
            <CustomerAvatar
              code={customer.codigo}
              store={customer.loja}
              name={name}
              hasAvatar={Boolean(customer.hasAvatar)}
              size="sm"
            />
            <div className="cm-open-orders-client__text">
              <button
                type="button"
                className="cm-open-orders-client__name"
                onClick={(event) => handleExplicitNavigate(event, customer)}
              >
                {name}
              </button>
              <span className="cm-open-orders-client__id">{codeStore}</span>
            </div>
          </div>
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
      <div className="cm-table-toolbar" style={tableStyle}>
        <div className="cm-table-toolbar__leading">
          <div className="cm-table-toolbar__layout">
            <HelpTooltip
              content={CM_HELP.customers.layoutToggle}
              ariaLabel="Ajuda: modo Tabela ou Cards"
              wrap
              placement="bottom"
            >
              <SegmentToggle
                prefix={UI_PREFIX}
                size="sm"
                ariaLabel="Modo de visualização"
                idPrefix="customers-layout"
                value={layout}
                onChange={setLayout}
                options={[
                  { value: "table", label: "Tabela" },
                  { value: "cards", label: "Cards" },
                ]}
              />
            </HelpTooltip>
          </div>
          <p className="cm-table-toolbar__hint">
            <HelpTooltip
              content={CM_HELP.customers.list}
              ariaLabel="Ajuda: tabela da carteira"
              wrap
              placement="bottom"
            >
              <span className="delpi-ui-section-hint-label">
                {visibleColumnCount} coluna(s) ·{" "}
                {exportRows.length.toLocaleString("pt-BR")} linha(s)
              </span>
            </HelpTooltip>
          </p>
        </div>
        <div className="cm-table-toolbar__actions">
          <CommercialExcelExportButton
            onExport={() => void handleExportExcel()}
            disabled={exportRows.length === 0 || exporting || loading}
            exporting={exporting}
          />
          <TableFontSizeControls
            fontSize={fontSize}
            onIncrease={increase}
            onDecrease={decrease}
            onReset={resetFontSize}
            canIncrease={canIncrease}
            canDecrease={canDecrease}
            isDefault={isDefault}
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
      </div>

      {layout === "cards" ? (
        <div className="cm-open-orders-cards-toolbar" style={tableStyle}>
          <CommercialSelectField
            id="customers-sort"
            label="Ordenar por"
            hint={CM_HELP.customers.sortBy}
            value={isSortableCustomerColumnKey(sortKey) ? sortKey : "nome"}
            options={SORT_OPTIONS}
            onChange={(value) => {
              if (isSortableCustomerColumnKey(value)) onSort(value);
            }}
          />
          <div className="cm-open-orders-cards-toolbar__dir">
            <HelpTooltip
              content={CM_HELP.customers.sortDirection}
              ariaLabel="Ajuda: direção da ordenação"
              wrap
              placement="bottom"
            >
              <SegmentToggle
                prefix={UI_PREFIX}
                size="sm"
                ariaLabel="Direção da ordenação"
                idPrefix="customers-sort-dir"
                value={sortDirection}
                onChange={(dir) => {
                  if (dir !== sortDirection && isSortableCustomerColumnKey(sortKey)) {
                    onSort(sortKey);
                  }
                }}
                options={[
                  { value: "asc", label: "Crescente" },
                  { value: "desc", label: "Decrescente" },
                ]}
              />
            </HelpTooltip>
          </div>
        </div>
      ) : null}

      {layout === "table" ? (
        <div className="cm-customers-list__table" style={tableStyle}>
          <CommercialDataTable
            rows={customers}
            columns={visibleColumns}
            rowKey={(customer) => customer.key}
            layout="section"
            loading={loading}
            emptyMessage={emptyMessage}
            sortKey={sortKey}
            sortDirection={sortDirection}
            onSortChange={(key) => {
              if (isSortableCustomerColumnKey(key)) onSort(key);
            }}
            onRowClick={openCustomer}
            rowClickRole="button"
            columnWidths={widths}
            onColumnWidthsChange={setWidths}
            resizableColumns
            enableColumnReorder
            onColumnOrderChange={applyVisibleOrder}
          />
        </div>
      ) : (
        <div
          className="cm-customers-list__cards"
          style={tableStyle}
          aria-label="Clientes da carteira"
        >
          {customers.length === 0 ? (
            <p className="cm-customers-list__cards-empty">{emptyMessage}</p>
          ) : (
            customers.map((customer) => {
              const status = customer.status ?? resolveCustomerStatus(customer);
              const { name, codeStore } = customerIdentity(customer);
              return (
                <CommercialDataRecordCard
                  key={customer.key}
                  leading={
                    <CustomerAvatar
                      code={customer.codigo}
                      store={customer.loja}
                      name={name}
                      hasAvatar={Boolean(customer.hasAvatar)}
                      size="sm"
                    />
                  }
                  title={name}
                  subtitle={codeStore}
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
                  ariaLabel={`Abrir cliente ${name === "—" ? codeStore : name}`}
                />
              );
            })
          )}
        </div>
      )}
    </>
  );
}
