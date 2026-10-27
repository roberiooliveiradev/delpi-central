import type {
  SupplierCreateDraft,
  SupplierDetail,
  SupplierEditDraft,
  SupplierEditableFieldKey,
  SupplierFieldError,
  SupplierFieldSpec,
  SupplierWriteResponse,
  SuppliersQuery,
} from "./types";
import {
  catalogDisplayText,
  catalogLabelOf,
} from "./supplierCatalogs";
import {
  SUPPLIER_FIELD_REGISTRY,
  SUPPLIER_PERSON_TYPE_LABELS,
  SUPPLIERS_PAGE_SIZE_OPTIONS,
  type SupplierDetailSectionKey,
} from "./types";

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

/**
 * Indica se o GET detail retornou o campo — distingue "não informado"
 * (chave presente, valor vazio) de "indisponível na consulta" (chave ausente
 * no payload upstream).
 */
export function isSupplierFieldAvailable(
  detail: SupplierDetail,
  spec: SupplierFieldSpec,
): boolean {
  switch (spec.get) {
    case "identity":
      return true;
    case "top":
      return detail.tax_id !== null || detail.tax_id_masked;
    case "section": {
      const section = detail.sections[spec.section];
      return section ? spec.key in section : false;
    }
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

export type SupplierFieldChange = {
  field: SupplierEditableFieldKey;
  before: string;
  after: string;
};

/**
 * Campos alterados entre o valor atual (GET) e o rascunho — somente campos
 * com `put === "editable"` entram no diff; readonly/protected nunca são
 * comparados nem enviados.
 */
export function diffEditableFields(
  detail: SupplierDetail,
  draft: SupplierEditDraft,
): SupplierFieldChange[] {
  const out: SupplierFieldChange[] = [];
  for (const spec of SUPPLIER_FIELD_REGISTRY) {
    if (spec.put !== "editable") continue;
    const key = spec.key as SupplierEditableFieldKey;
    const before = getSupplierFieldValue(detail, spec).trim();
    const after = (draft[key] ?? "").trim();
    if (after !== before) out.push({ field: key, before, after });
  }
  return out;
}

/** Rótulo curto de tipo de pessoa para exibição (header/chips); "" se ausente. */
export function personTypeLabel(value: string | null | undefined): string {
  if (!value) return "";
  return SUPPLIER_PERSON_TYPE_LABELS[value.trim().toUpperCase()] ?? "";
}

/** Classe utilitária do item de grid: span declarado no spec + estado visual. */
export function supplierFieldItemClass(
  spec: SupplierFieldSpec,
  options?: { changed?: boolean; invalid?: boolean },
): string {
  const span = Math.min(Math.max(spec.span, 1), 12);
  return [
    "sp-supplier-field",
    `sp-supplier-field--span-${span}`,
    options?.changed ? "sp-supplier-field--changed" : "",
    options?.invalid ? "sp-supplier-field--invalid" : "",
  ]
    .filter(Boolean)
    .join(" ");
}

/**
 * Texto de exibição de um valor de campo com catálogo — "descrição · código"
 * quando o rótulo já foi resolvido (cache), senão o código original.
 */
export function supplierCatalogValueText(
  spec: SupplierFieldSpec | undefined,
  value: string,
): string {
  const trimmed = value.trim();
  if (!spec?.catalog || !trimmed) return value;
  const label = catalogLabelOf(spec.catalog, trimmed);
  return catalogDisplayText(trimmed, label);
}

/** Agrupa alterações por seção do registry, preservando a ordem canônica. */
export type SupplierChangeSection = {
  section: SupplierDetailSectionKey;
  changes: SupplierFieldChange[];
};

export function groupChangesBySection(
  changes: ReadonlyArray<SupplierFieldChange>,
): SupplierChangeSection[] {
  const order: SupplierDetailSectionKey[] = [
    "identification",
    "address",
    "contact",
    "fiscal",
    "purchasing",
  ];
  const sections = new Map<SupplierDetailSectionKey, SupplierFieldChange[]>();
  for (const change of changes) {
    const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === change.field);
    const section = spec?.section ?? "identification";
    sections.set(section, [...(sections.get(section) ?? []), change]);
  }
  return order
    .filter((id) => sections.has(id))
    .map((id) => ({ section: id, changes: sections.get(id)! }));
}

/** Monta o draft de edição a partir do GET detail (registry-driven). */
export function draftFromDetail(detail: SupplierDetail): SupplierEditDraft {
  const draft = {} as SupplierEditDraft;
  for (const spec of SUPPLIER_FIELD_REGISTRY) {
    if (spec.put !== "editable") continue;
    draft[spec.key as SupplierEditableFieldKey] = getSupplierFieldValue(
      detail,
      spec,
    );
  }
  return draft;
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

/* ------------------------------------------------------------------ */
/* X4.PROD-C1.R6 — validação local pré-submit do cadastro              */
/* ------------------------------------------------------------------ */

/** Mensagem PT-BR por campo obrigatório ausente (seleção × preenchimento). */
export function supplierRequiredFieldMessage(spec: SupplierFieldSpec): string {
  if (spec.requiredMessage) return spec.requiredMessage;
  if (spec.catalog || spec.options) {
    return `Selecione ${spec.label.toLowerCase()}.`;
  }
  return `Informe ${spec.label.toLowerCase()}.`;
}

/**
 * Agrega TODOS os erros de preenchimento do draft antes do envio — o
 * backend permanece autoritativo; aqui é só a verificação antecipada de UX.
 * Retorna a lista na ordem canônica do registry (vazia quando válido).
 */
export function validateCreateDraft(
  draft: SupplierCreateDraft,
): SupplierFieldError[] {
  const errors: SupplierFieldError[] = [];
  for (const spec of SUPPLIER_FIELD_REGISTRY) {
    if (!spec.post || !spec.required) continue;
    const value = (
      draft[spec.key as keyof SupplierCreateDraft] ?? ""
    ).trim();
    if (!value) {
      errors.push({
        field: spec.key,
        message: supplierRequiredFieldMessage(spec),
        code: "missing_required",
      });
    }
  }
  const store = draft.supplier_store.trim();
  if (store && !/^\d{2}$/.test(store)) {
    const spec = SUPPLIER_FIELD_REGISTRY.find(
      (entry) => entry.key === "supplier_store",
    );
    errors.push({
      field: "supplier_store",
      message: spec?.requiredMessage ?? "Informe a loja com 2 dígitos.",
      code: "invalid_format",
    });
  }
  return errors;
}

/**
 * Códigos de erro do backend que indicam falha de autenticação na
 * integração — o usuário não deve tratá-los como erro de preenchimento.
 */
const INTEGRATION_AUTH_ERROR_CODES = new Set([
  "PROTHEUS_TOKEN_INVALID",
  "PROTHEUS_AUTH_FAILED",
  "PROTHEUS_IDENTITY_UNMAPPED",
  "PROTHEUS_IDENTITY_AMBIGUOUS",
  "PROTHEUS_IDENTITY_NOT_VERIFIED",
]);

export function isIntegrationAuthErrorCode(code?: string): boolean {
  return Boolean(code) && INTEGRATION_AUTH_ERROR_CODES.has(code!);
}
