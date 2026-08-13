import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { useState } from "react";

import {
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialHostDialog,
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../../app/commercialUi";
import { formatCurrency } from "../../../../utils/format";
import { formatDisplayDate } from "../../../../utils/dates";
import type { CustomerInvoice } from "../types/customerBilling";
import { situationLabel } from "../utils/billingPeriod";
import { CustomerInvoiceItems } from "./CustomerInvoiceItems";

type CustomerInvoicesTableProps = {
  invoices: CustomerInvoice[];
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function CustomerInvoicesTable({
  invoices,
  page,
  totalPages,
  total,
  onPageChange,
}: CustomerInvoicesTableProps) {
  const [itemsInvoiceKey, setItemsInvoiceKey] = useState<string | null>(null);
  const itemsInvoice =
    invoices.find((invoice) => invoice.key === itemsInvoiceKey) ?? null;

  const invoiceActions = (invoice: CustomerInvoice) => (
    <CommercialActionButton
      variant="ghost"
      onClick={() => setItemsInvoiceKey(invoice.key)}
    >
      Ver itens
    </CommercialActionButton>
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
      render: (invoice) =>
        `${invoice.invoice_number}${invoice.invoice_series ? ` / ${invoice.invoice_series}` : ""}${
          invoice.branch
            ? ` · ${OPERATIONAL_UNIT_COLUMN_LABEL} ${formatOperationalUnitCode(invoice.branch)}`
            : ""
        }`,
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
    {
      key: "details",
      header: "Detalhes",
      render: (invoice) => invoiceActions(invoice),
    },
  ];

  return (
    <CommercialSectionCard title="Notas fiscais">
      <div className="cm-customer-invoices__desktop">
        <CommercialDataTable
          rows={invoices}
          columns={columns}
          rowKey={(invoice) => invoice.key}
          layout="section"
        />
      </div>
      <div className="cm-customer-invoices__mobile">
        {invoices.map((invoice) => (
          <div key={invoice.key} className="cm-customer-invoices__mobile-item">
            <CommercialDataRecordCard
              title={`Nota ${invoice.invoice_number}${
                invoice.invoice_series ? ` / ${invoice.invoice_series}` : ""
              }`}
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
              context={invoiceActions(invoice)}
            />
          </div>
        ))}
      </div>

      <CommercialHostDialog
        open={Boolean(itemsInvoice)}
        title={
          itemsInvoice
            ? `Itens da nota ${itemsInvoice.invoice_number}${
                itemsInvoice.invoice_series ? ` / ${itemsInvoice.invoice_series}` : ""
              }`
            : "Itens da nota"
        }
        description={
          itemsInvoice
            ? `Emissão ${formatDisplayDate(itemsInvoice.issue_date)}`
            : undefined
        }
        onClose={() => setItemsInvoiceKey(null)}
        footer={
          <CommercialActionButton variant="ghost" onClick={() => setItemsInvoiceKey(null)}>
            Fechar
          </CommercialActionButton>
        }
      >
        {itemsInvoice ? (
          itemsInvoice.items.length > 0 ? (
            <CustomerInvoiceItems items={itemsInvoice.items} />
          ) : (
            <p className="cm-customer-invoices__empty">Sem itens nesta nota.</p>
          )
        ) : null}
      </CommercialHostDialog>

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
