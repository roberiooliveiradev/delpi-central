import type { SupplierEditDraft, SupplierWriteResponse, SuppliersQuery } from "./types";
import { SUPPLIERS_PAGE_SIZE_OPTIONS } from "./types";

export function createDefaultQuery(): SuppliersQuery {
  return { query: "", state: "", blocked: "", page: 1, page_size: 20 };
}

export function parseQueryFromSearch(search: string): SuppliersQuery {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const defaults = createDefaultQuery();
  const page = Number.parseInt(params.get("page") ?? "", 10);
  const pageSize = Number.parseInt(params.get("page_size") ?? "", 10);
  const blocked = params.get("blocked") ?? "";
  return {
    query: (params.get("query") ?? "").slice(0, 120),
    state: (params.get("state") ?? "").toUpperCase().slice(0, 2),
    blocked: blocked === "0" || blocked === "1" ? blocked : "",
    page: Number.isFinite(page) && page > 0 ? page : defaults.page,
    page_size: (SUPPLIERS_PAGE_SIZE_OPTIONS as readonly number[]).includes(pageSize)
      ? pageSize
      : defaults.page_size,
  };
}

export function buildUrlSearch(query: SuppliersQuery): string {
  const params = new URLSearchParams();
  if (query.query.trim()) params.set("query", query.query.trim());
  if (query.state) params.set("state", query.state);
  if (query.blocked) params.set("blocked", query.blocked);
  if (query.page > 1) params.set("page", String(query.page));
  if (query.page_size !== 20) params.set("page_size", String(query.page_size));
  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}

export function hasActiveFilters(query: SuppliersQuery): boolean {
  return Boolean(query.query.trim() || query.state || query.blocked);
}

export function formatTaxIdMasked(value: string | null, masked: boolean): string {
  if (!value) return "—";
  if (masked) return "••••••";
  const digits = value.replace(/\D/g, "");
  if (digits.length === 14) {
    return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`;
  }
  if (digits.length === 11) {
    return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`;
  }
  return value;
}

/** Campos alterados entre o valor atual e o rascunho (PUT allowlist). */
export function diffEditableFields(
  current: { supplier_name?: string | number | null; supplier_short_name?: string | number | null },
  draft: SupplierEditDraft,
): Array<{ field: "supplier_name" | "supplier_short_name"; before: string; after: string }> {
  const out: Array<{ field: "supplier_name" | "supplier_short_name"; before: string; after: string }> = [];
  const name = (current.supplier_name ?? "").toString().trim();
  const shortName = (current.supplier_short_name ?? "").toString().trim();
  if (draft.supplier_name.trim() !== name) {
    out.push({ field: "supplier_name", before: name, after: draft.supplier_name.trim() });
  }
  if (draft.supplier_short_name.trim() !== shortName) {
    out.push({
      field: "supplier_short_name",
      before: shortName,
      after: draft.supplier_short_name.trim(),
    });
  }
  return out;
}

/**
 * Classifica o resultado de escrita: acknowledged≠persistido. Persistência só
 * é confirmada quando o backend comprova (`persistence_proven`).
 */
export function classifyWriteOutcome(
  response: SupplierWriteResponse | undefined,
  statusCode?: number,
): "rejected" | "acknowledged" | "persistence_confirmed" | "indeterminate" | "write_disabled" {
  if (response?.outcome) return response.outcome;
  if (response?.code && response.code.endsWith("_DISABLED")) return "write_disabled";
  if (statusCode && statusCode >= 400 && statusCode < 500) return "rejected";
  if (response?.persistence_proven) return "persistence_confirmed";
  if (response?.acknowledged) return "acknowledged";
  return "indeterminate";
}
