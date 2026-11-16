import { formatBrl } from "../constants/labels";

export type MileageRateLookup = {
  date: string;
  status: "idle" | "loading" | "success" | "error";
  rate: number | null;
  error: string | null;
};

export const emptyMileageRateLookup: MileageRateLookup = {
  date: "",
  status: "idle",
  rate: null,
  error: null,
};

export function rateForDate(lookup: MileageRateLookup, selectedDate: string): number | null {
  if (
    !selectedDate ||
    lookup.date !== selectedDate ||
    lookup.status !== "success" ||
    lookup.rate === null ||
    !Number.isFinite(lookup.rate) ||
    lookup.rate <= 0
  ) {
    return null;
  }
  return lookup.rate;
}

export function mileageRateLabel(lookup: MileageRateLookup, selectedDate: string): string {
  if (!selectedDate) return "Informe a data da despesa";
  if (lookup.date !== selectedDate || lookup.status === "idle" || lookup.status === "loading") {
    return "Consultando tarifa…";
  }
  const rate = rateForDate(lookup, selectedDate);
  return rate === null ? "Tarifa indisponível" : `${formatBrl(rate)}/km`;
}
