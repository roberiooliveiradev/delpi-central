import { normalizeBasePath } from "./pluginRoutes";

/**
 * Directory objects of Portal Suprimentos.
 *
 * TARGET pages (not routed yet). Aligns with the product queue:
 * - `/apps/supplies/suppliers/:code/:store` — supplier 360 (TOTVS A2)
 * - `/apps/supplies/people/:code` — person (requester / buyer)
 *
 * Avatars use plugin-ui EntityAvatarLabel today. When those pages land,
 * add href + title on EntityAvatarLabel; do not invent a destination before.
 */
export const SUPPLIES_SUPPLIER_COLLECTION_PATH = "suppliers";
export const SUPPLIES_PERSON_COLLECTION_PATH = "people";

export function reservedSupplierDetailPath(
  code: string,
  store?: string | null,
  basePath?: string,
): string {
  const base = normalizeBasePath(basePath);
  const slug = encodeURIComponent(code.trim());
  const path = `${base}/${SUPPLIES_SUPPLIER_COLLECTION_PATH}/${slug}`;
  const loja = (store || "").trim();
  return loja ? `${path}/${encodeURIComponent(loja)}` : path;
}

export function reservedPersonDetailPath(code: string, basePath?: string): string {
  const base = normalizeBasePath(basePath);
  return `${base}/${SUPPLIES_PERSON_COLLECTION_PATH}/${encodeURIComponent(code.trim())}`;
}

export function supplierColorKey(code?: string | null, store?: string | null): string {
  return [code, store].map((part) => String(part || "").trim()).filter(Boolean).join("|");
}

export function personColorKey(code?: string | null, protheusUserId?: string | null): string {
  return String(protheusUserId || code || "").trim();
}
