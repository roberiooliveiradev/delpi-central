import type { DelpiProductLookupItem } from "../api/delpiLookupApi";

export type DelpiProductLookupMeta = {
  code: string;
  description: string;
  customerReference: string;
};

export function toProductLookupMeta(item: DelpiProductLookupItem): DelpiProductLookupMeta {
  return {
    code: item.code,
    description: item.description,
    customerReference: item.customerReference ?? "",
  };
}

export function formatProductCodeOptionLabel(meta: DelpiProductLookupMeta): string {
  if (meta.description) {
    return `${meta.code} — ${meta.description}`;
  }
  return meta.code;
}

export function formatCustomerReferenceOptionLabel(meta: DelpiProductLookupMeta): string {
  const reference = meta.customerReference || meta.code;
  if (meta.description) {
    return `${reference} — ${meta.code} — ${meta.description}`;
  }
  return `${reference} — ${meta.code}`;
}

export function looksLikeDelpiProductCodeQuery(query: string): boolean {
  const trimmed = query.trim();
  if (!trimmed) return false;
  if (/^9026/i.test(trimmed)) return true;
  return /^[0-9A-Za-z./-]+$/.test(trimmed) && !/\s/.test(trimmed);
}
