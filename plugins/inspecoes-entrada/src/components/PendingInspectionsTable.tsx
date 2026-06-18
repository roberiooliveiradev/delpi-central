import type { InspecoesEntradaPendente } from "../types/inspecoesEntradaDashboard";
import { formatDatePt, formatNumber, formatText } from "../utils/format";

type PendingInspectionsTableProps = {
  items: InspecoesEntradaPendente[];
  loading: boolean;
  error: string | null;
  totalCount?: number;
};

function formatReceived(item: InspecoesEntradaPendente): string {
  const dateLabel = formatDatePt(item.received_date);
  if (dateLabel === "—") return "—";

  const time = item.received_time?.trim();
  return time ? `${dateLabel} ${time}` : dateLabel;
}

export function PendingInspectionsTable({
  items,
  loading,
  error,
  totalCount,
}: PendingInspectionsTableProps) {
  if (loading) {
    return <div className="ie-state-box ie-state-box--compact">Carregando pendências…</div>;
  }

  if (error) {
    return (
      <div className="ie-alert ie-alert--error" role="alert">
        <p>{error}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="ie-state-box ie-state-box--compact">
        Nenhuma inspeção pendente encontrada para esta filial.
      </div>
    );
  }

  const total = totalCount ?? items.length;
  const truncated = total > items.length;

  return (
    <>
      <p className="ie-pending-summary" aria-live="polite">
        {total.toLocaleString("pt-BR")} {total === 1 ? "pendência" : "pendências"} aguardando inspeção
      </p>

      <div className="ie-table-wrap ie-table-wrap--pending-scroll">
        <table className="ie-table ie-table--compact">
          <thead>
            <tr>
              <th>Recebimento</th>
              <th>NF</th>
              <th>Fornecedor</th>
              <th>Código</th>
              <th>Descrição</th>
              <th>Qtd</th>
              <th>UM</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={`${item.invoice_number}-${item.product_code}-${item.received_date}-${item.received_time}`}
              >
                <td className="ie-table__muted">{formatReceived(item)}</td>
                <td className="ie-cell-mono ie-table__highlight">{formatText(item.invoice_number)}</td>
                <td className="ie-table__highlight">{formatText(item.supplier_name)}</td>
                <td className="ie-cell-mono">{formatText(item.product_code)}</td>
                <td>{formatText(item.product_description)}</td>
                <td>{formatNumber(item.quantity)}</td>
                <td>{formatText(item.unit)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {truncated ? (
        <p className="ie-preview-hint">
          Exibindo {items.length.toLocaleString("pt-BR")} de {total.toLocaleString("pt-BR")} pendências.
        </p>
      ) : null}
    </>
  );
}
