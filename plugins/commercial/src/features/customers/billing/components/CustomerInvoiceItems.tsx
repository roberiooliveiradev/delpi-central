import type { DataTableColumn } from "@delpi/plugin-ui/index";

import {
  CommercialDataRecordCard,
  CommercialDataTable,
} from "../../../../app/commercialUi";
import {
  CUSTOMER_INVOICE_ITEM_COLUMN_HELP,
  withColumnHelp,
} from "../../../../utils/customersColumnHelp";
import { formatCurrency } from "../../../../utils/format";

type CustomerInvoiceItem = {
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
};

type CustomerInvoiceItemsProps = {
  items: readonly CustomerInvoiceItem[];
};

export function CustomerInvoiceItems({ items }: CustomerInvoiceItemsProps) {
  const rows = Array.from(items);
  const columns: DataTableColumn<CustomerInvoiceItem>[] = [
    { key: "item", header: "Item", render: (line) => line.item || "—" },
    { key: "product", header: "Produto", render: (line) => line.product_code || "—" },
    {
      key: "description",
      header: "Descrição",
      render: (line) => line.product_description || "—",
    },
    {
      key: "quantity",
      header: "Qtd",
      align: "right",
      render: (line) => line.quantity.toLocaleString("pt-BR"),
    },
    { key: "unit", header: "UM", render: (line) => line.unit || "—" },
    {
      key: "unit-price",
      header: "Unitário",
      align: "right",
      render: (line) => formatCurrency(line.unit_price),
    },
    {
      key: "total",
      header: "Total",
      align: "right",
      render: (line) => formatCurrency(line.total_value),
    },
    {
      key: "order",
      header: "Pedido",
      render: (line) =>
        `${line.sales_order || "—"}${line.customer_order ? ` · ${line.customer_order}` : ""}`,
    },
  ];
  const rowKey = (line: CustomerInvoiceItem) =>
    `${line.item}-${line.product_code}-${line.sales_order_item}`;

  return (
    <div className="cm-customer-invoice-items" role="region" aria-label="Itens da nota fiscal">
      <div className="cm-customer-invoice-items__desktop">
        <CommercialDataTable
          rows={rows}
          columns={withColumnHelp(columns, CUSTOMER_INVOICE_ITEM_COLUMN_HELP)}
          rowKey={rowKey}
          layout="section"
        />
      </div>
      <div className="cm-customer-invoice-items__mobile">
        {rows.map((line) => (
          <CommercialDataRecordCard
            key={rowKey(line)}
            title={line.product_code || "Produto não informado"}
            subtitle={line.product_description || "Sem descrição"}
            fields={[
              { id: "item", label: "Item", value: line.item || "—" },
              { id: "quantity", label: "Quantidade", value: `${line.quantity.toLocaleString("pt-BR")} ${line.unit || ""}`.trim() },
              { id: "unit-price", label: "Unitário", value: formatCurrency(line.unit_price) },
              { id: "total", label: "Total", value: formatCurrency(line.total_value) },
              {
                id: "order",
                label: "Pedido",
                value: `${line.sales_order || "—"}${line.customer_order ? ` · ${line.customer_order}` : ""}`,
              },
            ]}
          />
        ))}
      </div>
    </div>
  );
}
