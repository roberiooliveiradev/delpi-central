import type { EntityDirectoryOption } from "@delpi/plugin-ui/index";

import type { Carrier, Party, ProductHit } from "./types";
import { formatTaxId } from "./formatTaxId";

export function partyEntityId(party: Pick<Party, "party_code" | "party_store">): string {
  return `${party.party_code}|${party.party_store}`;
}

function partySecondary(party: Party): string {
  const codeStore = `${party.party_code}/${party.party_store}`;
  const tax = formatTaxId(party.tax_id);
  return tax ? `${tax} · ${codeStore}` : codeStore;
}

export function partyToOption(party: Party): EntityDirectoryOption {
  return {
    id: partyEntityId(party),
    label: (party.party_name || "").trim() || party.party_code,
    secondary: partySecondary(party),
  };
}

export function productEntityId(product: Pick<ProductHit, "code">): string {
  return product.code;
}

export function productToOption(product: ProductHit): EntityDirectoryOption {
  return {
    id: productEntityId(product),
    label: (product.description || "").trim() || product.code,
    secondary: product.code,
  };
}

export function carrierEntityId(carrier: Pick<Carrier, "carrier_code">): string {
  return carrier.carrier_code;
}

function carrierSecondary(carrier: Carrier): string {
  const tax = formatTaxId(carrier.tax_id);
  return tax ? `${tax} · ${carrier.carrier_code}` : carrier.carrier_code;
}

export function carrierToOption(carrier: Carrier): EntityDirectoryOption {
  return {
    id: carrierEntityId(carrier),
    label: (carrier.carrier_name || "").trim() || carrier.carrier_code,
    secondary: carrierSecondary(carrier),
  };
}
