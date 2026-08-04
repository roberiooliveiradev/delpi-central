import type { CustomerBillingPeriodPreset } from "../types/customerBilling";

function toIso(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function periodRangeFromPreset(
  preset: Exclude<CustomerBillingPeriodPreset, "custom">,
  today: Date = new Date(),
): { startDate: string; endDate: string } {
  const days = Number(preset);
  const end = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const start = new Date(end);
  start.setDate(start.getDate() - (days - 1));
  return { startDate: toIso(start), endDate: toIso(end) };
}

export function isValidIsoDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00`);
  return !Number.isNaN(date.getTime()) && toIso(date) === value;
}

export function validateBillingPeriod(
  startDate: string,
  endDate: string,
): string | null {
  if (!isValidIsoDate(startDate) || !isValidIsoDate(endDate)) {
    return "Informe datas válidas no formato AAAA-MM-DD.";
  }
  if (startDate > endDate) {
    return "A data inicial não pode ser posterior à data final.";
  }
  return null;
}

export function situationLabel(situation: string): string {
  if (situation === "return") return "Devolução";
  if (situation === "emitted") return "Emitida";
  return situation || "—";
}
