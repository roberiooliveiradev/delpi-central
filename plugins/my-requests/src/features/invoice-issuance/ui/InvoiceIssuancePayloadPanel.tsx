import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { DetailFields, MyRequestsSectionCard } from "../../../ui/mrUi";
import {
  projectInvoiceIssuancePayload,
  type InvoicePayloadField,
} from "../domain/invoiceIssuancePayloadView";

type InvoiceIssuancePayloadPanelProps = {
  payload: Record<string, unknown>;
};

const HINTS: Record<string, string> = {
  "recipient.name": MY_REQUESTS_HELP_TOOLTIPS.detail.party,
  "recipient.partyType": MY_REQUESTS_HELP_TOOLTIPS.detail.partyType,
  "recipient.codeStore": MY_REQUESTS_HELP_TOOLTIPS.detail.party,
  "recipient.taxId": MY_REQUESTS_HELP_TOOLTIPS.detail.taxId,
  "invoice.type": MY_REQUESTS_HELP_TOOLTIPS.detail.invoiceType,
  "invoice.typeOther": MY_REQUESTS_HELP_TOOLTIPS.detail.invoiceTypeOther,
  "freight.mode": MY_REQUESTS_HELP_TOOLTIPS.detail.freight,
  "freight.carrier": MY_REQUESTS_HELP_TOOLTIPS.detail.carrier,
  "extras.weight": MY_REQUESTS_HELP_TOOLTIPS.detail.weight,
  "extras.volumes": MY_REQUESTS_HELP_TOOLTIPS.detail.volumes,
  "extras.observation": MY_REQUESTS_HELP_TOOLTIPS.detail.observation,
  "item.productCode": MY_REQUESTS_HELP_TOOLTIPS.detail.items,
  "item.description": MY_REQUESTS_HELP_TOOLTIPS.detail.productDescription,
  "item.quantity": MY_REQUESTS_HELP_TOOLTIPS.detail.items,
  "item.unitPrice": MY_REQUESTS_HELP_TOOLTIPS.detail.unitPrice,
  "item.salesOrder": MY_REQUESTS_HELP_TOOLTIPS.detail.salesOrder,
  "item.stockWriteOff": MY_REQUESTS_HELP_TOOLTIPS.detail.stockWriteOff,
};

function toDetailFields(fields: InvoicePayloadField[]) {
  return fields.map((entry) => ({
    label: entry.label,
    hint: HINTS[entry.id],
    value:
      entry.id === "extras.observation" ? (
        <span className="my-requests-invoice-payload__text">{entry.value}</span>
      ) : (
        entry.value
      ),
    wide: entry.wide,
  }));
}

export function InvoiceIssuancePayloadPanel({ payload }: InvoiceIssuancePayloadPanelProps) {
  const view = projectInvoiceIssuancePayload(payload);
  const sections = [
    {
      title: "Destinatário",
      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.party,
      fields: view.recipient,
    },
    {
      title: "Nota fiscal",
      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.invoiceType,
      fields: view.invoice,
    },
    {
      title: "Transporte",
      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.freight,
      fields: view.freight,
    },
    {
      title: "Informações adicionais",
      hint: MY_REQUESTS_HELP_TOOLTIPS.detail.invoicePayload,
      fields: view.extras,
    },
  ].filter((section) => section.fields.length > 0);

  if (!sections.length && view.items.length === 0) return null;

  return (
    <div className="my-requests-invoice-payload" data-help="invoice-payload">
      {sections.map((section) => (
        <MyRequestsSectionCard key={section.title} title={section.title} hint={section.hint}>
          <DetailFields fields={toDetailFields(section.fields)} />
        </MyRequestsSectionCard>
      ))}
      {view.items.length > 0 ? (
        <MyRequestsSectionCard
          title="Itens"
          hint={MY_REQUESTS_HELP_TOOLTIPS.detail.items}
        >
          {view.items.map((item) => (
            <div key={item.id} className="my-requests-invoice-item">
              <h3 className="my-requests-invoice-item__title">{item.title}</h3>
              <DetailFields fields={toDetailFields(item.fields)} />
            </div>
          ))}
        </MyRequestsSectionCard>
      ) : null}
    </div>
  );
}
