import { KAIZEN_STATUSES, SAVINGS_TYPES } from "../constants/kaizen";

export function savingsTypeLabel(value: string | null | undefined): string {
  if (!value) return "—";
  return SAVINGS_TYPES.find((item) => item.value === value)?.label ?? value;
}

export function statusLabel(value: string | null | undefined): string {
  if (!value) return "—";
  return KAIZEN_STATUSES.find((item) => item.value === value)?.label ?? value;
}
