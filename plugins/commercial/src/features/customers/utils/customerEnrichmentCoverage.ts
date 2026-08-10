import type { CustomerSummary } from "../types/customerSummary";

export function hasCustomerEnrichmentCoverage(
  customer: Pick<CustomerSummary, "coverageKnown" | "enrichmentAvailable">,
): boolean {
  return customer.coverageKnown === true || customer.enrichmentAvailable === true;
}
