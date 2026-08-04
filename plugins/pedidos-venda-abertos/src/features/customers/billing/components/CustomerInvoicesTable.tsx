import { Fragment, useId, useState } from "react";

import { formatCurrency } from "../../../../utils/format";
import { formatDisplayDate } from "../../../../utils/dates";
import { StatusBadge } from "../../../../ui/StatusBadge";
import { PVA_TABLE } from "../../../../ui/tableChrome";
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

  return (
    <section className="pva-table-card" aria-label="Notas fiscais de saída">
      <h2 className="pva-checkup-section-title">Notas fiscais</h2>
      <div className={PVA_TABLE.wrap}>
        <table className={PVA_TABLE.sortableTable}>
          <thead>
            <tr>
              <th scope="col">Emissão</th>
              <th scope="col">Nota / série</th>
              <th scope="col">Pedido de venda</th>
              <th scope="col">Pedido do cliente</th>
              <th scope="col">Situação</th>
              <th scope="col" className={PVA_TABLE.colNumeric}>
                Itens
              </th>
              <th scope="col" className={PVA_TABLE.colNumeric}>
                Valor
              </th>
              <th scope="col">Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((invoice) => {
              const expanded = expandedKey === invoice.key;
              const safe = invoice.key.replace(/\|/g, "-");
              const panelId = `${baseId}-nf-${safe}`;
              const controlId = `${baseId}-toggle-${safe}`;
              return (
                <Fragment key={invoice.key}>
                  <tr>
                    <td data-label="Emissão">{formatDisplayDate(invoice.issue_date)}</td>
                    <td data-label="Nota / série">
                      {invoice.invoice_number}
                      {invoice.invoice_series ? ` / ${invoice.invoice_series}` : ""}
                      {invoice.branch ? ` · Filial ${invoice.branch}` : ""}
                    </td>
                    <td data-label="Pedido de venda">{invoice.sales_order || "—"}</td>
                    <td data-label="Pedido do cliente">{invoice.customer_order || "—"}</td>
                    <td data-label="Situação">
                      <StatusBadge tone={invoice.situation === "return" ? "info" : "success"}>
                        {situationLabel(invoice.situation)}
                      </StatusBadge>
                    </td>
                    <td data-label="Itens" className={PVA_TABLE.colNumeric}>
                      {invoice.item_count.toLocaleString("pt-BR")}
                    </td>
                    <td data-label="Valor" className={PVA_TABLE.colNumeric}>
                      {formatCurrency(invoice.total_value)}
                    </td>
                    <td data-label="Detalhes">
                      <button
                        type="button"
                        id={controlId}
                        className="pva-btn pva-btn--secondary pva-btn--sm pva-checkup-expand"
                        aria-expanded={expanded}
                        aria-controls={panelId}
                        onClick={() =>
                          setExpandedKey((current) =>
                            current === invoice.key ? null : invoice.key,
                          )
                        }
                      >
                        {expanded ? "Recolher itens" : "Expandir itens"}
                      </button>
                    </td>
                  </tr>
                  {expanded ? (
                    <tr className="pva-checkup-detail-row">
                      <td colSpan={8}>
                        <div id={panelId} role="region" aria-labelledby={controlId}>
                          {invoice.items.length > 0 ? (
                            <CustomerInvoiceItems items={invoice.items} />
                          ) : (
                            <p className="pva-attention__empty">Sem itens nesta nota.</p>
                          )}
                        </div>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 ? (
        <div className="pva-billing-pagination" role="navigation" aria-label="Paginação de notas">
          <button
            type="button"
            className="pva-btn pva-btn--ghost"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Anterior
          </button>
          <span aria-live="polite">
            Página {page.toLocaleString("pt-BR")} de {totalPages.toLocaleString("pt-BR")} (
            {total.toLocaleString("pt-BR")} notas)
          </span>
          <button
            type="button"
            className="pva-btn pva-btn--ghost"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Próxima
          </button>
        </div>
      ) : null}
    </section>
  );
}
