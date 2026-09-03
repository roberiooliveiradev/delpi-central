import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";

type InvoiceIssuancePayloadPanelProps = {
  payload: Record<string, unknown>;
};

export function InvoiceIssuancePayloadPanel({ payload }: InvoiceIssuancePayloadPanelProps) {
  const items = Array.isArray(payload.items) ? payload.items : [];
  return (
    <section
      className="dashboard-my-requests__panel"
      data-help="invoice-payload"
      title={MY_REQUESTS_HELP_TOOLTIPS.detail.invoicePayload}
    >
      <h2>Dados da emissão</h2>
      <dl className="dashboard-my-requests__meta">
        <div>
          <dt>Destinatário</dt>
          <dd>
            {String(payload.party_name || "—")} ({String(payload.party_code || "")}/
            {String(payload.party_store || "")})
          </dd>
        </div>
        <div>
          <dt>Tipo NF</dt>
          <dd>{String(payload.invoice_type || "—")}</dd>
        </div>
        <div>
          <dt>Frete</dt>
          <dd>{String(payload.freight_mode || "—")}</dd>
        </div>
        <div>
          <dt>Itens</dt>
          <dd>{items.length}</dd>
        </div>
      </dl>
      <ul className="dashboard-my-requests__list">
        {items.map((raw, index) => {
          const item = raw as Record<string, unknown>;
          return (
            <li key={`${String(item.product_code)}-${index}`}>
              {String(item.product_code)} — qtd {String(item.quantity)} ×{" "}
              {String(item.unit_price)}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
