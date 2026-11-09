/** Diagnóstico tipado de verificação oficial — PRC-REF-020-UX-01.
 * Deriva resumo/contagens/observações a partir de `field_results` do
 * backend. Nunca recalcula match. */

import type { PrcFieldResult, PrcVerification } from "./api/productRegistrationApi";
import { PRC_FIELD_LABELS, PRC_SUPPLIER_LABELS, prcFieldLabel } from "./prcCopy";

export type DiagnosisKind =
  | "field"
  | "supplier_attribute"
  | "supplier_link"
  | "infra";

export type DiagnosisItem = {
  id: string;
  kind: DiagnosisKind;
  /** Path SB1 (ex.: description) ou `suppliers`. */
  path?: string;
  supplierCode?: string;
  store?: string;
  attribute?: string;
  operation?: string;
  result: string;
  reasonCode?: string | null;
  previous?: unknown;
  expected?: unknown;
  observed?: unknown;
  isProblem: boolean;
  observation: string;
  label: string;
};

export type DiagnosisSummary = {
  verificationId?: string | null;
  officialCode?: string | null;
  checkedAt?: string | null;
  globalResult?: string | null;
  isInfra: boolean;
  totalChecks: number;
  matched: number;
  problems: number;
  mismatched: number;
  unverifiable: number;
  items: DiagnosisItem[];
  problemItems: DiagnosisItem[];
};

const INFRA_RESULTS = new Set([
  "timeout",
  "unavailable",
  "forbidden",
  "contract_error",
  "not_found",
]);

const PROBLEM_RESULTS = new Set([
  "mismatched",
  "unverifiable",
  "missing_in_official",
  "still_present_official",
  "ambiguous_official",
  "official_links_incomplete",
]);

export function isInfraVerificationResult(result: string | null | undefined): boolean {
  return Boolean(result && INFRA_RESULTS.has(result));
}

