/**
 * Helpers para consumir o contrato de coverage-audit / add-customer warning.
 */
import type {
  AddSellerCustomerResult,
  CoverageLinkWarning,
  SellerPortfolio,
  SellerPortfoliosCoverageAudit,
} from "../types/portfolio";
import { customerKey } from "../shared/format";

export function stripPortfolioCoverageFields(
  result: AddSellerCustomerResult,
): SellerPortfolio {
  const {
    warnings: _warnings,
    coverage_warning: _coverageWarning,
    ...portfolio
  } = result;
  return portfolio;
}

export function readCoverageLinkWarning(
  result: AddSellerCustomerResult,
): CoverageLinkWarning | null {
  if (result.coverage_warning) return result.coverage_warning;
  const first = result.warnings?.[0];
  return first ?? null;
}

export function overlappingPortfolioIdSet(
  audit: SellerPortfoliosCoverageAudit | null | undefined,
): Set<string> {
  const ids = new Set<string>();
  for (const item of audit?.portfolios_with_overlap ?? []) {
    if (item.id) ids.add(item.id);
  }
  return ids;
}

export function overlappingCustomerKeySetForPortfolio(
  audit: SellerPortfoliosCoverageAudit | null | undefined,
  portfolioId: string,
): Set<string> {
  const keys = new Set<string>();
  const pid = portfolioId.trim();
  if (!pid) return keys;
  for (const item of audit?.overlapping ?? []) {
    if (!item.portfolio_ids?.includes(pid)) continue;
    keys.add(customerKey(item.customer_code, item.customer_store));
  }
  return keys;
}

export function otherPortfolioNamesForCustomer(
  audit: SellerPortfoliosCoverageAudit | null | undefined,
  portfolioId: string,
  customerCode: string,
  customerStore: string,
): string[] {
  const pid = portfolioId.trim();
  const key = customerKey(customerCode, customerStore);
  for (const item of audit?.overlapping ?? []) {
    if (customerKey(item.customer_code, item.customer_store) !== key) continue;
    return (item.portfolios ?? [])
      .filter((ref) => ref.id !== pid)
      .map((ref) => ref.display_name.trim() || ref.id);
  }
  return [];
}
