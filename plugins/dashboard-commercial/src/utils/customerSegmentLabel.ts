import type { CommercialCustomerSegment } from "../types/commercial";

export function formatCustomerSegmentFilterLabel(
  segment: CommercialCustomerSegment | "" | undefined
): string | null {
  if (segment === "weg") return "WEG";
  if (segment === "new_business") return "Novos negócios";
  return null;
}

export function appendCustomerSegmentToLabel(
  label: string,
  segment: CommercialCustomerSegment | "" | undefined
): string {
  const segmentLabel = formatCustomerSegmentFilterLabel(segment);
  return segmentLabel ? `${label} · ${segmentLabel}` : label;
}

export function formatNewBusinessRolContextLine(
  data: {
    new_business_rol?: number | null;
    weg_rol?: number | null;
  } | null,
  segment: CommercialCustomerSegment | "" | undefined,
  formatCurrency: (value: number) => string
): string {
  if (segment === "weg") {
    return `${formatCurrency(data?.weg_rol ?? 0)} WEG`;
  }
  if (segment === "new_business") {
    return `${formatCurrency(data?.new_business_rol ?? 0)} novos negócios`;
  }
  return `${formatCurrency(data?.new_business_rol ?? 0)} não-WEG`;
}
