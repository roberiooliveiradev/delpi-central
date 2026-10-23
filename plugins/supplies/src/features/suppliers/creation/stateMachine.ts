/** Regras puras do cadastro assistido — testáveis sem React (X4.UX-R1.S2). */

import type {
  SuggestionEntry,
  SuggestionEntryMap,
  SupplierCreationPreview,
} from "./types";

/** Dígitos do CNPJ (máscara removida). */
export function normalizeCnpjDigits(value: string): string {
  return (value ?? "").replace(/\D/g, "");
}

/**
 * Validação básica de frontend — 14 dígitos + verificadores.
 * A validação definitiva é do backend (S1).
 */
export function isCnpjFormatValid(value: string): boolean {
  const digits = normalizeCnpjDigits(value);
  if (digits.length !== 14) return false;
  if (digits === digits[0].repeat(14)) return false;
  const dv = (base: string, weights: readonly number[]) => {
    const sum = base
      .split("")
      .reduce((acc, d, i) => acc + Number(d) * weights[i], 0);
    const r = sum % 11;
    return r < 2 ? 0 : 11 - r;
  };
  const d1 = dv(digits.slice(0, 12), [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
  const d2 = dv(digits.slice(0, 13), [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
  return Number(digits[12]) === d1 && Number(digits[13]) === d2;
}

/** Snapshot das sugestões + campos indisponíveis da prévia. */
export function buildSuggestionEntries(
  preview: SupplierCreationPreview,
): SuggestionEntryMap {
  const map: SuggestionEntryMap = {};
  for (const s of preview.suggestions) {
    map[s.field_key] = { ...s, status: "SUGGESTED" };
  }
  for (const key of preview.unavailable_fields) {
    map[key] ??= {
      field_key: key,
      suggested_value: null,
      source: null,
      applicable: false,
      status: "UNAVAILABLE",
    };
  }
  return map;
}

/**
 * Reconcilia edição do draft com o estado das sugestões.
 * Valor igual ao sugerido → CONFIRMED; diferente e preenchido →
 * MANUALLY_CHANGED; esvaziado → volta a SUGGESTED (sugestão re-disponível).
 */
export function applyDraftPatchToEntries(
  entries: SuggestionEntryMap,
  patch: Record<string, string>,
): SuggestionEntryMap {
  let changed = false;
  const next = { ...entries };
  for (const [key, value] of Object.entries(patch)) {
    const entry = entries[key];
    if (!entry || entry.status === "UNAVAILABLE") continue;
    const current = (value ?? "").trim();
    const suggested = (entry.suggested_value ?? "").trim();
    const status =
      !current || !suggested
        ? "SUGGESTED"
        : current === suggested
          ? "CONFIRMED"
          : "MANUALLY_CHANGED";
    if (status !== entry.status) {
      next[key] = { ...entry, status };
      changed = true;
    }
  }
  return changed ? next : entries;
}

export type IdentityCheck = {
  /** Campos de identidade que mudariam (somente se já preenchidos com valor divergente). */
  changedKeys: readonly ("tax_id" | "person_type")[];
  /** Quantidade de demais campos preenchidos — risco de mistura de empresas. */
  filledFieldCount: number;
};

/**
 * Decide se incorporar a identidade consultada exige confirmação.
 * Campo vazio nunca é "identidade existente" — pode ser preenchido livremente.
 * Valor divergente em `tax_id` ou `person_type` exige confirmação explícita.
 */
export function identityChangeCheck(
  draft: Record<string, string>,
  consultedTaxId: string,
  consultedPersonType: string,
): IdentityCheck {
  const changedKeys: ("tax_id" | "person_type")[] = [];
  const currentTax = normalizeCnpjDigits(draft.tax_id ?? "");
  if (currentTax && currentTax !== consultedTaxId) changedKeys.push("tax_id");
  const currentPerson = (draft.person_type ?? "").trim();
  if (currentPerson && currentPerson !== consultedPersonType) {
    changedKeys.push("person_type");
  }
  const filledFieldCount = Object.entries(draft).filter(
    ([key, value]) =>
      key !== "tax_id" && key !== "person_type" && (value ?? "").trim() !== "",
  ).length;
  return { changedKeys, filledFieldCount };
}

/**
 * Coerência de identidade: as sugestões do preview só podem ser aplicadas
 * quando o documento do formulário é o mesmo da consulta bem-sucedida.
 */
export function isIdentityCoherent(
  draft: Record<string, string>,
  consultedTaxId: string | null,
): boolean {
  if (!consultedTaxId) return false;
  return normalizeCnpjDigits(draft.tax_id ?? "") === consultedTaxId;
}

/** true quando a digitação mudou os 14 dígitos — máscara não invalida. */
export function searchTaxIdChanged(
  inputValue: string,
  activeTaxId: string | null,
): boolean {
  if (!activeTaxId) return false;
  return normalizeCnpjDigits(inputValue) !== activeTaxId;
}

export type ApplyDecision = "apply" | "confirm_overwrite" | "blocked";

/**
 * Campo vazio → aplica; já preenchido igual → aplica (idempotente);
 * preenchido diferente → exige confirmação explícita; não elegível → bloqueado.
 */
export function suggestionApplyDecision(
  entry: SuggestionEntry | undefined,
  currentValue: string,
): ApplyDecision {
  if (!entry || entry.status === "UNAVAILABLE" || !entry.suggested_value) {
    return "blocked";
  }
  if (!entry.applicable) return "blocked";
  const current = (currentValue ?? "").trim();
  if (!current || current === entry.suggested_value.trim()) return "apply";
  return "confirm_overwrite";
}

/** Sugestões aplicáveis ainda não confirmadas — para ação «aplicar todas». */
export function pendingApplicableEntries(
  entries: SuggestionEntryMap,
  draft: Record<string, string>,
): SuggestionEntry[] {
  return Object.values(entries).filter(
    (e) =>
      e.status === "SUGGESTED" &&
      suggestionApplyDecision(e, draft[e.field_key] ?? "") === "apply",
  );
}


