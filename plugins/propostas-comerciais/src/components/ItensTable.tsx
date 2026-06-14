import type { PropostaComercialItem } from "../types/propostasComerciais";
import { displayValue } from "../utils/format";

type ItensTableProps = {
  items: PropostaComercialItem[];
};

export function ItensTable({ items }: ItensTableProps) {
  return (
    <div className="pc-table-wrap">
      <table className="pc-table pc-table--items">
        <thead>
          <tr>
            <th>Item</th>
            <th>Produto</th>
            <th>Descrição</th>
            <th>Ref. cliente</th>
            <th>NCM</th>
            <th>Qtd.</th>
            <th>Preço R$/mil</th>
            <th>Total R$/mil</th>
            <th>Prazo</th>
            <th>Lote mín.</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.item}>
              <td data-label="Item">{displayValue(item.item)}</td>
              <td data-label="Produto">{displayValue(item.produto)}</td>
              <td data-label="Descrição">{displayValue(item.descricao)}</td>
              <td data-label="Ref. cliente">{displayValue(item.referencia_cliente)}</td>
              <td data-label="NCM">{displayValue(item.ncm)}</td>
              <td data-label="Qtd.">
                {item.quantidade.toLocaleString("pt-BR")} {item.unidade}
              </td>
              <td data-label="Preço R$/mil">{displayValue(item.preco_unitario)}</td>
              <td data-label="Total R$/mil">{displayValue(item.valor_total)}</td>
              <td data-label="Prazo">{displayValue(item.prazo_dias)}</td>
              <td data-label="Lote mín.">{displayValue(item.lote_minimo)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
