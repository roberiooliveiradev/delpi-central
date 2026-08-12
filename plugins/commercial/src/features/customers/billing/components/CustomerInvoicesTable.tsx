import type { DataTableColumn } from "@delpi/plugin-ui/index";
import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
} from "@delpi/plugin-ui/index";
import { useId, useState } from "react";

import {
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialDataTable,
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
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const baseId = useId();
  const toggle = (key: string) =>
    setExpandedKey((current) => (current === key ? null : key));
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
      render: (invoice) => {
        const expanded = expandedKey === invoice.key;
        const safe = invoice.key.replace(/\|/g, "-");
        return (
          <CommercialActionButton
            variant="ghost"
            aria-expanded={expanded}
            aria-controls={`${baseId}-desktop-nf-${safe}`}
            onClick={() => toggle(invoice.key)}
          >
            {expanded ? "Recolher itens" : "Expandir itens"}
          </CommercialActionButton>
        );
      },
    },
  ];
  const expandedInvoice =
    invoices.find((invoice) => invoice.key === expandedKey) ?? null;

  return (
    <CommercialSectionCard title="Notas fiscais">
      <div className="cm-customer-invoices__desktop">
        <CommercialDataTable
          rows={invoices}
          columns={columns}
          rowKey={(invoice) => invoice.key}
          layout="section"
        />
        {expandedInvoice ? (
          <div
            id={`${baseId}-desktop-nf-${expandedInvoice.key.replace(/\|/g, "-")}`}
            role="region"
            aria-label={`Itens da nota ${expandedInvoice.invoice_number}`}
          >
            {expandedInvoice.items.length > 0 ? (
              <CustomerInvoiceItems items={expandedInvoice.items} />
            ) : (
              <p className="cm-customer-invoices__empty">Sem itens nesta nota.</p>
            )}
          </div>
        ) : null}
      </div>
      <div className="cm-customer-invoices__mobile">
        {invoices.map((invoice) => {
          const expanded = expandedKey === invoice.key;
          const panelId = `${baseId}-mobile-nf-${invoice.key.replace(/\|/g, "-")}`;
          return (
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
                context={
                  <CommercialActionButton
                    variant="ghost"
                    aria-expanded={expanded}
                    aria-controls={panelId}
                    onClick={() => toggle(invoice.key)}
                  >
                    {expanded ? "Recolher itens" : "Expandir itens"}
                  </CommercialActionButton>
                }
              />
              {expanded ? (
                <div id={panelId} role="region" aria-label={`Itens da nota ${invoice.invoice_number}`}>
                  {invoice.items.length > 0 ? (
                    <CustomerInvoiceItems items={invoice.items} />
                  ) : (
                    <p className="cm-customer-invoices__empty">Sem itens nesta nota.</p>
                  )}
                </div>
              ) : null}
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
