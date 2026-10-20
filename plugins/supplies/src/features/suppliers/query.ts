import type {
  SupplierCreateDraft,
  SupplierDetail,
  SupplierEditDraft,
  SupplierFieldSpec,
  SupplierWriteResponse,
  SuppliersQuery,
} from "./types";
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

/**
 * Mapeia um campo do registry para o valor retornado pelo GET detail da BFF.
 * Campos ausentes no payload retornam "" — nunca valor inventado.
 */
export function getSupplierFieldValue(
  detail: SupplierDetail,
  spec: SupplierFieldSpec,
): string {
  switch (spec.get) {
    case "identity":
      return (
        (spec.key === "supplier_code"
          ? detail.supplier_code
          : detail.supplier_store) ?? ""
      ).toString();
    case "top":
      return detail.tax_id
        ? formatTaxIdMasked(detail.tax_id, detail.tax_id_masked)
        : "";
    case "section":
      return (
        detail.sections[spec.section]?.[spec.key]?.toString() ?? ""
      );
  }
}

/** POST: envia somente campos preenchidos; preserva zeros à esquerda. */
export function buildCreateFornecedor(
  draft: SupplierCreateDraft,
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(draft)) {
    const trimmed = value.trim();
    if (trimmed) out[key] = trimmed;
  }
  if (out.state) out.state = out.state.toUpperCase();
  if (out.person_type) out.person_type = out.person_type.toUpperCase();
  if (out.rohs_indicator) out.rohs_indicator = out.rohs_indicator.toUpperCase();
  return out;
}

/** PUT parcial: somente campos efetivamente modificados entram no body. */
export function buildUpdateFornecedor(
  changes: ReadonlyArray<{ field: keyof SupplierEditDraft; after: string }>,
): Partial<SupplierEditDraft> {
  const out: Partial<SupplierEditDraft> = {};
  for (const change of changes) out[change.field] = change.after;
  return out;
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
