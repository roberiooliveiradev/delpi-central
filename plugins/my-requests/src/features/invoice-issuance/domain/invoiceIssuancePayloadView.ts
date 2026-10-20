import { formatTaxId } from "./formatTaxId";
import {
  freightModeLabel,
  invoiceTypeLabel,
  partyTypeLabel,
} from "./status";

/**
 * Projeção somente de leitura do payload persistido de emissão de NF.
 *
 * Cobre os campos de negócio do wizard e os campos legados ainda gravados
 * na migração. Não reconstrói valores ausentes.
 *
 * `stock_write_off` na raiz é default do validador e não representa a escolha
 * por item. O flag por item só aparece quando a chave existe no item.
 * `checklist`, `_migration`, `id` e `line_number` não são dados do formulário.
 */
export type InvoicePayloadField = {
  id: string;
  label: string;
  value: string;
  wide?: boolean;
};

export type InvoicePayloadItemView = {
  id: string;
  title: string;
  fields: InvoicePayloadField[];
};

export type InvoiceIssuancePayloadView = {
  recipient: InvoicePayloadField[];
  invoice: InvoicePayloadField[];
  freight: InvoicePayloadField[];
  extras: InvoicePayloadField[];
  items: InvoicePayloadItemView[];
};

/** Chaves de negócio que esta projeção sabe apresentar quando preenchidas. */
export const INVOICE_PAYLOAD_DISPLAY_KEYS = {
  root: [
    "party_name",
    "party_type",
    "party_code",
    "party_store",
    "tax_id",
    "invoice_type",
    "invoice_type_other",
    "freight_mode",
    "carrier_code",
    "carrier_name",
    "carrier_legal_name",
    "carrier_tax_id",
    "carrier_address",
    "carrier_phone",
    "weight_kg",
    "volume_count",
    "purchase_order_number",
    "observation",
  ],
  item: [
    "product_code",
    "product_description",
    "quantity",
    "unit_price",
    "stock_write_off",
    "sales_order",
    "sales_order_item",
    "customer_order_number",
  ],
} as const;

/** Metadados persistidos que não são resposta do formulário. */
export const INVOICE_PAYLOAD_NON_FORM_KEYS = {
  root: ["stock_write_off", "checklist", "_migration", "items"],
  item: ["id", "line_number"],
} as const;

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

function filledText(value: unknown): string | null {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) return null;
    return formatExactDecimal(value);
  }
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed || null;
}

/** Mantém os dígitos persistidos. Troca só o separador decimal para pt-BR. */
function formatExactDecimal(value: number | string): string | null {
  const raw = typeof value === "number" ? String(value) : value.trim();
  if (!raw || raw.includes("e") || raw.includes("E")) return null;
  if (!/^-?\d+(\.\d+)?$/.test(raw)) return typeof value === "string" ? raw : null;
  return raw.replace(".", ",");
}

function moneyText(value: unknown): string | null {
  const exact = typeof value === "number" || typeof value === "string"
    ? formatExactDecimal(typeof value === "number" ? value : value.trim())
    : null;
  if (exact === null) return filledText(value);
  if (!/^-?\d+(,\d+)?$/.test(exact)) return exact;
  return `R$ ${exact}`;
}

function field(
  id: string,
  label: string,
  value: string | null,
  wide = false,
): InvoicePayloadField | null {
  if (value === null || value.trim() === "") return null;
  return wide ? { id, label, value, wide: true } : { id, label, value };
}

function push(target: InvoicePayloadField[], next: InvoicePayloadField | null) {
  if (next) target.push(next);
}

function hasOwn(record: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(record, key);
}

