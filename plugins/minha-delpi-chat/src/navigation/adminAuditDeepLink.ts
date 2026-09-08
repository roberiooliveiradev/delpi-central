/**
 * Deep link bolha → Auditoria filtrada por traceId.
 */

import { buildAdminHref } from "./adminNavigation";
import {
  DEFAULT_ADMIN_AUDIT_URL_FILTERS,
  serializeAuditFiltersToQuery,
} from "./adminUrlQuery";

export function buildAdminAuditHrefWithTrace(traceId: string | null | undefined): string {
  const base = buildAdminHref({ section: "governance", subTab: "audit" });
  const normalized = (traceId ?? "").trim();

  if (!normalized) {
    return base;
  }

  const query = serializeAuditFiltersToQuery({
    ...DEFAULT_ADMIN_AUDIT_URL_FILTERS,
    traceId: normalized,
  });

  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value) {
      params.set(key, value);
    }
  }

  const search = params.toString();
  return search ? `${base}?${search}` : base;
}
