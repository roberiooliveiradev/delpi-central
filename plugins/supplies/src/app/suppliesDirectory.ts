/**
 * Directory objects of Portal Suprimentos — color keys for entity avatars.
 * Canonical destinations live in `pluginRoutes.ts`
 * (`buildSupplierDetailPath`, `buildUserProfileHref`); the former reserved
 * `/people/:code` path was discarded in favor of `/users/:userId`.
 */
export function supplierColorKey(code?: string | null, store?: string | null): string {
  return [code, store].map((part) => String(part || "").trim()).filter(Boolean).join("|");
}

export function personColorKey(code?: string | null, protheusUserId?: string | null): string {
  return String(protheusUserId || code || "").trim();
}
