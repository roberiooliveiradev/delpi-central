import { II_SHEET } from "../../content/helpTooltips";
import { buildIssuanceSheet, type IssuanceSheetField } from "../../domain/issuanceSheet";
import type { IssuanceRequest } from "../../domain/types";
import { formatMoney, formatQuantity, formatTaxId, itemTotal } from "../format";
import { CopyableValue } from "./CopyableValue";

type Props = {
  request: IssuanceRequest;
};

function displayValue(field: IssuanceSheetField): string {
  if (!field.value) return "";
  if (field.format === "taxId") return formatTaxId(field.value);
  if (field.format === "quantity") return formatQuantity(Number(field.value));
  return field.value;
}

function fieldNode(field: IssuanceSheetField) {
  const text = displayValue(field) || "—";
  if (field.copyable && field.value) {
    return (
      <CopyableValue value={field.copyValue ?? field.value} label={field.label}>
        {text}
      </CopyableValue>
    );
  }
  return text;
}

export function IssuanceProtheusSheet({ request }: Props) {
  const sections = buildIssuanceSheet(request);
  const total = request.items.reduce(
    (sum, item) => sum + itemTotal(item.quantity, item.unit_price),
    0,
  );
  return (
    <article className="ii-ticket" data-testid="issuance-sheet">
      {sections.map((section) => (
        <section key={section.id} className="ii-ticket__block">
          <h2>{section.title}</h2>
          <dl className="ii-ticket__list">
            {section.fields.map((field) => (
              <div
                key={field.label}
                className={field.wide ? "ii-ticket__row ii-ticket__row--wide" : "ii-ticket__row"}
              >
                <dt>{field.label}</dt>
                <dd>{fieldNode(field)}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
      <section className="ii-ticket__block">
        <h2>{II_SHEET.items}</h2>
        <table className="ii-table ii-table--compact">
          <thead>
            <tr>
              <th>Produto</th>
              <th>Descrição</th>
              <th>Pedido</th>
              <th>Item</th>
              <th className="ii-cell-num">Qtd</th>
              <th className="ii-cell-num">Valor unit.</th>
              <th>Baixa</th>
              <th className="ii-cell-num">Total</th>
            </tr>
          </thead>
          <tbody>
            {request.items.map((item, index) => (
              <tr key={`${item.product_code}-${item.line_number ?? index}`}>
                <td>
                  <CopyableValue value={item.product_code} label="Produto">
                    {item.product_code}
                  </CopyableValue>
                </td>
                <td>{item.product_description}</td>
                <td>
                  {item.sales_order ? (
                    <CopyableValue value={item.sales_order} label="Pedido">
                      {item.sales_order}
                    </CopyableValue>
                  ) : (
                    "—"
                  )}
                </td>
                <td>{item.sales_order_item || "—"}</td>
                <td className="ii-cell-num">{formatQuantity(item.quantity)}</td>
                <td className="ii-cell-num">{formatMoney(item.unit_price)}</td>
                <td>{item.stock_write_off ? "Sim" : "Não"}</td>
                <td className="ii-cell-num ii-cell-strong">
                  {formatMoney(itemTotal(item.quantity, item.unit_price))}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={7} className="ii-cell-strong">
                Total
              </td>
              <td className="ii-cell-num ii-cell-strong">{formatMoney(total)}</td>
            </tr>
          </tfoot>
        </table>
      </section>
    </article>
  );
}
