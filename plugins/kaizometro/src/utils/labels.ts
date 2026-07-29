import { BRANCHES, KAIZEN_STATUSES, SAVINGS_TYPES } from "../constants/kaizen";

/** Rótulo da unidade (ex.: "01" → "Santa Catarina"). Mantém o código como fallback. */
export function unitLabel(code: string | null | undefined): string {
  if (!code) return "—";
  return BRANCHES.find((item) => item.code === code)?.label ?? code;
}

export function savingsTypeLabel(value: string | null | undefined): string {
  if (!value) return "—";
  return SAVINGS_TYPES.find((item) => item.value === value)?.label ?? value;
}

export function statusLabel(value: string | null | undefined): string {
  if (!value) return "—";
  return KAIZEN_STATUSES.find((item) => item.value === value)?.label ?? value;
}
