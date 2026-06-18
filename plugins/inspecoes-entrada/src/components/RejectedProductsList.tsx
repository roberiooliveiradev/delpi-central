import type { InspecoesEntradaRejeitadaProduto } from "../types/inspecoesEntradaDashboard";
import { formatDateTimePt, formatNumber, formatText } from "../utils/format";

type RejectedProductsListProps = {
  items: InspecoesEntradaRejeitadaProduto[];
  loading: boolean;
  error: string | null;
  total?: number;
};

function formatProductLabel(item: InspecoesEntradaRejeitadaProduto): string {
  const code = item.product_code?.trim();
  const description = item.product_description?.trim();

  if (code && description) {
    return `${code} — ${description}`;
  }

  return formatText(code || description);
}

export function RejectedProductsList({
  items,
  loading,
  error,
  total,
}: RejectedProductsListProps) {
  if (loading) {
    return <div className="ie-state-box ie-state-box--compact">Carregando rejeições…</div>;
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
      <div className="ie-state-box ie-state-box--compact ie-state-box--positive">
        Nenhuma rejeição registrada para esta filial.
      </div>
    );
  }

  const totalCount = total ?? items.length;
  const truncated = totalCount > items.length;

  return (
    <>
      {truncated ? (
        <p className="ie-rejected-summary">
          Exibindo {items.length.toLocaleString("pt-BR")} de{" "}
          {totalCount.toLocaleString("pt-BR")} rejeições recentes.
        </p>
      ) : null}

      <ul className="ie-rejected-list">
        {items.map((item) => (
          <li key={item.inspection_id} className="ie-rejected-list__item">
            <div className="ie-rejected-list__main">
              <p className="ie-rejected-list__product">{formatProductLabel(item)}</p>
              <p className="ie-rejected-list__supplier">{formatText(item.supplier_name)}</p>
              <p className="ie-rejected-list__meta">
                NF {formatText(item.invoice_number)}
                {item.lot?.trim() ? ` · Lote ${formatText(item.lot)}` : ""}
                {item.quantity ? ` · ${formatNumber(item.quantity)} ${formatText(item.unit)}` : ""}
              </p>
            </div>
            <time className="ie-rejected-list__date" dateTime={item.report_date ?? undefined}>
              {formatDateTimePt(item.report_date, item.report_time)}
            </time>
          </li>
        ))}
      </ul>
    </>
  );
}
