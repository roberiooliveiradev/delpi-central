import type {
  Carrier,
  FreightMode,
  InvoiceType,
  IssuanceItem,
  Party,
  PartyType,
} from "../domain/types";

export type InvoiceWizardPrefill = {
  partyType: PartyType;
  party: Party | null;
  invoiceType: InvoiceType;
  invoiceTypeOther: string;
  items: IssuanceItem[];
  freightMode: FreightMode;
  carrier: Carrier | null;
  weightKg: string;
  volumeCount: string;
  observation: string;
};

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

/** Map API invoice-issuance payload into wizard state. */
export function prefillInvoiceWizardFromPayload(
  payload: Record<string, unknown> | null | undefined,
): InvoiceWizardPrefill {
  const row = payload || {};
  const partyType = (asString(row.party_type, "customer") as PartyType) || "customer";
  const partyCode = asString(row.party_code);
  const party: Party | null = partyCode
    ? {
        party_type: partyType,
        party_code: partyCode,
        party_store: asString(row.party_store) || "",
        party_name: asString(row.party_name) || partyCode,
        tax_id: asString(row.tax_id) || null,
        blocked: false,
      }
    : null;

  const invoiceType = (asString(row.invoice_type, "sale") as InvoiceType) || "sale";
  const freightMode = (asString(row.freight_mode, "cif") as FreightMode) || "cif";
  const carrierCode = asString(row.carrier_code);
  const carrier: Carrier | null = carrierCode
    ? {
        carrier_code: carrierCode,
        carrier_name: asString(row.carrier_name) || carrierCode,
        legal_name: null,
        tax_id: null,
        blocked: false,
      }
    : null;

  const rawItems = Array.isArray(row.items) ? row.items : [];
  const items: IssuanceItem[] = rawItems.map((raw, index) => {
    const item = (raw || {}) as Record<string, unknown>;
    return {
      id: `prefill-${index}-${asString(item.product_code, "item")}`,
      product_code: asString(item.product_code),
      product_description: asString(item.product_description),
      quantity: asNumber(item.quantity, 1),
      unit_price: asNumber(item.unit_price, 0),
      stock_write_off: Boolean(item.stock_write_off),
      sales_order: asString(item.sales_order) || null,
      sales_order_item: asString(item.sales_order_item) || null,
    };
  });

  return {
    partyType,
    party,
    invoiceType,
    invoiceTypeOther: asString(row.invoice_type_other),
    items,
    freightMode,
    carrier,
    weightKg: String(asNumber(row.weight_kg, 1) || 1),
    volumeCount: String(asNumber(row.volume_count, 1) || 1),
    observation: asString(row.observation),
  };
}

export function buildInvoiceIssuancePayload(input: {
  party: Party;
  invoiceType: InvoiceType;
  invoiceTypeOther: string;
  freightMode: FreightMode;
  carrier: Carrier | null;
  weightKg: string;
  volumeCount: string;
  observation: string;
  items: IssuanceItem[];
}): Record<string, unknown> {
  return {
    party_type: input.party.party_type,
    party_code: input.party.party_code,
    party_store: input.party.party_store,
    party_name: input.party.party_name,
    tax_id: input.party.tax_id,
    invoice_type: input.invoiceType,
    invoice_type_other: input.invoiceType === "other" ? input.invoiceTypeOther : null,
    freight_mode: input.freightMode,
    carrier_code: input.carrier?.carrier_code || null,
    carrier_name: input.carrier?.carrier_name || null,
    weight_kg: Number(input.weightKg),
    volume_count: Number(input.volumeCount),
    observation: input.observation || null,
    items: input.items.map((item) => ({
      product_code: item.product_code,
      product_description: item.product_description,
      quantity: item.quantity,
      unit_price: item.unit_price,
      stock_write_off: item.stock_write_off,
      sales_order: item.sales_order || null,
      sales_order_item: item.sales_order_item || null,
    })),
  };
}
