import { formatCurrency } from "../../../../utils/format";

type CustomerInvoiceItemsProps = {
  items: readonly {
    item: string;
    product_code: string;
    product_description: string;
    quantity: number;
    unit: string;
    unit_price: number;
    total_value: number;
    sales_order: string;
    sales_order_item: string;
    customer_order: string;
  }[];
};

export function CustomerInvoiceItems({ items }: CustomerInvoiceItemsProps) {
  return (
    <div className="pva-checkup-lines" role="region" aria-label="Itens da nota fiscal">
      <table className="pva-checkup-lines__table">
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col">Produto</th>
            <th scope="col">Descrição</th>
            <th scope="col" className="pva-col-numeric">
              Qtd
            </th>
            <th scope="col">UM</th>
            <th scope="col" className="pva-col-numeric">
              Unitário
            </th>
            <th scope="col" className="pva-col-numeric">
              Total
            </th>
            <th scope="col">Pedido</th>
          </tr>
        </thead>
        <tbody>
          {items.map((line) => (
            <tr key={`${line.item}-${line.product_code}-${line.sales_order_item}`}>
              <td data-label="Item">{line.item || "—"}</td>
              <td data-label="Produto">{line.product_code || "—"}</td>
              <td data-label="Descrição">{line.product_description || "—"}</td>
              <td data-label="Qtd" className="pva-col-numeric">
                {line.quantity.toLocaleString("pt-BR")}
              </td>
              <td data-label="UM">{line.unit || "—"}</td>
              <td data-label="Unitário" className="pva-col-numeric">
                {formatCurrency(line.unit_price)}
              </td>
              <td data-label="Total" className="pva-col-numeric">
                {formatCurrency(line.total_value)}
              </td>
              <td data-label="Pedido">
                {line.sales_order || "—"}
                {line.customer_order ? ` · ${line.customer_order}` : ""}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
