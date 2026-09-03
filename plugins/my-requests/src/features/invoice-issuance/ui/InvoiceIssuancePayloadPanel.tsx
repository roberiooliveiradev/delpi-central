import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { DetailFields, MyRequestsSectionCard } from "../../../ui/mrUi";

type InvoiceIssuancePayloadPanelProps = {
  payload: Record<string, unknown>;
};

export function InvoiceIssuancePayloadPanel({ payload }: InvoiceIssuancePayloadPanelProps) {
  const items = Array.isArray(payload.items) ? payload.items : [];
  return (
    <MyRequestsSectionCard title="Dados da emissão">
      <div data-help="invoice-payload" title={MY_REQUESTS_HELP_TOOLTIPS.detail.invoicePayload}>
        <DetailFields
          fields={[
            {
              label: "Destinatário",
              value: `${String(payload.party_name || "—")} (${String(payload.party_code || "")}/${String(payload.party_store || "")})`,
            },
            { label: "Tipo NF", value: String(payload.invoice_type || "—") },
            { label: "Frete", value: String(payload.freight_mode || "—") },
            { label: "Itens", value: String(items.length) },
          ]}
        />
        {items.length > 0 ? (
          <ul className="my-requests-domain-list">
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
        ) : null}
      </div>
    </MyRequestsSectionCard>
  );
}