export function formatDiagnosticValue(value: unknown): string {
  if (value === null || value === undefined) return "Não retornado pela fonte oficial";
  if (value === "") return "Vazio (oficialmente verificado)";
  if (Array.isArray(value)) return `${value.length} item(ns)`;
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function fieldObservation(
  path: string,
  result: string,
  reasonCode: string | null | undefined,
  expected: unknown,
  observed: unknown,
): string {
  if (result === "unverifiable" || reasonCode === "field_absent" || reasonCode === "contract_gap") {
    return "Não foi possível confirmar este atributo na fonte oficial. A conclusão permanece bloqueada.";
  }
  if (result === "mismatched") {
    if (observed === "" && expected !== "") {
      return (
        "O cadastro oficial retornou valor vazio para este campo, diferente do valor solicitado. " +
        "Confirme o valor correto e ajuste a ficha ou solicite a alteração manual do cadastro oficial, conforme autorização."
      );
    }
    if (expected === "" && observed !== "" && observed != null) {
      return (
        "A ficha solicita valor vazio, mas o cadastro oficial possui um valor preenchido. " +
        "Confirme o valor correto antes de ajustar."
      );
    }
    const byPath: Record<string, string> = {
      description:
        "A descrição solicitada é diferente da descrição encontrada no TOTVS. Confirme o valor correto e ajuste a ficha ou solicite a alteração manual do cadastro oficial, conforme autorização.",
      group:
        "O grupo de classificação do produto não corresponde ao solicitado. Confirme o valor correto antes de realizar ajustes.",
      productKind:
        "O tipo de produto cadastrado não corresponde ao solicitado. Confirme a classificação correta.",
      unit:
        "A unidade de medida cadastrada é diferente da solicitada. Confirme a unidade correta antes de realizar ajustes.",
      defaultWarehouse:
        "O armazém padrão oficial não corresponde ao solicitado. Confirme o valor correto antes de ajustar.",
      accountingAccount:
        "A conta contábil oficial não corresponde à conta informada na solicitação. Confirme o valor correto antes de ajustar.",
      thirdPartyProduct:
        "A classificação de produto de terceiros não corresponde à solicitada. Confirme o valor correto.",
      customerReference:
        "A referência cadastrada não corresponde à referência solicitada. Confirme o valor correto antes de ajustar.",
    };
    return (
      byPath[path] ||
      "Há diferença entre o valor solicitado e o valor oficial. Confirme o valor correto e ajuste a ficha ou solicite a alteração manual do cadastro oficial, conforme autorização."
    );
  }
  return "Correspondência confirmada pela Engineering API.";
}

function supplierAttributeObservation(
  attribute: string,
  result: string,
): string {
  const label =
    PRC_SUPPLIER_LABELS[attribute] || attribute;
  if (result === "unverifiable") {
    return `Não foi possível confirmar ${label} na fonte oficial. A conclusão permanece bloqueada.`;
  }
  if (result === "mismatched") {
    return (
      `${label} solicitado difere do valor oficial neste vínculo. ` +
      "Confirme o valor correto e ajuste a ficha ou solicite a alteração manual do cadastro oficial, conforme autorização."
    );
  }
  return `${label} correspondente.`;
}

function supplierLinkObservation(reasonCode: string | null | undefined): string {
  switch (reasonCode) {
    case "missing_in_official":
      return "O vínculo de fornecedor solicitado não foi encontrado no cadastro oficial.";
    case "still_present_official":
      return "O vínculo ainda está presente no cadastro oficial após a remoção solicitada.";
    case "ambiguous_official":
      return "Há mais de um vínculo oficial com o mesmo código e loja — a comparação ficou ambígua.";
    case "official_links_incomplete":
      return "A leitura oficial dos vínculos SA5 está incompleta. A conclusão permanece bloqueada.";
    default:
      return "Há divergência neste vínculo de fornecedor. Confirme o valor correto antes de ajustar.";
  }
}

type SupplierDetailEntry = {
  key?: string;
  result?: string;
  reasonCode?: string;
  supplierCode?: string;
  store?: string;
  operation?: string;
  supplierKey?: { supplierCode?: string; store?: string };
  fields?: string[];
  attributes?: Array<{
    attribute: string;
    expected?: unknown;
    observed?: unknown;
    result?: string;
    reasonCode?: string | null;
  }>;
};

function parseLegacySupplierKey(key: string | undefined): {
  operation?: string;
  supplierCode?: string;
  store?: string;
} {
  if (!key) return {};
  // update:000089.01  |  000089/01
  const colon = key.indexOf(":");
  const body = colon >= 0 ? key.slice(colon + 1) : key;
  const operation = colon >= 0 ? key.slice(0, colon) : undefined;
  const sep = body.includes("/") ? "/" : ".";
  const [supplierCode, store] = body.split(sep);
  return { operation, supplierCode, store };
}

function expandSupplierDetail(
  entry: SupplierDetailEntry,
  index: number,
): DiagnosisItem[] {
  const parsed = parseLegacySupplierKey(entry.key);
  const supplierCode =
    entry.supplierCode ||
    entry.supplierKey?.supplierCode ||
    parsed.supplierCode ||
    "";
  const store =
    entry.store || entry.supplierKey?.store || parsed.store || "";
  const operation = entry.operation || parsed.operation;
  const linkResult = entry.result || "unverifiable";
  const reasonCode = entry.reasonCode || (
    ["missing_in_official", "still_present_official", "ambiguous_official", "official_links_incomplete"].includes(linkResult)
      ? linkResult
      : null
  );

  if (Array.isArray(entry.attributes) && entry.attributes.length) {
    return entry.attributes.map((attr) => {
      const result = attr.result || "unverifiable";
      const isProblem = PROBLEM_RESULTS.has(result);
      return {
        id: `sa5-${supplierCode}-${store}-${attr.attribute}-${index}`,
        kind: "supplier_attribute" as const,
        path: "suppliers",
        supplierCode,
        store,
        attribute: attr.attribute,
        operation,
        result,
        reasonCode: attr.reasonCode ?? reasonCode,
        expected: attr.expected,
        observed: attr.observed,
        isProblem,
        observation: supplierAttributeObservation(attr.attribute, result),
        label: `Fornecedor ${supplierCode} / Loja ${store} · ${PRC_SUPPLIER_LABELS[attr.attribute] || attr.attribute}`,
      };
    });
  }

  // Legado: result = "partNumber:mismatched,catalogNumber:matched"
  if (linkResult.includes(":")) {
    const tokens = linkResult.split(",").map((t) => t.trim()).filter(Boolean);
    const items: DiagnosisItem[] = [];
    for (const token of tokens) {
      const [attribute, attrResult] = token.split(":");
      if (!attribute || !attrResult) continue;
      const isProblem = PROBLEM_RESULTS.has(attrResult);
      items.push({
        id: `sa5-legacy-${supplierCode}-${store}-${attribute}-${index}`,
        kind: "supplier_attribute",
        path: "suppliers",
        supplierCode,
        store,
        attribute,
        operation,
        result: attrResult,
        reasonCode: attrResult === "mismatched" ? "mismatch" : attrResult,
        isProblem,
        observation: supplierAttributeObservation(attribute, attrResult),
        label: `Fornecedor ${supplierCode} / Loja ${store} · ${PRC_SUPPLIER_LABELS[attribute] || attribute}`,
      });
    }
    if (items.length) return items;
  }

  const isProblem =
    PROBLEM_RESULTS.has(linkResult) || linkResult === "mismatched";
  if (linkResult === "matched") {
    return [{
      id: `sa5-link-${supplierCode}-${store}-${index}`,
      kind: "supplier_link",
      path: "suppliers",
      supplierCode,
      store,
      operation,
      result: "matched",
      isProblem: false,
      observation: "Vínculo correspondente.",
      label: `Fornecedor ${supplierCode} / Loja ${store}`,
    }];
  }
  return [{
    id: `sa5-link-${supplierCode}-${store}-${index}`,
    kind: "supplier_link",
    path: "suppliers",
    supplierCode,
    store,
    operation,
    result: linkResult === "mismatched" ? "mismatched" : linkResult,
    reasonCode,
    isProblem,
    observation: supplierLinkObservation(reasonCode || linkResult),
    label: `Fornecedor ${supplierCode || "—"} / Loja ${store || "—"}`,
  }];
}

/** Constrói itens de diagnóstico a partir de field_results oficiais. */
export function buildDiagnosisItems(
  fieldResults: Record<string, PrcFieldResult> | null | undefined,
): DiagnosisItem[] {
  if (!fieldResults) return [];
  const items: DiagnosisItem[] = [];
  for (const [path, raw] of Object.entries(fieldResults)) {
    if (path === "suppliers") {
      const detail = Array.isArray(raw.detail) ? raw.detail : [];
      if (detail.length) {
        detail.forEach((entry, index) => {
          items.push(...expandSupplierDetail(entry as SupplierDetailEntry, index));
        });
        continue;
      }
      // Sem detalhe: contar o agregado uma única vez (não inventar filhos).
      const result = raw.result || "unverifiable";
      items.push({
        id: `field-${path}`,
        kind: "field",
        path,
        result,
        reasonCode: raw.reason,
        previous: raw.previous,
        expected: raw.expected,
        observed: raw.observed,
        isProblem: PROBLEM_RESULTS.has(result),
        observation:
          result === "matched"
            ? "Fornecedores correspondentes."
            : "Há divergência nos vínculos de fornecedores, sem detalhe granular disponível nesta evidência.",
        label: PRC_FIELD_LABELS.suppliers || "Fornecedores",
      });
      continue;
    }
    const result = raw.result || "unverifiable";
    items.push({
      id: `field-${path}`,
      kind: "field",
      path,
      result,
      reasonCode: raw.reason,
      previous: raw.previous,
      expected: raw.expected,
      observed: raw.observed,
      isProblem: PROBLEM_RESULTS.has(result),
      observation: fieldObservation(
        path,
        result,
        raw.reason,
        raw.expected,
        raw.observed,
      ),
      label: prcFieldLabel(path),
    });
  }
  return items;
}

export function summarizeDiagnosis(args: {
  fieldResults?: Record<string, PrcFieldResult> | null;
  verification?: PrcVerification | null;
  globalResult?: string | null;
  officialCode?: string | null;
}): DiagnosisSummary {
  const globalResult =
    args.globalResult ||
    args.verification?.result ||
    null;
  const isInfra = isInfraVerificationResult(globalResult);
  const items = isInfra ? [] : buildDiagnosisItems(args.fieldResults);
  const matched = items.filter((i) => i.result === "matched").length;
  const mismatched = items.filter((i) => i.result === "mismatched").length;
  const unverifiable = items.filter(
    (i) => i.isProblem && i.result !== "mismatched",
  ).length;
  const problemItems = items.filter((i) => i.isProblem);
  return {
    verificationId: args.verification?.id || null,
    officialCode:
      args.verification?.official_product_code || args.officialCode || null,
    checkedAt: args.verification?.checked_at || null,
    globalResult,
    isInfra,
    totalChecks: items.length,
    matched,
    problems: problemItems.length,
    mismatched,
    unverifiable,
    items,
    problemItems,
  };
}

/** Seleciona a evidência da tentativa ativa: preferir a última
 * verificação persistida; `lastError` só quando ainda não há tentativa
 * com field_results (ou fingerprint bate). */
export function pickActiveFieldResults(args: {
  verifications: PrcVerification[];
  lastError?: Record<string, PrcFieldResult> | null;
  status: string;
}): {
  fieldResults: Record<string, PrcFieldResult> | null;
  verification: PrcVerification | null;
  staleError: boolean;
} {
  const last = args.verifications.length
    ? args.verifications[args.verifications.length - 1]
    : null;
  if (args.status === "completed") {
    return {
      fieldResults: last?.field_results || null,
      verification: last,
      staleError: Boolean(args.lastError),
    };
  }
  if (last?.field_results && Object.keys(last.field_results).length) {
    return {
      fieldResults: last.field_results,
      verification: last,
      staleError: false,
    };
  }
  if (args.lastError && Object.keys(args.lastError).length) {
    return {
      fieldResults: args.lastError,
      verification: last,
      staleError: false,
    };
  }
  return { fieldResults: null, verification: last, staleError: false };
}

export function technicalTargetElementId(item: DiagnosisItem): string | null {
  if (item.kind === "field" && item.path && item.path !== "suppliers") {
    return `prc-field-${item.path}`;
  }
  if (
    (item.kind === "supplier_attribute" || item.kind === "supplier_link") &&
    item.supplierCode &&
    item.store
  ) {
    const attr = item.attribute || "partNumber";
    return `prc-supplier-${item.supplierCode}-${item.store}-${attr}`;
  }
  return null;
}

/** Identidade estável do alvo de encaminhamento (PRC-REF-021). */
export function diagnosisItemRoutingKey(item: DiagnosisItem): string {
  if (item.kind === "field") {
    return `FIELD:${item.path || item.id}`;
  }
  const code = item.supplierCode || "";
  const store = item.store || "";
  const attr = item.attribute || "link";
  return `SUPPLIER_LINK:${code}/${store}:${attr}`;
}
