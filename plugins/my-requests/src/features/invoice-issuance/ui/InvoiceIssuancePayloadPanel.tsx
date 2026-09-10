import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { DetailFields, MyRequestsSectionCard } from "../../../ui/mrUi";
import {
  freightModeLabel,
  invoiceTypeLabel,
} from "../domain/status";

type InvoiceIssuancePayloadPanelProps = {
  payload: Record<string, unknown>;
};

export function InvoiceIssuancePayloadPanel({ payload }: InvoiceIssuancePayloadPanelProps) {
  const items = Array.isArray(payload.items) ? payload.items : [];
  const invoiceType = String(payload.invoice_type || "");
  const freightMode = String(payload.freight_mode || "");
  return (
    <MyRequestsSectionCard
      title="Dados da emissão"
      hint={MY_REQUESTS_HELP_TOOLTIPS.detail.invoicePayload}
    >
      <div data-help="invoice-payload">
        <DetailFields
          fields={[
            {
              label: "Destinatário",
              hint: MY_REQUESTS_HELP_TOOLTIPS.detail.party,
              value: `${String(payload.party_name || "—")} (${String(payload.party_code || "")}/${String(payload.party_store || "")})`,
            },
            {
              label: "Tipo NF",
              hint: MY_REQUESTS_HELP_TOOLTIPS.detail.invoiceType,
              value: invoiceType ? invoiceTypeLabel(invoiceType) : "—",
            },
            {
              label: "Frete",
              hint: MY_REQUESTS_HELP_TOOLTIPS.detail.freight,
              value: freightMode ? freightModeLabel(freightMode) : "—",
            },
            {
              label: "Itens",
              hint: MY_REQUESTS_HELP_TOOLTIPS.detail.items,
              value: String(items.length),
            },
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
