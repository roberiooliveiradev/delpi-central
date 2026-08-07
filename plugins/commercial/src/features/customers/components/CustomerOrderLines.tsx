import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate, getDeliveryOverdueDays, isDeliveryOverdue } from "../../../utils/dates";
import type { OpenOrdersTotvsItem } from "../../../types/openOrdersTotvs";
import { toFiniteNumber } from "../utils/customerAggregation";

type CustomerOrderLinesProps = {
  lines: readonly OpenOrdersTotvsItem[];
  orderKey: string;
};

function lineOverdueLabel(item: OpenOrdersTotvsItem): string {
  const saldo = toFiniteNumber(item.saldo);
  if (!isDeliveryOverdue(item.data_entrega, saldo)) return "Em dia";
  const days = getDeliveryOverdueDays(item.data_entrega) ?? 0;
  if (days <= 0) return "Atrasado";
  if (days === 1) return "Atrasado (1 dia)";
  return `Atrasado (${days.toLocaleString("pt-BR")} dias)`;
}

export function CustomerOrderLines({ lines, orderKey }: CustomerOrderLinesProps) {
  const regionId = `pva-order-lines-${orderKey.replace(/\|/g, "-")}`;

  return (
    <div
      id={regionId}
      className="pva-checkup-lines"
      role="region"
      aria-label="Linhas do pedido"
    >
      <table className="pva-checkup-lines__table">
        <thead>
          <tr>
            <th scope="col">Produto</th>
            <th scope="col" className="pva-col-numeric">
              Pedida
            </th>
            <th scope="col" className="pva-col-numeric">
              Entregue
            </th>
            <th scope="col" className="pva-col-numeric">
              Saldo
            </th>
            <th scope="col">Entrega</th>
            <th scope="col" className="pva-col-numeric">
              Valor aberto
            </th>
            <th scope="col">Atraso</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line, index) => {
            const rowKey = `${orderKey}-${line.linha ?? index}-${line.produto ?? ""}`;
            return (
              <tr key={rowKey}>
                <td data-label="Produto">{line.produto?.trim() || "—"}</td>
                <td data-label="Pedida" className="pva-col-numeric">
                  {toFiniteNumber(line.quantidade).toLocaleString("pt-BR")}
                </td>
                <td data-label="Entregue" className="pva-col-numeric">
                  {toFiniteNumber(line.entregue).toLocaleString("pt-BR")}
                </td>
                <td data-label="Saldo" className="pva-col-numeric">
                  {toFiniteNumber(line.saldo).toLocaleString("pt-BR")}
                </td>
                <td data-label="Entrega">{formatDisplayDate(line.data_entrega)}</td>
                <td data-label="Valor aberto" className="pva-col-numeric">
                  {formatCurrency(toFiniteNumber(line.valor_aberto))}
                </td>
                <td data-label="Atraso">{lineOverdueLabel(line)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