export function projectInvoiceIssuancePayload(
  payload: Record<string, unknown> | null | undefined,
): InvoiceIssuancePayloadView {
  const row = asRecord(payload) || {};
  const recipient: InvoicePayloadField[] = [];
  const invoice: InvoicePayloadField[] = [];
  const freight: InvoicePayloadField[] = [];
  const extras: InvoicePayloadField[] = [];

  push(recipient, field("recipient.name", "Nome", filledText(row.party_name)));
  const partyType = filledText(row.party_type);
  push(
    recipient,
    field(
      "recipient.partyType",
      "Tipo",
      partyType ? partyTypeLabel(partyType) : null,
    ),
  );
  const code = filledText(row.party_code);
  const store = filledText(row.party_store);
  const codeStore = [code, store].filter(Boolean).join(" / ");
  push(recipient, field("recipient.codeStore", "Código / loja", codeStore || null));
  push(
    recipient,
    field("recipient.taxId", "CPF/CNPJ", formatTaxId(filledText(row.tax_id)) || null),
  );

  const invoiceType = filledText(row.invoice_type);
  push(
    invoice,
    field(
      "invoice.type",
      "Tipo de nota fiscal",
      invoiceType ? invoiceTypeLabel(invoiceType) : null,
    ),
  );
  push(
    invoice,
    field(
      "invoice.typeOther",
      "Descrição do tipo",
      filledText(row.invoice_type_other),
      true,
    ),
  );

  const freightMode = filledText(row.freight_mode);
  push(
    freight,
    field(
      "freight.mode",
      "Frete",
      freightMode ? freightModeLabel(freightMode) : null,
    ),
  );
  const carrierCode = filledText(row.carrier_code);
  const carrierName = filledText(row.carrier_name);
  const carrier = [carrierCode, carrierName].filter(Boolean).join(" — ");
  push(freight, field("freight.carrier", "Transportadora", carrier || null));
  push(
    freight,
    field(
      "freight.carrierLegalName",
      "Razão social da transportadora",
      filledText(row.carrier_legal_name),
    ),
  );
  push(
    freight,
    field(
      "freight.carrierTaxId",
      "CPF/CNPJ da transportadora",
      formatTaxId(filledText(row.carrier_tax_id)) || null,
    ),
  );
  push(
    freight,
    field(
      "freight.carrierAddress",
      "Endereço da transportadora",
      filledText(row.carrier_address),
      true,
    ),
  );
  push(
    freight,
    field(
      "freight.carrierPhone",
      "Telefone da transportadora",
      filledText(row.carrier_phone),
    ),
  );

  push(extras, field("extras.weight", "Peso (kg)", decimalOrText(row.weight_kg)));
  push(extras, field("extras.volumes", "Volumes", decimalOrText(row.volume_count)));
  push(
    extras,
    field(
      "extras.purchaseOrder",
      "Pedido de compra",
      filledText(row.purchase_order_number),
    ),
  );
  push(
    extras,
    field("extras.observation", "Observação", filledText(row.observation), true),
  );

  const rawItems = Array.isArray(row.items) ? row.items : [];
  const items = rawItems.flatMap((raw, index) => {
    const item = asRecord(raw);
    if (!item) return [];
    return [projectItem(item, index)];
  }).filter((item) => item.fields.length > 0);

  return { recipient, invoice, freight, extras, items };
}

function decimalOrText(value: unknown): string | null {
  if (typeof value === "number" || typeof value === "string") {
    const exact = formatExactDecimal(typeof value === "number" ? value : value.trim());
    if (exact !== null) return exact;
  }
  return filledText(value);
}

function projectItem(
  item: Record<string, unknown>,
  index: number,
): InvoicePayloadItemView {
  const code = filledText(item.product_code);
  const line = typeof item.line_number === "number" && item.line_number > 0
    ? item.line_number
    : index + 1;
  const title = code ? `Item ${line} · ${code}` : `Item ${line}`;
  const fields: InvoicePayloadField[] = [];

  push(fields, field("item.productCode", "Código", code));
  push(
    fields,
    field("item.description", "Descrição", filledText(item.product_description), true),
  );
  push(fields, field("item.quantity", "Quantidade", decimalOrText(item.quantity)));
  push(fields, field("item.unitPrice", "Preço unitário", moneyText(item.unit_price)));

  const salesOrder = filledText(item.sales_order);
  const salesItem = filledText(item.sales_order_item);
  const sales = [salesOrder, salesItem].filter(Boolean).join(" / ");
  push(fields, field("item.salesOrder", "Pedido de venda", sales || null));
  push(
    fields,
    field(
      "item.customerOrder",
      "Pedido do cliente",
      filledText(item.customer_order_number),
    ),
  );

  if (hasOwn(item, "stock_write_off") && typeof item.stock_write_off === "boolean") {
    push(
      fields,
      field(
        "item.stockWriteOff",
        "Baixa de estoque",
        item.stock_write_off ? "Sim" : "Não",
      ),
    );
  }

  return {
    id: `item-${line}-${code || index}`,
    title,
    fields,
  };
}

export function invoicePayloadFieldIds(view: InvoiceIssuancePayloadView): string[] {
  return [
    ...view.recipient,
    ...view.invoice,
    ...view.freight,
    ...view.extras,
    ...view.items.flatMap((item) => item.fields),
  ].map((entry) => entry.id);
}
