import { formatCurrency } from "../../../utils/format";
import { compareDeliveryDates, formatDisplayDate } from "../../../utils/dates";
import { PVA_TABLE } from "../../../ui/tableChrome";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";

type CustomerOpenOrdersPreviewProps = {
  orders: CustomerOrderSummary[];
  onSeeAll: () => void;
};

function previewStatus(order: CustomerOrderSummary): {
  label: string;
  tone: "danger" | "success" | "info";
} {
  if (order.situacao === "atrasado") return { label: "Vencido", tone: "danger" };
  if (order.situacao === "parcial") return { label: "Em produção", tone: "info" };
  return { label: "No prazo", tone: "success" };
}

function pickEmission(order: CustomerOrderSummary): string | null {
  let earliest: string | null = null;
  for (const line of order.lines) {
    const value = line.data_despacho;
    if (!value) continue;
    if (!earliest || compareDeliveryDates(value, earliest) < 0) {
      earliest = value;
    }
  }
  return earliest;
}

const PREVIEW_LIMIT = 5;

export function CustomerOpenOrdersPreview({
  orders,
  onSeeAll,
}: CustomerOpenOrdersPreviewProps) {
  const rows = orders.slice(0, PREVIEW_LIMIT);

  return (
    <section className="pva-card pva-orders-preview" aria-label="Pedidos em aberto">
      <div className="pva-orders-preview__header">
        <h2 className="pva-orders-preview__title">Pedidos em aberto</h2>
      </div>
      {rows.length === 0 ? (
        <p className="pva-orders-preview__empty">Nenhum pedido em aberto no momento.</p>
      ) : (
        <div className={PVA_TABLE.wrap}>
          <table className={PVA_TABLE.table}>
            <thead>
              <tr>
                <th scope="col">Pedido</th>
                <th scope="col">Emissão</th>
                <th scope="col">Previsão</th>
                <th scope="col" className={PVA_TABLE.colNumeric}>
                  Valor em aberto
                </th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((order) => {
                const status = previewStatus(order);
                return (
                  <tr key={order.key}>
                    <td data-label="Pedido">{order.pedido || "—"}</td>
                    <td data-label="Emissão">
                      {formatDisplayDate(pickEmission(order))}
                    </td>
                    <td data-label="Previsão">
                      {order.proximaEntrega
                        ? formatDisplayDate(order.proximaEntrega)
                        : "—"}
                    </td>
                    <td data-label="Valor em aberto" className={PVA_TABLE.colNumeric}>
                      {formatCurrency(order.valorTotalAberto)}
                    </td>
                    <td data-label="Status">
                      <span className={`pva-order-status pva-order-status--${status.tone}`}>
                        <span className="pva-order-status__dot" aria-hidden="true" />
                        {status.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <div className="pva-orders-preview__footer">
        <button type="button" className="pva-orders-preview__link" onClick={onSeeAll}>
          Ver todos os pedidos
          <span aria-hidden="true"> →</span>
        </button>
      </div>
    </section>
  );
}
