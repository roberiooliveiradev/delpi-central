import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialEntityLink,
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../../app/commercialUi";
import { currentLocationAsReturnTo } from "../../../../app/commercialNavigationReturn";
import {
  buildCustomerInvoiceDetailHref,
  navigateCustomerInvoiceDetail,
} from "../../../../app/pluginNavigation";
import { invoiceLinkTitle } from "../../../../content/entityLinkHints";
import {
  CUSTOMER_INVOICE_COLUMN_HELP,
  withColumnHelp,
} from "../../../../utils/customersColumnHelp";
import { formatCurrency } from "../../../../utils/format";
import { formatDisplayDate } from "../../../../utils/dates";
import type { CustomerInvoice } from "../types/customerBilling";
import { situationLabel } from "../utils/billingPeriod";

type CustomerInvoicesTableProps = {
  invoices: CustomerInvoice[];
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
  basePath: string;
  codigo: string;
  loja: string;
};

export function CustomerInvoicesTable({
  invoices,
  page,
  totalPages,
  total,
  onPageChange,
  basePath,
  codigo,
  loja,
}: CustomerInvoicesTableProps) {
  const invoiceReturnNav = {
    returnTo: currentLocationAsReturnTo(),
    returnLabel: "Histórico",
  };

  const openInvoiceDetail = (invoice: CustomerInvoice) => {
    if (
      !invoice.branch?.trim() ||
      !invoice.invoice_number?.trim() ||
      !invoice.invoice_series?.trim()
    ) {
      return;
    }
    navigateCustomerInvoiceDetail(
      codigo,
      loja,
      invoice.branch,
      invoice.invoice_number,
      invoice.invoice_series,
      {
        basePath,
        returnNav: invoiceReturnNav,
      },
    );
  };

  const invoiceHref = (invoice: CustomerInvoice) =>
    buildCustomerInvoiceDetailHref(
      codigo,
      loja,
      invoice.branch,
      invoice.invoice_number,
      invoice.invoice_series,
      {
        basePath,
        returnNav: invoiceReturnNav,
      },
    );

  const columns: DataTableColumn<CustomerInvoice>[] = [
    {
      key: "issue",
      header: "Emissão",
      render: (invoice) => formatDisplayDate(invoice.issue_date),
    },
    {
      key: "invoice",
      header: "Nota / série",
      interactive: true,
      rowClick: "stop",
      render: (invoice) => {
        const label = `${invoice.invoice_number}${
          invoice.invoice_series ? ` / ${invoice.invoice_series}` : ""
        }${
          invoice.branch
            ? ` · ${OPERATIONAL_UNIT_COLUMN_LABEL} ${formatOperationalUnitCode(invoice.branch)}`
            : ""
        }`;
        const href = invoiceHref(invoice);
        if (!href) return label;
        return (
          <CommercialEntityLink
            href={href}
            title={invoiceLinkTitle(invoice.invoice_number)}
            className="cm-link-button"
            onNavigate={() => openInvoiceDetail(invoice)}
          >
            {label}
          </CommercialEntityLink>
        );
      },
    },
    {
      key: "sales-order",
      header: "Pedido de venda",
      render: (invoice) => invoice.sales_order || "—",
    },
    {
      key: "customer-order",
      header: "Pedido do cliente",
      render: (invoice) => invoice.customer_order || "—",
    },
    {
      key: "situation",
      header: "Situação",
      render: (invoice) => (
        <CommercialStatusBadge
          variant={invoice.situation === "return" ? "info" : "success"}
          label={situationLabel(invoice.situation)}
        />
      ),
    },
    {
      key: "items",
      header: "Itens",
      align: "right",
      render: (invoice) => invoice.item_count.toLocaleString("pt-BR"),
    },
    {
      key: "value",
      header: "Valor",
      align: "right",
      render: (invoice) => formatCurrency(invoice.total_value),
    },
  ];

  return (
    <CommercialSectionCard title="Notas fiscais">
      <div className="cm-customer-invoices__desktop">
        <CommercialDataTable
          rows={invoices}
          columns={withColumnHelp(columns, CUSTOMER_INVOICE_COLUMN_HELP)}
          rowKey={(invoice) => invoice.key}
          layout="section"
          onRowClick={openInvoiceDetail}
          rowClickRole="button"
        />
      </div>
      <div className="cm-customer-invoices__mobile">
        {invoices.map((invoice) => {
          const href = invoiceHref(invoice);
          const titleLabel = `Nota ${invoice.invoice_number}${
            invoice.invoice_series ? ` / ${invoice.invoice_series}` : ""
          }`;
          return (
            <div
              key={invoice.key}
              className="cm-customer-invoices__mobile-item cm-customer-orders__mobile-item--clickable"
              role="button"
              tabIndex={0}
              onClick={() => openInvoiceDetail(invoice)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  openInvoiceDetail(invoice);
                }
              }}
            >
              <CommercialDataRecordCard
                title={
                  href ? (
                    <CommercialEntityLink
                      href={href}
                      title={invoiceLinkTitle(invoice.invoice_number)}
                      className="cm-link-button"
                      onNavigate={() => openInvoiceDetail(invoice)}
                    >
                      {titleLabel}
                    </CommercialEntityLink>
                  ) : (
                    titleLabel
                  )
                }
                subtitle={`Emissão ${formatDisplayDate(invoice.issue_date)}`}
                status={
                  <CommercialStatusBadge
                    variant={invoice.situation === "return" ? "info" : "success"}
                    label={situationLabel(invoice.situation)}
                  />
                }
                fields={[
                  { id: "sales-order", label: "Pedido de venda", value: invoice.sales_order || "—" },
                  { id: "customer-order", label: "Pedido do cliente", value: invoice.customer_order || "—" },
                  { id: "items", label: "Itens", value: invoice.item_count.toLocaleString("pt-BR") },
                  { id: "value", label: "Valor", value: formatCurrency(invoice.total_value) },
                ]}
              />
            </div>
          );
        })}
      </div>

      {totalPages > 1 ? (
        <div className="cm-customer-billing-pagination" role="navigation" aria-label="Paginação de notas">
          <CommercialActionButton
            variant="ghost"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Anterior
          </CommercialActionButton>
          <span aria-live="polite">
            Página {page.toLocaleString("pt-BR")} de {totalPages.toLocaleString("pt-BR")} (
            {total.toLocaleString("pt-BR")} notas)
          </span>
          <CommercialActionButton
            variant="ghost"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Próxima
          </CommercialActionButton>
        </div>
      ) : null}
    </CommercialSectionCard>
  );
}
